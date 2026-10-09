package main

import (
	"crypto/sha1"
	"database/sql"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"path/filepath"
	"sort"
	"strconv"
	"strings"
	"time"

	colly "github.com/gocolly/colly/v2"
	"github.com/lib/pq"
)

// The fetcher container (fetcher/app.py) runs the scripts that fetch every source outside
// CSRankings, NSF and IPEDS (those three are fetched in Go). The pipeline asks it to run a group of
// sources and waits for them; a source that fails, runs out of time or stops at an API allowance
// keeps its previous data, and the scheduler (startPipelineScheduler) runs the pipeline again later
// to finish it. Without FETCHER_URL, or with the fetcher down, the steps use the data on disk.

type fetchSource struct {
	Status   string   `json:"status"`
	Exit     any      `json:"exit"`
	Finished string   `json:"finished"`
	Fresh    bool     `json:"fresh"`
	LogTail  []string `json:"log_tail"`
}

type fetchGroup struct {
	Running []string               `json:"running"`
	Sources map[string]fetchSource `json:"sources"`
}

func fetcherURL() string { return strings.TrimRight(os.Getenv("FETCHER_URL"), "/") }

func fetchWait() time.Duration {
	if h, err := strconv.ParseFloat(os.Getenv("FETCH_WAIT_HOURS"), 64); err == nil && h > 0 {
		return time.Duration(h * float64(time.Hour))
	}
	return 6 * time.Hour
}

func fetcherCall(method, path string) (*fetchGroup, error) {
	req, err := http.NewRequest(method, fetcherURL()+path, nil)
	if err != nil {
		return nil, err
	}
	resp, err := (&http.Client{Timeout: 30 * time.Second}).Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	if resp.StatusCode >= 300 {
		return nil, fmt.Errorf("fetcher: HTTP %d", resp.StatusCode)
	}
	var g fetchGroup
	return &g, json.NewDecoder(resp.Body).Decode(&g)
}

// runFetchGroup starts a group's stale sources and waits until none is running (or the wait runs
// out). It never fails the pipeline: missing data is reported, and the load steps use what's there.
func runFetchGroup(mainCtx *colly.Context, group string, wait bool) *fetchGroup {
	if fetcherURL() == "" {
		logger.Warnf(mainCtx, "⚠️ FETCHER_URL not set: using the %s data already on disk", group)
		return nil
	}
	g, err := fetcherCall(http.MethodPost, "/run?group="+group)
	if err != nil {
		logger.Warnf(mainCtx, "⚠️ fetcher unreachable (%v): using the %s data already on disk", err, group)
		return nil
	}
	logger.Infof(mainCtx, "📥 Fetching %s sources: %s", group, strings.Join(g.Running, ", "))
	deadline := time.Now().Add(fetchWait())
	if !wait {
		deadline = time.Now()
	}
	for len(g.Running) > 0 && time.Now().Before(deadline) {
		time.Sleep(30 * time.Second)
		if next, err := fetcherCall(http.MethodGet, "/status?group="+group); err == nil {
			g = next
		}
	}
	if len(g.Running) > 0 && wait {
		logger.Warnf(mainCtx, "⚠️ still fetching after %s: %s (their previous data is used; the next run picks them up)",
			fetchWait(), strings.Join(g.Running, ", "))
	}
	names := make([]string, 0, len(g.Sources))
	for name := range g.Sources {
		names = append(names, name)
	}
	sort.Strings(names)
	for _, name := range names {
		s := g.Sources[name]
		switch s.Status {
		case "ok":
			logger.Infof(mainCtx, "📥 %s: ok (%s)", name, s.Finished)
		case "running":
		default:
			tail := ""
			if len(s.LogTail) > 0 {
				tail = s.LogTail[len(s.LogTail)-1]
			}
			logger.Warnf(mainCtx, "⚠️ %s: %s (exit %v) %s", name, s.Status, s.Exit, tail)
		}
	}
	return g
}

// fetchBaseSources: grants, DAAD scholarships and the DBLP dump, before the steps that load them.
func fetchBaseSources(mainCtx *colly.Context) error {
	runFetchGroup(mainCtx, "base", true)
	return nil
}

// openAlexOutputs are the files the OpenAlex fetches write and the load steps read.
var openAlexOutputs = []string{"fields_people.csv", "fields_works.csv", "subfields.csv", "works.csv"}

