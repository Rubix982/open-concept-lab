package main

import (
	"fmt"
	"net/http"
	"strconv"
	"sync"
	"sync/atomic"
	"time"

	colly "github.com/gocolly/colly/v2"
	"github.com/lib/pq"
)

// The Funding tab searches every grant loaded (explorer_grants), most of them held by people who
// aren't on the map, so they have their own Qdrant collection: one point per grant, embedded from its
// title and the start of its abstract, with the country and end date to filter on. Without it the
// tab matches words only.
const (
	grantCollection = "explorer_grants"
	grantMinScore   = 0.42 // below this a grant isn't counted as being about the search (see landscape)
	grantSearchMax  = 5000 // the most grants a search counts by meaning
)

// grantEnds turns an end date into a number Qdrant can compare: 2027-03-31 -> 20270331.
func grantEnds(t *time.Time) int {
	if t == nil {
		return 0
	}
	y, m, d := t.Date()
	return y*10000 + int(m)*100 + d
}

// embedGrants brings the grant collection in line with explorer_grants: embeds new and changed
// grants, deletes points for grants that are gone. explorer_grants_embedded remembers what Qdrant holds.
func embedGrants(mainCtx *colly.Context) error {
	probe := &http.Client{Timeout: 3 * time.Second}
	for _, u := range []string{embedderURL() + "/health", qdrantURL() + "/collections"} {
		resp, err := probe.Get(u)
		if err != nil {
			logger.Warnf(mainCtx, "⚠️ %s unreachable (%v); the Funding tab keeps matching words", u, err)
			return nil
		}
		resp.Body.Close()
	}
	db, err := GetDB()
	if err != nil {
		return fmt.Errorf("cannot get DB: %w", err)
	}

	var exists struct {
		Status string `json:"status"`
	}
	if err := postJSON(http.MethodGet, qdrantURL()+"/collections/"+grantCollection, nil, &exists); err != nil {
		if err := postJSON(http.MethodPut, qdrantURL()+"/collections/"+grantCollection,
			map[string]any{"vectors": map[string]any{"size": embeddingDim, "distance": "Cosine"},
				"quantization_config": map[string]any{"scalar": map[string]any{"type": "int8", "quantile": 0.99, "always_ram": true}}},
			nil); err != nil {
			return fmt.Errorf("failed to create Qdrant collection: %w", err)
		}
		if _, err := db.Exec(`TRUNCATE explorer_grants_embedded`); err != nil {
			return fmt.Errorf("failed to reset explorer_grants_embedded: %w", err)
		}
	}
	_ = postJSON(http.MethodPut, qdrantURL()+"/collections/"+grantCollection+"/index",
		map[string]any{"field_name": "country", "field_schema": "keyword"}, nil)
	_ = postJSON(http.MethodPut, qdrantURL()+"/collections/"+grantCollection+"/index",
		map[string]any{"field_name": "ends", "field_schema": "integer"}, nil)

	held := map[string]string{}
	rows, err := db.Query(`SELECT id::text, hash FROM explorer_grants_embedded`)
	if err != nil {
		return fmt.Errorf("failed to read explorer_grants_embedded: %w", err)
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

	// The hash covers the text and the payload: either changing means a new point.
	rows, err = db.Query(`
		SELECT md5(funder || '|' || id)::uuid::text, funder, id, COALESCE(country, ''), ends,
		       title || CASE WHEN snippet IS NULL THEN '' ELSE '. ' || snippet END
		FROM explorer_grants`)
	if err != nil {
		return fmt.Errorf("failed to read grants: %w", err)
	}
	type grantDoc struct {
		id, text, hash string
		payload        map[string]any
	}
	// Streamed: read a batch of grants that need embedding, embed and record it, read on. Holding all
	// ~1M grants' texts at once ran the Docker VM out of memory (swap full, every batch stalling).
	flush := func(batch []grantDoc) error {
		texts := make([]string, len(batch))
		for j, d := range batch {
			texts[j] = d.text
		}
		vectors, err := embedTexts(texts)
		if err != nil {
			return fmt.Errorf("failed to embed batch: %w", err)
		}
		points := make([]map[string]any, len(batch))
		ids, hashes := make([]string, len(batch)), make([]string, len(batch))
		for j, d := range batch {
			points[j] = map[string]any{"id": d.id, "vector": vectors[j], "payload": d.payload}
			ids[j], hashes[j] = d.id, d.hash
		}
		if err := postJSON(http.MethodPut, qdrantURL()+"/collections/"+grantCollection+"/points?wait=true",
			map[string]any{"points": points}, nil); err != nil {
			return fmt.Errorf("failed to upsert points: %w", err)
		}
		if _, err := db.Exec(`
			INSERT INTO explorer_grants_embedded (id, hash)
			SELECT unnest($1::uuid[]), unnest($2::text[])
			ON CONFLICT (id) DO UPDATE SET hash = EXCLUDED.hash`, pq.Array(ids), pq.Array(hashes)); err != nil {
			return fmt.Errorf("failed to record embedded grants: %w", err)
		}
		return nil
	}
	logger.Infof(mainCtx, "💰 Grant index: %d held; embedding new and changed grants", len(held))
	// A few batches in flight: the embedder uses only a few of the machine's cores per request, and
	// three at once roughly doubled throughput. The first error stops the rest.
	const workers = 3
	jobs := make(chan []grantDoc, workers)
	var wg sync.WaitGroup
	var failMu sync.Mutex
	var failed error
	var done atomic.Int64
	for w := 0; w < workers; w++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for b := range jobs {
				failMu.Lock()
				stop := failed != nil
				failMu.Unlock()
				if stop {
					continue
				}
				if err := flush(b); err != nil {
					failMu.Lock()
					if failed == nil {
						failed = err
					}
					failMu.Unlock()
					continue
				}
				done.Add(int64(len(b)))
			}
		}()
	}
	failure := func() error {
		failMu.Lock()
		defer failMu.Unlock()
		return failed
	}
	seen := make(map[string]struct{}, len(held))
	batch := make([]grantDoc, 0, embedBatchSize)
	start, lastLog := time.Now(), time.Now()
	for rows.Next() {
		var d grantDoc
		var funder, gid, country string
		var ends *time.Time
		if err := rows.Scan(&d.id, &funder, &gid, &country, &ends, &d.text); err != nil {
			rows.Close()
			return err
		}
		seen[d.id] = struct{}{}
		d.hash = textHash(d.text + "|" + country + "|" + strconv.Itoa(grantEnds(ends)))
		if held[d.id] == d.hash {
			continue
		}
		d.payload = map[string]any{"funder": funder, "id": gid, "country": country, "ends": grantEnds(ends)}
		if batch = append(batch, d); len(batch) == embedBatchSize {
			if err := failure(); err != nil {
				break
			}
			jobs <- batch
			batch = make([]grantDoc, 0, embedBatchSize)
			if time.Since(lastLog) > time.Minute {
				lastLog = time.Now()
				logger.Infof(mainCtx, "💰 Embedded %d grants (%s, %d held before)", done.Load(), time.Since(start).Round(time.Second), len(held))
			}
		}
	}
	if len(batch) > 0 && failure() == nil {
		jobs <- batch
	}
	close(jobs)
	wg.Wait()
	rows.Close()
	if err := failure(); err != nil {
		return err
	}
	if err := rows.Err(); err != nil {
		return fmt.Errorf("failed to read grants: %w", err)
	}
	logger.Infof(mainCtx, "💰 Embedded %d grants (%s)", done.Load(), time.Since(start).Round(time.Second))
	var toDelete []string
	for id := range held {
		if _, ok := seen[id]; !ok {
			toDelete = append(toDelete, id)
		}
	}
	for i := 0; i < len(toDelete); i += 1000 {
		batch := toDelete[i:min(i+1000, len(toDelete))]
		if err := postJSON(http.MethodPost, qdrantURL()+"/collections/"+grantCollection+"/points/delete?wait=true",
			map[string]any{"points": batch}, nil); err != nil {
			return fmt.Errorf("failed to delete points: %w", err)
		}
		if _, err := db.Exec(`DELETE FROM explorer_grants_embedded WHERE id = ANY($1::uuid[])`, pq.Array(batch)); err != nil {
			return err
		}
	}
	grantSearchState.Lock()
	grantSearchState.checked = time.Time{}
	grantSearchState.Unlock()
	logger.Infof(mainCtx, "💰 Grant index ready: %d grants", len(seen))
	return nil
}

