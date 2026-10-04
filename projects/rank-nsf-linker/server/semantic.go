package main

import (
	"bytes"
	"crypto/sha1"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"math"
	"net/http"
	"os"
	"regexp"
	"sort"
	"strings"
	"sync"
	"time"

	colly "github.com/gocolly/colly/v2"
	"github.com/lib/pq"
)

// Semantic goal matching: every NSF grant and recent paper of an explorer professor is embedded
// (all-MiniLM-L6-v2, via the embedder service) and stored in Qdrant with the professor's areas
// and university, so a student's goal can be matched by meaning ("LLMs explaining their
// answers" finds "interpretability of language models"). Without the embedder or Qdrant the
// explorer falls back to keyword matching.
const (
	workCollection   = "explorer_work"
	embeddingDim     = 384
	embedBatchSize   = 128  // the embedder's MAX_BATCH_SIZE
	semanticMinScore = 0.35 // cosine similarity below which a grant/paper is not counted as a match
	recencyHalfLife  = 5.5  // years; a match's ranking weight halves this often
)

var (
	semanticClient = &http.Client{Timeout: 60 * time.Second}
	// NSF titles for event support: "Conference: …", "Workshop on …", "Travel: …", "Student Travel Support …".
	eventGrant = regexp.MustCompile(`(?i)^(conference|workshop|travel|student travel|planning)\b|\bworkshop\b|\bsymposium\b`)
)

func embedderURL() string {
	if u := os.Getenv("EMBEDDER_SERVICE_URL"); u != "" {
		return strings.TrimRight(u, "/")
	}
	return "http://embedder:8000"
}

func qdrantURL() string {
	if u := os.Getenv("QDRANT_REST_URL"); u != "" {
		return strings.TrimRight(u, "/")
	}
	return "http://qdrant-local:6333"
}

func postJSON(method, url string, body any, out any) error {
	var buf bytes.Buffer
	if body != nil {
		if err := json.NewEncoder(&buf).Encode(body); err != nil {
			return err
		}
	}
	req, err := http.NewRequest(method, url, &buf)
	if err != nil {
		return err
	}
	req.Header.Set("Content-Type", "application/json")
	resp, err := semanticClient.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	if resp.StatusCode >= 300 {
		var msg bytes.Buffer
		_, _ = msg.ReadFrom(resp.Body)
		return fmt.Errorf("%s %s: HTTP %d: %.300s", method, url, resp.StatusCode, msg.String())
	}
	if out == nil {
		return nil
	}
	return json.NewDecoder(resp.Body).Decode(out)
}

func embedTexts(texts []string) ([][]float32, error) {
	var res struct {
		Embeddings [][]float32 `json:"embeddings"`
	}
	if err := postJSON(http.MethodPost, embedderURL()+"/embed/batch", map[string]any{"texts": texts}, &res); err != nil {
		return nil, err
	}
	if len(res.Embeddings) != len(texts) {
		return nil, fmt.Errorf("embedder returned %d vectors for %d texts", len(res.Embeddings), len(texts))
	}
	return res.Embeddings, nil
}

var semanticState struct {
	sync.Mutex
	checked time.Time
	ok      bool
}

// semanticAvailable reports whether the embedder and the Qdrant collection are up; the answer is
// cached for 30 seconds so requests don't pay for health checks.
func semanticAvailable() bool {
	semanticState.Lock()
	defer semanticState.Unlock()
	if time.Since(semanticState.checked) < 30*time.Second {
		return semanticState.ok
	}
	semanticState.checked = time.Now()
	semanticState.ok = checkSemantic()
	return semanticState.ok
}

func checkSemantic() bool {
	c := &http.Client{Timeout: 2 * time.Second}
	for _, u := range []string{embedderURL() + "/health", qdrantURL() + "/collections/" + workCollection} {
		resp, err := c.Get(u)
		if err != nil {
			return false
		}
		resp.Body.Close()
		if resp.StatusCode != http.StatusOK {
			return false
		}
	}
	return true
}