// openAlexLoadedPath records the outputs' fingerprint at the last load (data/fetch_state/).
func openAlexLoadedPath() string {
	return filepath.Join(getRootDirPath(DATA_DIR), "fetch_state", "openalex-loaded.txt")
}

func openAlexLoaded() (string, time.Time) {
	b, err := os.ReadFile(openAlexLoadedPath())
	if err != nil {
		return "", time.Time{}
	}
	info, _ := os.Stat(openAlexLoadedPath())
	return strings.TrimSpace(string(b)), info.ModTime()
}

// fetchOpenAlexSources runs after the explorer tables are built, because OpenAlex's inputs come
// from them: the universities to find researchers at, and the papers' DOIs to look up. The fetcher
// runs the OpenAlex sources as a daemon (they span several daily allowances), so this exports the
// inputs, nudges the daemon, and loads whatever arrived since the last load: the steps that read
// OpenAlex data run again. The scheduler calls back here whenever new data has arrived.
func fetchOpenAlexSources(mainCtx *colly.Context) error {
	db, err := GetDB()
	if err != nil {
		return fmt.Errorf("cannot get DB: %w", err)
	}
	if err := exportOpenAlexInputs(db); err != nil {
		logger.Warnf(mainCtx, "⚠️ could not export OpenAlex inputs: %v", err)
		return nil
	}
	runFetchGroup(mainCtx, "openalex", false)
	loaded, _ := openAlexLoaded()
	current := contentHashes(openAlexOutputs)
	if current == loaded {
		logger.Infof(mainCtx, "📥 OpenAlex: nothing new since the last load")
		return nil
	}
	// The fetch scripts refuse to shrink their outputs; this is the second lock on that door.
	if db, err := GetDB(); err == nil {
		var before int
		if db.QueryRow(`SELECT count(*) FROM explorer_faculty WHERE source = 'openalex'`).Scan(&before) == nil {
			if now := countLines(openAlexFieldsPath("fields_people.csv")); now < before*9/10 {
				logger.Warnf(mainCtx, "⚠️ OpenAlex researchers fell from %d to %d: not loading them", before, now)
				return nil
			}
		}
	}
	logger.Infof(mainCtx, "📥 OpenAlex: new data; loading it")
	for _, step := range []struct {
		name string
		fn   func(*colly.Context) error
	}{
		{"Load OpenAlex Researchers", loadOpenAlexResearchers},
		{"Remove Edge Case Entries", removeEdgeCaseEntries},
		{"Classify Institutions", classifyInstitutions},
		{"Link IPEDS Institutions", linkIpedsInstitutions},
		{"Merge Duplicate Institutions", mergeDuplicateInstitutions},
		{"Link NSF Investigators To Professors", linkInvestigatorsToProfessors},
		{"Load Funder Grants", loadFunderGrants},
		{"Link Funder Grants", linkFunderGrants},
		{"Load DBLP Papers", loadDblpPapers},
		{"Load OpenAlex Researcher Works", loadOpenAlexResearcherWorks},
		{"Link NSF Investigators By DBLP Affiliation", linkNsfByDblpAffiliation},
		{"Load OpenAlex Works", loadOpenAlexWorks},
		{"Build Explorer Tables", buildExplorerTables},
	} {
		logger.Infof(mainCtx, "🔁 %s (new OpenAlex data)", step.name)
		if err := step.fn(mainCtx); err != nil {
			return fmt.Errorf("%s after the OpenAlex fetch: %w", step.name, err)
		}
	}
	if err := os.WriteFile(openAlexLoadedPath(), []byte(current+"\n"), 0o644); err != nil {
		logger.Warnf(mainCtx, "⚠️ could not record the OpenAlex load: %v", err)
	}
	return nil
}

// fieldsCountries orders the universities on the map outside the US for the researcher fetch
// (fields beyond computing): it spends a daily allowance, so the countries where it helps students
// from Pakistan most come first. The ten main PhD destinations; then countries with no grant data
// (researchers are the only signal there); then the rest of Europe; India last (Pakistani students
// rarely go there). Every other country follows, before India.
var fieldsCountries = [][]string{
	{"de", "gb", "ca", "au", "cn", "kr", "tr", "it", "nl", "jp"},
	{"sa", "my", "ae", "qa"},
	{"fr", "at", "ch", "es", "se", "dk", "no", "fi", "be", "ie", "pt", "pl", "cz", "gr", "ee", "hu", "sk",
		"lv", "lu", "mt", "cy", "bg"},
	{"*"},
	{"in"},
}