var grantSearchState struct {
	sync.Mutex
	checked time.Time
	ok      bool
}

// grantSearchReady: the embedder is up and the grant collection holds points (cached 30 s).
func grantSearchReady() bool {
	grantSearchState.Lock()
	defer grantSearchState.Unlock()
	if time.Since(grantSearchState.checked) < 30*time.Second {
		return grantSearchState.ok
	}
	grantSearchState.checked = time.Now()
	var info struct {
		Result struct {
			PointsCount int `json:"points_count"`
		} `json:"result"`
	}
	grantSearchState.ok = semanticAvailable() &&
		postJSON(http.MethodGet, qdrantURL()+"/collections/"+grantCollection, nil, &info) == nil &&
		info.Result.PointsCount > 0
	return grantSearchState.ok
}

type grantHit struct {
	Funder string
	ID     string
	Score  float64
}

// searchGrants returns the grants closest in meaning to q, best first, within a country and to the
// running ones when asked.
func searchGrants(q, country string, active bool) ([]grantHit, error) {
	vector, err := embedQuery(q)
	if err != nil {
		return nil, err
	}
	var must []map[string]any
	if country != "" {
		must = append(must, map[string]any{"key": "country", "match": map[string]any{"value": country}})
	}
	if active {
		must = append(must, map[string]any{"key": "ends", "range": map[string]any{"gte": grantEnds(ptr(time.Now()))}})
	}
	req := map[string]any{
		"vector": vector, "limit": grantSearchMax, "score_threshold": grantMinScore,
		"with_payload": []string{"funder", "id"},
	}
	if len(must) > 0 {
		req["filter"] = map[string]any{"must": must}
	}
	var res struct {
		Result []struct {
			Score   float64 `json:"score"`
			Payload struct {
				Funder string `json:"funder"`
				ID     string `json:"id"`
			} `json:"payload"`
		} `json:"result"`
	}
	if err := postJSON(http.MethodPost, qdrantURL()+"/collections/"+grantCollection+"/points/search", req, &res); err != nil {
		return nil, err
	}
	hits := make([]grantHit, len(res.Result))
	for i, r := range res.Result {
		hits[i] = grantHit{r.Payload.Funder, r.Payload.ID, r.Score}
	}
	return hits, nil
}

func ptr[T any](v T) *T { return &v }