type workPayload struct {
	Name         string   `json:"name"`
	Kind         string   `json:"kind"`
	Ref          string   `json:"ref"`
	Title        string   `json:"title"`
	Year         *int     `json:"year"`
	URL          *string  `json:"url"`
	Areas        []string `json:"areas"`
	UniversityID string   `json:"university_id"`
}

func (p workPayload) hash() string {
	b, _ := json.Marshal(p)
	sum := sha1.Sum(b)
	return hex.EncodeToString(sum[:])
}

// embedExplorerWork brings the Qdrant collection in line with explorer_work_docs: embeds new
// grants/papers, refreshes payloads whose professor areas or university changed, and deletes
// points for work that is gone. explorer_embedded remembers what Qdrant holds.
func embedExplorerWork(mainCtx *colly.Context) error {
	probe := &http.Client{Timeout: 3 * time.Second}
	for _, u := range []string{embedderURL() + "/health", qdrantURL() + "/collections"} {
		resp, err := probe.Get(u)
		if err != nil {
			logger.Warnf(mainCtx, "⚠️ %s unreachable (%v); skipping semantic index, keyword matching stays on", u, err)
			return nil
		}
		resp.Body.Close()
	}

	db, err := GetDB()
	if err != nil {
		return fmt.Errorf("cannot get DB: %w", err)
	}

	// Collection and payload indexes (idempotent).
	var exists struct {
		Status string `json:"status"`
	}
	if err := postJSON(http.MethodGet, qdrantURL()+"/collections/"+workCollection, nil, &exists); err != nil {
		if err := postJSON(http.MethodPut, qdrantURL()+"/collections/"+workCollection,
			map[string]any{"vectors": map[string]any{"size": embeddingDim, "distance": "Cosine"}}, nil); err != nil {
			return fmt.Errorf("failed to create Qdrant collection: %w", err)
		}
		if _, err := db.Exec(`TRUNCATE explorer_embedded`); err != nil {
			return fmt.Errorf("failed to reset explorer_embedded: %w", err)
		}
	}
	for _, field := range []string{"areas", "university_id", "name", "kind"} {
		_ = postJSON(http.MethodPut, qdrantURL()+"/collections/"+workCollection+"/index",
			map[string]any{"field_name": field, "field_schema": "keyword"}, nil)
	}

	type doc struct {
		id      string
		text    string
		payload workPayload
	}
	rows, err := db.Query(`
		SELECT md5(d.name || '|' || d.kind || '|' || d.ref)::uuid::text,
		       d.name, d.kind, d.ref, COALESCE(d.title, ''), d.year, d.url, f.areas, COALESCE(u.id, ''),
		       -- '|| ''''' detoasts first: on Postgres 18.2 left() on a TOASTed value can split a UTF-8 character
		       COALESCE(d.title, '') || CASE WHEN d.kind = 'award' THEN '. ' || left(COALESCE(a.abstract, '') || '', 700) ELSE '' END
		FROM explorer_work_docs d
		JOIN explorer_faculty f ON f.name = d.name
		LEFT JOIN explorer_universities u ON u.name = f.university
		LEFT JOIN award a ON d.kind = 'award' AND a.id = d.ref`)
	if err != nil {
		return fmt.Errorf("failed to read work docs: %w", err)
	}
	docs := map[string]doc{}
	for rows.Next() {
		var d doc
		if err := rows.Scan(&d.id, &d.payload.Name, &d.payload.Kind, &d.payload.Ref, &d.payload.Title, &d.payload.Year,
			&d.payload.URL, pq.Array(&d.payload.Areas), &d.payload.UniversityID, &d.text); err != nil {
			rows.Close()
			return err
		}
		docs[d.id] = d
	}
	rows.Close()
	if err := rows.Err(); err != nil {
		return fmt.Errorf("failed to read work docs: %w", err)
	}

	held := map[string]string{} // id -> payload hash already in Qdrant
	rows, err = db.Query(`SELECT id::text, payload_hash FROM explorer_embedded`)
	if err != nil {
		return fmt.Errorf("failed to read explorer_embedded: %w", err)
	}
	for rows.Next() {
		var id, h string
		if err := rows.Scan(&id, &h); err != nil {
			rows.Close()
			return err
		}
		held[id] = h
	}
	rows.Close()
	if err := rows.Err(); err != nil {
		return fmt.Errorf("failed to read explorer_embedded: %w", err)
	}

	var toEmbed, toRepayload []doc
	for id, d := range docs {
		h, ok := held[id]
		switch {
		case !ok:
			toEmbed = append(toEmbed, d)
		case h != d.payload.hash():
			toRepayload = append(toRepayload, d)
		}
	}
	var toDelete []string
	for id := range held {
		if _, ok := docs[id]; !ok {
			toDelete = append(toDelete, id)
		}
	}
	logger.Infof(mainCtx, "🧠 Semantic index: %d to embed, %d payloads to refresh, %d to delete (%d held)",
		len(toEmbed), len(toRepayload), len(toDelete), len(held))

	record := func(ids []string, hashes []string) error {
		_, err := db.Exec(`
			INSERT INTO explorer_embedded (id, payload_hash)
			SELECT unnest($1::uuid[]), unnest($2::text[])
			ON CONFLICT (id) DO UPDATE SET payload_hash = EXCLUDED.payload_hash`, pq.Array(ids), pq.Array(hashes))
		return err
	}

	start := time.Now()
	for i := 0; i < len(toEmbed); i += embedBatchSize {
		batch := toEmbed[i:min(i+embedBatchSize, len(toEmbed))]
		texts := make([]string, len(batch))
		for j, d := range batch {
			texts[j] = d.text
		}
		vectors, err := embedTexts(texts)
		if err != nil {
			return fmt.Errorf("failed to embed batch: %w", err)
		}
		points := make([]map[string]any, len(batch))
		ids := make([]string, len(batch))
		hashes := make([]string, len(batch))
		for j, d := range batch {
			points[j] = map[string]any{"id": d.id, "vector": vectors[j], "payload": d.payload}
			ids[j], hashes[j] = d.id, d.payload.hash()
		}
		if err := postJSON(http.MethodPut, qdrantURL()+"/collections/"+workCollection+"/points?wait=true",
			map[string]any{"points": points}, nil); err != nil {
			return fmt.Errorf("failed to upsert points: %w", err)
		}
		if err := record(ids, hashes); err != nil {
			return fmt.Errorf("failed to record embedded points: %w", err)
		}
		if done := i + len(batch); done%(embedBatchSize*40) < embedBatchSize || done == len(toEmbed) {
			logger.Infof(mainCtx, "🧠 Embedded %d/%d (%s)", done, len(toEmbed), time.Since(start).Round(time.Second))
		}
	}

	for _, d := range toRepayload {
		if err := postJSON(http.MethodPost, qdrantURL()+"/collections/"+workCollection+"/points/payload?wait=true",
			map[string]any{"payload": d.payload, "points": []string{d.id}}, nil); err != nil {
			return fmt.Errorf("failed to refresh payload: %w", err)
		}
		if err := record([]string{d.id}, []string{d.payload.hash()}); err != nil {
			return err
		}
	}

	for i := 0; i < len(toDelete); i += 1000 {
		batch := toDelete[i:min(i+1000, len(toDelete))]
		if err := postJSON(http.MethodPost, qdrantURL()+"/collections/"+workCollection+"/points/delete?wait=true",
			map[string]any{"points": batch}, nil); err != nil {
			return fmt.Errorf("failed to delete points: %w", err)
		}
		if _, err := db.Exec(`DELETE FROM explorer_embedded WHERE id = ANY($1::uuid[])`, pq.Array(batch)); err != nil {
			return err
		}
	}

	logger.Infof(mainCtx, "🧠 Semantic index ready: %d grants and papers", len(docs))
	return nil
}