// exportOpenAlexInputs writes the files fields.py and works.py read: the explorer's US R1
// universities and every university outside the US, in fieldsCountries' order
// (data/openalex/universities.csv, name and country), and its papers' DOIs (data/openalex/dois.txt).
func exportOpenAlexInputs(db *sql.DB) error {
	dir := openAlexFieldsPath("")
	if err := os.MkdirAll(dir, 0o755); err != nil {
		return err
	}
	// US R1s first, then fieldsCountries' order; within a tier by country and name, so the order (and
	// the researchers' cached works groups) of earlier lists holds.
	var countries []string
	var tiers []int64
	rest := int64(0)
	for i, tier := range fieldsCountries {
		for _, c := range tier {
			if c == "*" {
				rest = int64(i + 1)
				continue
			}
			countries, tiers = append(countries, c), append(tiers, int64(i+1))
		}
	}
	if err := writeLines(db, filepath.Join(dir, "universities.csv"), "name,country",
		`SELECT u.name, u.country FROM explorer_universities u
		 LEFT JOIN (SELECT unnest($1::text[]) AS country, unnest($2::int[]) AS tier) t ON t.country = u.country
		 WHERE u.country <> 'us' OR u.carnegie = 'R1'
		 ORDER BY CASE WHEN u.country = 'us' THEN 0 ELSE COALESCE(t.tier, $3) END, u.country, u.name`,
		pq.Array(countries), pq.Array(tiers), rest); err != nil {
		return err
	}
	return writeLines(db, filepath.Join(dir, "dois.txt"), "",
		`SELECT DISTINCT lower(substring(url from 'doi\.org/(.+)$')) FROM explorer_work_docs
		 WHERE kind = 'paper' AND url ~* 'doi\.org/' ORDER BY 1`)
}

// writeLines writes one value per line (after an optional header), replacing the file only when
// complete. A CSV header means values are quoted when they need it.
func writeLines(db *sql.DB, path, header, query string, args ...any) error {
	rows, err := db.Query(query, args...)
	if err != nil {
		return err
	}
	defer rows.Close()
	var b strings.Builder
	if header != "" {
		b.WriteString(header + "\n")
	}
	cols, err := rows.Columns()
	if err != nil {
		return err
	}
	n := 0
	for rows.Next() {
		vals := make([]string, len(cols))
		ptrs := make([]any, len(cols))
		for i := range vals {
			ptrs[i] = &vals[i]
		}
		if err := rows.Scan(ptrs...); err != nil {
			return err
		}
		for i, v := range vals {
			if header != "" && strings.ContainsAny(v, ",\"\n") {
				vals[i] = `"` + strings.ReplaceAll(v, `"`, `""`) + `"`
			}
		}
		b.WriteString(strings.Join(vals, ",") + "\n")
		n++
	}
	if err := rows.Err(); err != nil {
		return err
	}
	if n == 0 {
		return fmt.Errorf("%s: nothing to export yet", filepath.Base(path))
	}
	tmp := path + ".tmp"
	if err := os.WriteFile(tmp, []byte(b.String()), 0o644); err != nil {
		return err
	}
	return os.Rename(tmp, path)
}

func countLines(path string) int {
	f, err := os.Open(path)
	if err != nil {
		return 0
	}
	defer f.Close()
	n, buf := 0, make([]byte, 1<<20)
	for {
		k, err := f.Read(buf)
		for _, b := range buf[:k] {
			if b == '\n' {
				n++
			}
		}
		if err != nil {
			return n
		}
	}
}

// contentHashes fingerprints the files' contents: a script may rewrite a file without changing it,
// and only a real change should reload the OpenAlex steps.
func contentHashes(names []string) string {
	var b strings.Builder
	for _, n := range names {
		f, err := os.Open(openAlexFieldsPath(n))
		if err != nil {
			continue
		}
		h := sha1.New()
		_, _ = io.Copy(h, f)
		f.Close()
		fmt.Fprintf(&b, "%s:%x;", n, h.Sum(nil))
	}
	return b.String()
}

