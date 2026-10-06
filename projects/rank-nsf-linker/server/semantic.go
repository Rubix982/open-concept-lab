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

// postJSON sends a JSON request to the embedder or Qdrant. A dropped connection or a 5xx is tried
// again (three attempts): every call here is idempotent (searches, upserts by id, payload writes,
// deletes), and one "use of closed network connection" used to fail a twelve-hour embedding run.
func postJSON(method, url string, body any, out any) error {
	var payload []byte
	if body != nil {
		var buf bytes.Buffer
		if err := json.NewEncoder(&buf).Encode(body); err != nil {
			return err
		}
		payload = buf.Bytes()
	}
	var resp *http.Response
	for attempt := 0; ; attempt++ {
		req, err := http.NewRequest(method, url, bytes.NewReader(payload))
		if err != nil {
			return err
		}
		req.Header.Set("Content-Type", "application/json")
		resp, err = semanticClient.Do(req)
		if err == nil && resp.StatusCode < 500 {
			break
		}
		if attempt == 2 {
			if err != nil {
				return err
			}
			break
		}
		if err == nil {
			resp.Body.Close()
		}
		time.Sleep(time.Duration(2+3*attempt) * time.Second)
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

// A search sends three requests at once (universities, faculty, grants) that embed the same query;
// each took seconds while the embedder was busy. Queries are embedded once: concurrent callers wait
// for the first, later ones reuse the vector (the last 256 queries are kept).
var queryVectors struct {
	sync.Mutex
	m map[string]*queryVector
}

type queryVector struct {
	done chan struct{}
	vec  []float32
	err  error
}

func embedQuery(text string) ([]float32, error) {
	queryVectors.Lock()
	if queryVectors.m == nil || len(queryVectors.m) > 256 {
		queryVectors.m = map[string]*queryVector{}
	}
	q, ok := queryVectors.m[text]
	if !ok {
		q = &queryVector{done: make(chan struct{})}
		queryVectors.m[text] = q
	}
	queryVectors.Unlock()
	if !ok {
		vectors, err := embedTexts([]string{text})
		if err == nil {
			q.vec = vectors[0]
		}
		q.err = err
		close(q.done)
		if err != nil { // don't keep a failure
			queryVectors.Lock()
			delete(queryVectors.m, text)
			queryVectors.Unlock()
		}
	}
	<-q.done
	return q.vec, q.err
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

// docHash identifies the fields that belong to the work itself, not to its professor.
func (p workPayload) docHash() string {
	b, _ := json.Marshal([]any{p.Name, p.Kind, p.Ref, p.Title, p.Year, p.URL})
	sum := sha1.Sum(b)
	return hex.EncodeToString(sum[:])
}

// hash identifies a payload's content; area order doesn't count (Qdrant filters areas as a set).
func (p workPayload) hash() string {
	p.Areas = append([]string(nil), p.Areas...)
	sort.Strings(p.Areas)
	b, _ := json.Marshal(p)
	sum := sha1.Sum(b)
	return hex.EncodeToString(sum[:])
}

// qdrantPointIDs lists every point id in the work collection, in small pages: Qdrant 1.3 runs out of
// memory on large scrolls.
func qdrantPointIDs() (map[string]bool, error) {
	ids := map[string]bool{}
	var offset any
	for {
		var page struct {
			Result struct {
				Points []struct {
					ID string `json:"id"`
				} `json:"points"`
				NextPageOffset any `json:"next_page_offset"`
			} `json:"result"`
		}
		body := map[string]any{"limit": 2000, "with_payload": false, "with_vector": false}
		if offset != nil {
			body["offset"] = offset
		}
		if err := postJSON(http.MethodPost, qdrantURL()+"/collections/"+workCollection+"/points/scroll", body, &page); err != nil {
			return nil, fmt.Errorf("failed to list Qdrant points: %w", err)
		}
		for _, p := range page.Result.Points {
			ids[p.ID] = true
		}
		if page.Result.NextPageOffset == nil {
			return ids, nil
		}
		offset = page.Result.NextPageOffset
	}
}

// qdrantPayloads reads the payloads of the given points, 500 at a time.
func qdrantPayloads(ids []string) (map[string]workPayload, error) {
	out := map[string]workPayload{}
	for i := 0; i < len(ids); i += 500 {
		var res struct {
			Result []struct {
				ID      string      `json:"id"`
				Payload workPayload `json:"payload"`
			} `json:"result"`
		}
		if err := postJSON(http.MethodPost, qdrantURL()+"/collections/"+workCollection+"/points",
			map[string]any{"ids": ids[i:min(i+500, len(ids))], "with_payload": true, "with_vector": false}, &res); err != nil {
			return nil, fmt.Errorf("failed to read Qdrant payloads: %w", err)
		}
		for _, p := range res.Result {
			out[p.ID] = p.Payload
		}
	}
	return out, nil
}

func textHash(text string) string {
	sum := sha1.Sum([]byte(text))
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
			map[string]any{"vectors": map[string]any{"size": embeddingDim, "distance": "Cosine"},
				// int8 copies kept in RAM: the first search on a cold, memory-mapped index took seconds
				"quantization_config": map[string]any{"scalar": map[string]any{"type": "int8", "quantile": 0.99, "always_ram": true}}},
			nil); err != nil {
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
		id       string
		text     string
		baseText string // the title-only text vectors were embedded from before text_hash existed
		payload  workPayload
	}
	type heldPoint struct{ payloadHash, textHash, docHash string } // "" = recorded before that column existed
	held := map[string]heldPoint{}
	rows, err := db.Query(`SELECT id::text, payload_hash, COALESCE(text_hash, ''), COALESCE(doc_hash, '') FROM explorer_embedded`)
	if err != nil {
		return fmt.Errorf("failed to read explorer_embedded: %w", err)
	}
	for rows.Next() {
		var id string
		var h heldPoint
		if err := rows.Scan(&id, &h.payloadHash, &h.textHash, &h.docHash); err != nil {
			rows.Close()
			return err
		}
		held[id] = h
	}
	rows.Close()
	if err := rows.Err(); err != nil {
		return fmt.Errorf("failed to read explorer_embedded: %w", err)
	}

	// explorer_embedded can claim points Qdrant lost (a crash before its write-ahead log was flushed):
	// forget those so they are embedded again.
	inQdrant, err := qdrantPointIDs()
	if err != nil {
		return err
	}
	var lost []string
	for id := range held {
		if !inQdrant[id] {
			lost = append(lost, id)
			delete(held, id)
		}
	}
	if len(lost) > 0 {
		if _, err := db.Exec(`DELETE FROM explorer_embedded WHERE id = ANY($1::uuid[])`, pq.Array(lost)); err != nil {
			return err
		}
		logger.Warnf(mainCtx, "⚠️ %d points recorded as embedded were missing from Qdrant; re-embedding them", len(lost))
	}
	inQdrant = nil

	rows, err = db.Query(`
		SELECT md5(d.name || '|' || d.kind || '|' || d.ref)::uuid::text,
		       d.name, d.kind, d.ref, COALESCE(d.title, ''), d.year, d.url, f.areas, COALESCE(u.id, ''),
		       -- '|| ''''' detoasts first: on Postgres 18.2 left() on a TOASTed value can split a UTF-8 character
		       COALESCE(d.title, '') || CASE WHEN d.kind = 'award'
		         THEN '. ' || left(COALESCE(a.abstract, fg.abstract, '') || '', 700) ELSE '' END,
		       -- papers: the OpenAlex abstract, when the DOI matched one
		       COALESCE(d.title, '') || CASE
		         WHEN d.kind = 'award' THEN '. ' || left(COALESCE(a.abstract, fg.abstract, '') || '', 700)
		         WHEN ow.abstract IS NOT NULL THEN '. ' || left(ow.abstract || '', 700)
		         ELSE '' END
		FROM explorer_work_docs d
		JOIN explorer_faculty f ON f.name = d.name
		LEFT JOIN explorer_universities u ON u.name = f.university
		LEFT JOIN award a ON d.kind = 'award' AND a.id = d.ref
		LEFT JOIN funder_grants fg ON d.kind = 'award' AND d.ref = fg.funder || ':' || fg.grant_id
		LEFT JOIN openalex_works ow ON d.kind = 'paper' AND ow.doi = lower(substring(d.url from 'doi\.org/(.+)$'))`)
	if err != nil {
		return fmt.Errorf("failed to read work docs: %w", err)
	}
	// Decide per row while reading, keeping only the docs that need work: holding every doc's text
	// (and its title-only base text) at once ran the container out of memory at ~830k docs.
	seen := make(map[string]struct{}, len(held))
	pending := map[string]workPayload{} // payloads to compare with Qdrant before rewriting
	var toEmbed, toRepayload []doc
	for rows.Next() {
		var d doc
		if err := rows.Scan(&d.id, &d.payload.Name, &d.payload.Kind, &d.payload.Ref, &d.payload.Title, &d.payload.Year,
			&d.payload.URL, pq.Array(&d.payload.Areas), &d.payload.UniversityID, &d.baseText, &d.text); err != nil {
			rows.Close()
			return err
		}
		seen[d.id] = struct{}{}
		h, ok := held[d.id]
		textChanged := ok && ((h.textHash == "" && d.text != d.baseText) ||
			(h.textHash != "" && h.textHash != textHash(d.text)))
		d.baseText = ""
		switch {
		case !ok || textChanged:
			toEmbed = append(toEmbed, d)
		case h.payloadHash != d.payload.hash():
			d.text = ""
			toRepayload = append(toRepayload, d)
			pending[d.id] = d.payload
		}
	}
	rows.Close()
	if err := rows.Err(); err != nil {
		return fmt.Errorf("failed to read work docs: %w", err)
	}

	var toDelete []string
	for id := range held {
		if _, ok := seen[id]; !ok {
			toDelete = append(toDelete, id)
		}
	}

	// A stale hash doesn't always mean a stale payload (area order used to count): compare with what
	// Qdrant holds and only rewrite real changes. Rewriting hundreds of thousands of payloads makes
	// Qdrant 1.3 rebuild its index and run out of memory.
	candidates := make([]string, len(toRepayload))
	for i, d := range toRepayload {
		candidates[i] = d.id
	}
	stored, err := qdrantPayloads(candidates)
	if err != nil {
		return err
	}
	var current []string
	changed := toRepayload[:0]
	for _, d := range toRepayload {
		if p, ok := stored[d.id]; ok && d.payload.hash() == p.hash() {
			current = append(current, d.id)
			continue
		}
		changed = append(changed, d)
	}
	toRepayload = changed
	if len(current) > 0 {
		hashes := make([]string, len(current))
		docHashes := make([]string, len(current))
		for i, id := range current {
			hashes[i], docHashes[i] = pending[id].hash(), pending[id].docHash()
		}
		if _, err := db.Exec(`
			UPDATE explorer_embedded e SET payload_hash = v.h, doc_hash = v.dh
			FROM (SELECT unnest($1::uuid[]) id, unnest($2::text[]) h, unnest($3::text[]) dh) v
			WHERE e.id = v.id`, pq.Array(current), pq.Array(hashes), pq.Array(docHashes)); err != nil {
			return fmt.Errorf("failed to record current payloads: %w", err)
		}
	}

	logger.Infof(mainCtx, "🧠 Semantic index: %d to embed, %d payloads to refresh, %d to delete (%d held)",
		len(toEmbed), len(toRepayload), len(toDelete), len(held))

	// record remembers what Qdrant holds; texts is nil for a payload-only refresh (text unchanged).
	record := func(ids, hashes, docHashes, texts []string) error {
		if texts == nil {
			_, err := db.Exec(`
				INSERT INTO explorer_embedded (id, payload_hash, doc_hash)
				SELECT unnest($1::uuid[]), unnest($2::text[]), unnest($3::text[])
				ON CONFLICT (id) DO UPDATE SET payload_hash = EXCLUDED.payload_hash, doc_hash = EXCLUDED.doc_hash`,
				pq.Array(ids), pq.Array(hashes), pq.Array(docHashes))
			return err
		}
		_, err := db.Exec(`
			INSERT INTO explorer_embedded (id, payload_hash, doc_hash, text_hash)
			SELECT unnest($1::uuid[]), unnest($2::text[]), unnest($3::text[]), unnest($4::text[])
			ON CONFLICT (id) DO UPDATE SET payload_hash = EXCLUDED.payload_hash, doc_hash = EXCLUDED.doc_hash,
			  text_hash = EXCLUDED.text_hash`,
			pq.Array(ids), pq.Array(hashes), pq.Array(docHashes), pq.Array(texts))
		return err
	}

	start, lastLog := time.Now(), time.Now()
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
		textHashes := make([]string, len(batch))
		docHashes := make([]string, len(batch))
		for j, d := range batch {
			points[j] = map[string]any{"id": d.id, "vector": vectors[j], "payload": d.payload}
			ids[j], hashes[j], textHashes[j], docHashes[j] = d.id, d.payload.hash(), textHash(d.text), d.payload.docHash()
		}
		if err := postJSON(http.MethodPut, qdrantURL()+"/collections/"+workCollection+"/points?wait=true",
			map[string]any{"points": points}, nil); err != nil {
			return fmt.Errorf("failed to upsert points: %w", err)
		}
		if err := record(ids, hashes, docHashes, textHashes); err != nil {
			return fmt.Errorf("failed to record embedded points: %w", err)
		}
		// Progress about once a minute (and at the end), whatever the batch size.
		if done := i + len(batch); time.Since(lastLog) > time.Minute || done == len(toEmbed) {
			lastLog = time.Now()
			logger.Infof(mainCtx, "🧠 Embedded %d/%d (%s)", done, len(toEmbed), time.Since(start).Round(time.Second))
		}

	}

	// A payload changes when its professor's areas or university change, and those are shared by all
	// of that professor's work: refresh them with one set_payload per professor, not one per point.
	type group struct {
		areas        []string
		universityID string
		ids, hashes  []string
		docHashes    []string
	}
	groups := map[string]*group{}
	for _, d := range toRepayload {
		if h := held[d.id]; h.docHash != "" && h.docHash != d.payload.docHash() {
			// the work itself changed (title, year, url): replace its whole payload
			if err := postJSON(http.MethodPost, qdrantURL()+"/collections/"+workCollection+"/points/payload?wait=true",
				map[string]any{"payload": d.payload, "points": []string{d.id}}, nil); err != nil {
				return fmt.Errorf("failed to refresh payload: %w", err)
			}
			if err := record([]string{d.id}, []string{d.payload.hash()}, []string{d.payload.docHash()}, nil); err != nil {
				return err
			}
			continue
		}
		key := d.payload.UniversityID + "|" + strings.Join(d.payload.Areas, ",")
		g := groups[key]
		if g == nil {
			g = &group{areas: d.payload.Areas, universityID: d.payload.UniversityID}
			groups[key] = g
		}
		g.ids = append(g.ids, d.id)
		g.hashes = append(g.hashes, d.payload.hash())
		g.docHashes = append(g.docHashes, d.payload.docHash())
	}
	for _, g := range groups {
		for i := 0; i < len(g.ids); i += 1000 {
			j := min(i+1000, len(g.ids))
			if err := postJSON(http.MethodPost, qdrantURL()+"/collections/"+workCollection+"/points/payload?wait=true",
				map[string]any{"payload": map[string]any{"areas": g.areas, "university_id": g.universityID},
					"points": g.ids[i:j]}, nil); err != nil {
				return fmt.Errorf("failed to refresh payload: %w", err)
			}
			if err := record(g.ids[i:j], g.hashes[i:j], g.docHashes[i:j], nil); err != nil {
				return err
			}
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

	logger.Infof(mainCtx, "🧠 Semantic index ready: %d grants and papers", len(seen))
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
// universityIDs, when given, limits the search to work at those universities (one, or a country's).
func searchWork(goal string, areas []string, universityIDs []string, kind string, depth int) ([]workHit, error) {
	vector, err := embedQuery(goal)
	if err != nil {
		return nil, err
	}

	var must []map[string]any
	if len(areas) > 0 {
		must = append(must, map[string]any{"key": "areas", "match": map[string]any{"any": areas}})
	}
	if len(universityIDs) > 0 {
		must = append(must, map[string]any{"key": "university_id", "match": map[string]any{"any": universityIDs}})
	}
	if kind != "" {
		must = append(must, map[string]any{"key": "kind", "match": map[string]any{"value": kind}})
	}
	req := map[string]any{
		"vector": vector,
		"limit":  depth,
		// Only what matching needs: payloads are stored on disk, and the long title and url fields made
		// a 4,000-hit search take 5.7 s instead of 0.2 s. Titles come from Postgres for the few shown.
		"with_payload":    []string{"name", "university_id", "year", "kind", "ref"},
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

// scorePersonWork rates one professor's work of one kind ("paper", "award") against a goal:
// ref -> similarity, for every item Qdrant holds for them (no score threshold).
func scorePersonWork(goal, name, kind string, limit int) (map[string]float64, error) {
	vector, err := embedQuery(goal)
	if err != nil {
		return nil, err
	}
	req := map[string]any{
		"vector":       vector,
		"limit":        limit,
		"with_payload": []string{"ref"},
		"filter": map[string]any{"must": []map[string]any{
			{"key": "name", "match": map[string]any{"value": name}},
			{"key": "kind", "match": map[string]any{"value": kind}},
		}},
	}
	var res struct {
		Result []workHit `json:"result"`
	}
	if err := postJSON(http.MethodPost, qdrantURL()+"/collections/"+workCollection+"/points/search", req, &res); err != nil {
		return nil, err
	}
	scores := make(map[string]float64, len(res.Result))
	for _, h := range res.Result {
		scores[h.Payload.Ref] = h.Score
	}
	return scores, nil
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
// areas and universityIDs narrow the search; depth bounds how many grants/papers are considered.
func semanticFacultyMatches(goal string, areas []string, universityIDs []string, depth int) ([]semanticMatch, error) {
	hits, err := searchWork(goal, areas, universityIDs, "", depth)
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
	hits, err := searchWork(goal, areas, nil, "award", depth)
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

type similarPerson struct {
	Name       string  `json:"name"`
	University string  `json:"university"`
	Score      float64 `json:"score"`
	Source     string  `json:"source"`
}

// getExplorerSimilar: GET /explorer/faculty/similar?name= — people whose work is closest to this
// person's: Qdrant recommends from their own papers and grants (average vector), excluding them,
// and the hits are grouped by person.
func getExplorerSimilar(w http.ResponseWriter, r *http.Request) {
	db, err := GetDB()
	if err != nil {
		writeError(w, r, http.StatusInternalServerError, "database unavailable", err)
		return
	}
	name := r.URL.Query().Get("name")
	if !semanticAvailable() {
		writeJSON(w, http.StatusOK, map[string]any{"similar": []similarPerson{}})
		return
	}
	rows, err := db.Query(`
		SELECT md5(name || '|' || kind || '|' || ref)::uuid::text FROM explorer_work_docs
		WHERE name = $1 ORDER BY year DESC NULLS LAST LIMIT 20`, name)
	if err != nil {
		writeError(w, r, http.StatusInternalServerError, "failed to load work", err)
		return
	}
	var ids []string
	for rows.Next() {
		var id string
		if rows.Scan(&id) == nil {
			ids = append(ids, id)
		}
	}
	rows.Close()
	if len(ids) == 0 {
		writeJSON(w, http.StatusOK, map[string]any{"similar": []similarPerson{}})
		return
	}
	var res struct {
		Result []workHit `json:"result"`
	}
	if err := postJSON(http.MethodPost, qdrantURL()+"/collections/"+workCollection+"/points/recommend", map[string]any{
		"positive": ids, "strategy": "average_vector", "limit": 80, "with_payload": []string{"name"},
		"filter": map[string]any{"must_not": []map[string]any{{"key": "name", "match": map[string]any{"value": name}}}},
	}, &res); err != nil {
		writeError(w, r, http.StatusBadGateway, "semantic search failed", err)
		return
	}
	best := map[string]float64{}
	var order []string
	for _, h := range res.Result {
		if _, seen := best[h.Payload.Name]; !seen {
			order = append(order, h.Payload.Name)
			best[h.Payload.Name] = h.Score
		}
	}
	if len(order) > 6 {
		order = order[:6]
	}
	people := []similarPerson{}
	for _, n := range order {
		p := similarPerson{Name: n, Score: best[n]}
		if db.QueryRow(`SELECT university, source FROM explorer_faculty WHERE name = $1`, n).Scan(&p.University, &p.Source) == nil {
			people = append(people, p)
		}
	}
	writeJSON(w, http.StatusOK, map[string]any{"similar": people})
}