// semanticMatch is one professor's best match for a goal.
type semanticMatch struct {
	Name       string
	University string // university id
	Similarity float64
	Rank       float64 // similarity weighted by recency
	Work       workPayload
}

type workHit struct {
	Score   float64     `json:"score"`
	Payload workPayload `json:"payload"`
}

// searchWork embeds the goal and returns grants/papers whose meaning is close to it, narrowed
// to areas, a university and a kind ("award" or "paper") when given.
func searchWork(goal string, areas []string, universityID, kind string, depth int) ([]workHit, error) {
	vectors, err := embedTexts([]string{goal})
	if err != nil {
		return nil, err
	}

	var must []map[string]any
	if len(areas) > 0 {
		must = append(must, map[string]any{"key": "areas", "match": map[string]any{"any": areas}})
	}
	if universityID != "" {
		must = append(must, map[string]any{"key": "university_id", "match": map[string]any{"value": universityID}})
	}
	if kind != "" {
		must = append(must, map[string]any{"key": "kind", "match": map[string]any{"value": kind}})
	}
	req := map[string]any{
		"vector":          vectors[0],
		"limit":           depth,
		"with_payload":    true,
		"score_threshold": semanticMinScore,
	}
	if len(must) > 0 {
		req["filter"] = map[string]any{"must": must}
	}
	var res struct {
		Result []workHit `json:"result"`
	}
	if err := postJSON(http.MethodPost, qdrantURL()+"/collections/"+workCollection+"/points/search", req, &res); err != nil {
		return nil, err
	}
	return res.Result, nil
}