// startPipelineScheduler checks every few hours whether the data needs another pipeline run: the
// last complete run is older than PIPELINE_REFRESH_DAYS (default 7), or a fetch was left partial
// (an API allowance), failed, or unfinished. The pipeline keeps serving the previous data meanwhile.
func startPipelineScheduler(mainCtx *colly.Context) {
	days := 7.0
	if v, err := strconv.ParseFloat(os.Getenv("PIPELINE_REFRESH_DAYS"), 64); err == nil && v > 0 {
		days = v
	}
	go func() {
		for {
			time.Sleep(6 * time.Hour)
			if reason, from := pipelineDue(mainCtx, days); reason != "" {
				logger.Infof(mainCtx, "🗓️ Running the pipeline again from step %d: %s", from, reason)
				runPipeline(mainCtx, from)
			}
		}
	}()
}

// pipelineDue says whether to run the pipeline again, why, and from which step (1 = everything).
func pipelineDue(mainCtx *colly.Context, days float64) (string, int) {
	if pipelineRunning.Load() {
		return "", 0
	}
	var last time.Time
	if db, err := GetDB(); err == nil {
		if db.QueryRow(`SELECT last_run FROM pipeline_status WHERE pipeline_name = $1`,
			string(POPULATION_SUCCEEDED_MESSAGE)).Scan(&last) == nil && time.Since(last) > time.Duration(days*24)*time.Hour {
			return fmt.Sprintf("the last complete run was %.0f days ago", time.Since(last).Hours()/24), 1
		}
	}
	// A run that failed (a step's error, say a dropped connection) resumes at the step that failed,
	// at most every few hours (the scheduler's period), instead of waiting for the weekly refresh.
	if GetPipelineStatus(mainCtx, string(PIPELINE_POPULATE_POSTGRES)) == string(PIPELINE_STATUS_FAILED) {
		return "the last run failed; resuming at the step that failed", 0
	}
	// New OpenAlex data from the daemon: load it (steps from "Fetch OpenAlex Data" on), at most twice
	// a day; a day's fetch usually lands once.
	if loaded, at := openAlexLoaded(); time.Since(at) > 12*time.Hour && contentHashes(openAlexOutputs) != loaded {
		return "new OpenAlex data arrived", openAlexStep()
	}
	if fetcherURL() == "" {
		return "", 0
	}
	groups := map[string]*fetchGroup{}
	for _, group := range []string{"base", "openalex"} {
		g, err := fetcherCall(http.MethodGet, "/status?group="+group)
		if err != nil {
			return "", 0
		}
		groups[group] = g
	}
	// A source still fetching when the pipeline stopped waiting (FETCH_WAIT_HOURS) finishes later:
	// load it now rather than at the weekly refresh. "Later" is after its group's fetch step last
	// completed (the load steps follow it); once reloaded that step is newer, so this fires once.
	// (OpenAlex's daemon output is handled above, by content.)
	fetchStep := map[string]string{"base": "%Fetch Source Data"}
	for group, g := range groups {
		if fetchStep[group] == "" {
			continue
		}
		var stepDone time.Time
		if db, err := GetDB(); err != nil || db.QueryRow(`SELECT COALESCE(max(last_run), 'epoch') FROM pipeline_status
			WHERE pipeline_name LIKE $1 AND status = 'completed'`, fetchStep[group]).Scan(&stepDone) != nil {
			continue
		}
		for name, s := range g.Sources {
			if f, err := time.Parse(time.RFC3339, s.Finished); err == nil && s.Status == "ok" &&
				stepDone.Year() > 1970 && f.After(stepDone) {
				return fmt.Sprintf("%s finished after the pipeline last loaded it", name), 1
			}
		}
	}
	// Unfinished fetches are retried at most about once a day: an API allowance resets daily, and a
	// source that keeps failing shouldn't rerun the whole pipeline every few hours.
	if !last.IsZero() && time.Since(last) < 20*time.Hour {
		return "", 0
	}
	if g := groups["base"]; g != nil { // OpenAlex's daemon retries on its own
		for name, s := range g.Sources {
			if s.Status == "partial" || s.Status == "failed" || s.Status == "interrupted" {
				return fmt.Sprintf("%s was left %s", name, s.Status), 1
			}
		}
	}
	return "", 0
}

// openAlexStep is the 1-based number of the "Fetch OpenAlex Data" step.
func openAlexStep() int {
	for i, st := range pipelineSteps() {
		if st.name == "Fetch OpenAlex Data" {
			return i + 1
		}
	}
	return 1
}