// recencyWeight halves a match's weight every recencyHalfLife years and discounts event grants.
func recencyWeight(p workPayload) float64 {
	age := 15.0
	if p.Year != nil {
		age = math.Max(0, float64(time.Now().Year()-*p.Year))
	}
	w := math.Pow(0.5, age/recencyHalfLife)
	if eventGrant.MatchString(p.Title) {
		w *= 0.6 // a grant to host a meeting is not a research direction
	}
	return w
}

// semanticFacultyMatches returns professors whose grants/papers match the goal, best first.
// areas and universityID narrow the search; depth bounds how many grants/papers are considered.
func semanticFacultyMatches(goal string, areas []string, universityID string, depth int) ([]semanticMatch, error) {
	hits, err := searchWork(goal, areas, universityID, "", depth)
	if err != nil {
		return nil, err
	}
	best := map[string]semanticMatch{}
	for _, hit := range hits {
		rank := hit.Score * recencyWeight(hit.Payload)
		if cur, ok := best[hit.Payload.Name]; !ok || rank > cur.Rank {
			best[hit.Payload.Name] = semanticMatch{
				Name: hit.Payload.Name, University: hit.Payload.UniversityID,
				Similarity: hit.Score, Rank: rank, Work: hit.Payload,
			}
		}
	}
	matches := make([]semanticMatch, 0, len(best))
	for _, m := range best {
		matches = append(matches, m)
	}
	sort.Slice(matches, func(i, j int) bool { return matches[i].Rank > matches[j].Rank })
	return matches, nil
}

// grantMatch is one NSF award close to a goal, with the explorer professors on it.
type grantMatch struct {
	AwardID    string
	Similarity float64
	People     []string
}

// semanticGrantMatches returns NSF awards whose title/abstract match the goal, most similar first.
func semanticGrantMatches(goal string, areas []string, depth int) ([]grantMatch, error) {
	hits, err := searchWork(goal, areas, "", "award", depth)
	if err != nil {
		return nil, err
	}
	byAward := map[string]*grantMatch{}
	var order []string
	for _, h := range hits {
		g, ok := byAward[h.Payload.Ref]
		if !ok {
			g = &grantMatch{AwardID: h.Payload.Ref, Similarity: h.Score}
			byAward[h.Payload.Ref] = g
			order = append(order, h.Payload.Ref)
		}
		g.People = append(g.People, h.Payload.Name)
	}
	matches := make([]grantMatch, len(order))
	for i, id := range order {
		matches[i] = *byAward[id]
	}
	return matches, nil
}
