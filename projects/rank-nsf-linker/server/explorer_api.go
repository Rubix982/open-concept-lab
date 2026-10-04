package main

import (
	"database/sql"
	"encoding/json"
	"net/http"
	"net/url"
	"sort"
	"strconv"
	"strings"
	"time"

	chi "github.com/go-chi/chi/v5"
	"github.com/lib/pq"
)

// Student-facing explorer API: area -> universities -> faculty -> their work and funding.
// Everything reads the explorer_* tables built by the "Build Explorer Tables" step.
//
//	GET /explorer/areas
//	GET /explorer/universities?areas=ml,nlp&q=<goal>
//	GET /explorer/universities/{id}
//	GET /explorer/faculty?areas=ml&q=<goal>&university=<id>&limit=50
//	GET /explorer/faculty/profile?name=<name>
//	GET /explorer/faculty/papers?name=<name>
//	GET /explorer/grants?q=<goal>&areas=ml&active=1
//	GET /explorer/scholarships?country=DE&nationality=PK&level=phd

const (
	maxRecentPapers = 12
	maxFacultyLimit = 200
)

func writeJSON(w http.ResponseWriter, status int, v any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(v)
}

func writeError(w http.ResponseWriter, r *http.Request, status int, msg string, err error) {
	if err != nil {
		logger.Errorf(buildCollyContext(w, r), "%s: %v", msg, err)
	}
	writeJSON(w, status, map[string]string{"error": msg})
}

// areasParam reads ?areas=ml,nlp into a list of area codes.
func areasParam(r *http.Request) []string {
	areas := []string{} // never nil: pq sends a nil slice as NULL, which disables the area filter checks
	for _, a := range strings.Split(r.URL.Query().Get("areas"), ",") {
		if a = strings.TrimSpace(a); a != "" {
			areas = append(areas, a)
		}
	}
	return areas
}

type exploreArea struct {
	Group   string `json:"group"`
	Area    string `json:"area"`
	Name    string `json:"name"`
	Faculty int    `json:"faculty"`
	Funded  int    `json:"funded"`
}

func getExplorerAreas(w http.ResponseWriter, r *http.Request) {
	db, err := GetDB()
	if err != nil {
		writeError(w, r, http.StatusInternalServerError, "database unavailable", err)
		return
	}
	rows, err := db.Query(`
		SELECT v.area_group, v.area, v.area_name,
		       count(f.name), count(f.name) FILTER (WHERE f.active_awards > 0)
		FROM (SELECT DISTINCT area_group, area, area_name FROM research_area_venues) v
		LEFT JOIN explorer_faculty f ON v.area = ANY (f.areas)
		GROUP BY v.area_group, v.area, v.area_name
		ORDER BY v.area_group, v.area_name`)
	if err != nil {
		writeError(w, r, http.StatusInternalServerError, "failed to load areas", err)
		return
	}
	defer rows.Close()

	areas := []exploreArea{}
	for rows.Next() {
		var a exploreArea
		if err := rows.Scan(&a.Group, &a.Area, &a.Name, &a.Faculty, &a.Funded); err != nil {
			writeError(w, r, http.StatusInternalServerError, "failed to read areas", err)
			return
		}
		areas = append(areas, a)
	}
	if err := rows.Err(); err != nil {
		writeError(w, r, http.StatusInternalServerError, "failed to read results", err)
		return
	}
	writeJSON(w, http.StatusOK, areas)
}

type exploreUniversity struct {
	ID                    string          `json:"id"`
	Name                  string          `json:"name"`
	City                  *string         `json:"city"`
	State                 *string         `json:"state"`
	Country               *string         `json:"country"`
	Latitude              *float64        `json:"latitude"`
	Longitude             *float64        `json:"longitude"`
	Homepage              *string         `json:"homepage,omitempty"`
	Carnegie              *string         `json:"carnegie"`
	GradTuitionInState    *int            `json:"grad_tuition_in_state,omitempty"`
	GradTuitionOutOfState *int            `json:"grad_tuition_out_of_state,omitempty"`
	GradEnrollment        *int            `json:"grad_enrollment,omitempty"`
	FacultyTotal          int             `json:"faculty_total"`
	FundedTotal           int             `json:"funded_total"`
	Faculty               int             `json:"faculty"`      // in the selected areas
	Funded                int             `json:"funded"`       // in the selected areas, with an active NSF award
	GoalMatches           int             `json:"goal_matches"` // faculty whose NSF work matches the goal text
	AreaFaculty           json.RawMessage `json:"area_faculty,omitempty"`
	AreaFunded            json.RawMessage `json:"area_funded,omitempty"`
	GrantFunders          []string        `json:"grant_funders,omitempty"` // funders whose grants are loaded for this country
}

// getExplorerUniversities lists universities with faculty in the selected areas (all areas if
// none), with how many of them hold active NSF funding and, given ?q=, match the goal text.
func getExplorerUniversities(w http.ResponseWriter, r *http.Request) {
	db, err := GetDB()
	if err != nil {
		writeError(w, r, http.StatusInternalServerError, "database unavailable", err)
		return
	}
	areas := areasParam(r)
	q := strings.TrimSpace(r.URL.Query().Get("q"))

	// Semantic matching when available: count matching faculty per university; the SQL then
	// skips its keyword count.
	var semantic map[string]int
	keywordGoal := q
	if q != "" && semanticAvailable() {
		matches, err := semanticFacultyMatches(q, areas, "", 4000)
		if err != nil {
			logger.Warnf(buildCollyContext(w, r), "⚠️ semantic matching failed, using keywords: %v", err)
		} else {
			semantic = map[string]int{}
			for _, m := range matches {
				semantic[m.University]++
			}
			keywordGoal = ""
		}
	}

	rows, err := db.Query(`
		WITH goal AS (SELECT CASE WHEN $2 = '' THEN NULL ELSE websearch_to_tsquery('english', $2) END AS q),
		matched AS (
			SELECT f.university,
			       count(*) AS faculty,
			       count(*) FILTER (WHERE f.active_awards > 0) AS funded,
			       count(*) FILTER (WHERE goal.q IS NOT NULL AND EXISTS (
			         SELECT 1 FROM explorer_work_docs d WHERE d.name = f.name AND d.doc @@ goal.q)) AS goal_matches
			FROM explorer_faculty f, goal
			WHERE cardinality($1::text[]) = 0 OR f.areas && $1::text[]
			GROUP BY f.university
		)
		SELECT u.id, u.name, u.city, u.state, u.country, u.latitude, u.longitude, u.carnegie,
		       u.faculty_count, u.funded_faculty, m.faculty, m.funded, m.goal_matches
		FROM matched m JOIN explorer_universities u ON u.name = m.university
		ORDER BY m.goal_matches DESC, m.funded DESC, m.faculty DESC, u.name`, pq.Array(areas), keywordGoal)
	if err != nil {
		writeError(w, r, http.StatusInternalServerError, "failed to load universities", err)
		return
	}
	defer rows.Close()

	unis := []exploreUniversity{}
	for rows.Next() {
		var u exploreUniversity
		if err := rows.Scan(&u.ID, &u.Name, &u.City, &u.State, &u.Country, &u.Latitude, &u.Longitude, &u.Carnegie,
			&u.FacultyTotal, &u.FundedTotal, &u.Faculty, &u.Funded, &u.GoalMatches); err != nil {
			writeError(w, r, http.StatusInternalServerError, "failed to read universities", err)
			return
		}
		unis = append(unis, u)
	}
	if err := rows.Err(); err != nil {
		writeError(w, r, http.StatusInternalServerError, "failed to read results", err)
		return
	}
	if semantic != nil {
		for i := range unis {
			unis[i].GoalMatches = semantic[unis[i].ID]
		}
		sort.SliceStable(unis, func(i, j int) bool {
			a, b := unis[i], unis[j]
			if a.GoalMatches != b.GoalMatches {
				return a.GoalMatches > b.GoalMatches
			}
			if a.Funded != b.Funded {
				return a.Funded > b.Funded
			}
			return a.Faculty > b.Faculty
		})
	}
	writeJSON(w, http.StatusOK, unis)
}

func getExplorerUniversity(w http.ResponseWriter, r *http.Request, id string) {
	db, err := GetDB()
	if err != nil {
		writeError(w, r, http.StatusInternalServerError, "database unavailable", err)
		return
	}
	var u exploreUniversity
	var areaFaculty, areaFunded []byte
	err = db.QueryRow(`
		SELECT id, name, city, state, country, latitude, longitude, homepage, carnegie,
		       grad_tuition_in_state, grad_tuition_out_of_state, grad_enrollment,
		       faculty_count, funded_faculty, area_faculty, area_funded
		FROM explorer_universities WHERE id = $1`, id).Scan(
		&u.ID, &u.Name, &u.City, &u.State, &u.Country, &u.Latitude, &u.Longitude, &u.Homepage, &u.Carnegie,
		&u.GradTuitionInState, &u.GradTuitionOutOfState, &u.GradEnrollment,
		&u.FacultyTotal, &u.FundedTotal, &areaFaculty, &areaFunded)
	if err == sql.ErrNoRows {
		writeError(w, r, http.StatusNotFound, "university not found", nil)
		return
	}
	if err != nil {
		writeError(w, r, http.StatusInternalServerError, "failed to load university", err)
		return
	}
	u.AreaFaculty, u.AreaFunded = areaFaculty, areaFunded
	if u.Country != nil {
		u.GrantFunders = grantFundersByCountry(db)[*u.Country]
	}
	writeJSON(w, http.StatusOK, u)
}

type exploreFaculty struct {
	Name          string          `json:"name"`
	University    string          `json:"university"`
	UniversityID  *string         `json:"university_id"`
	Country       *string         `json:"country"` // ISO alpha-2, lowercase; grant data is US (NSF) only so far
	Homepage      *string         `json:"homepage"`
	ScholarID     *string         `json:"scholar_id"`
	Areas         []string        `json:"areas"`
	AreaPubs      json.RawMessage `json:"area_pubs"`
	RecentPubs    float64         `json:"recent_pubs"`
	ActiveAwards  int             `json:"active_awards"`
	TotalAwards   int             `json:"total_awards"`
	ActiveFunding int64           `json:"active_funding"`
	LastAward     *time.Time      `json:"last_award_date"`
	Funding       json.RawMessage `json:"funding"` // per funder: active/total grants and active amount, own currency
	GoalScore     *float64        `json:"goal_score,omitempty"`
	Match         *exploreWork    `json:"match,omitempty"` // the professor's award or paper closest to the goal
}

type exploreWork struct {
	Funder *string `json:"funder,omitempty"` // for awards: "nsf", "marsden", "arc", ...
	Kind   *string `json:"kind"`             // "award" | "paper"
	Title  *string `json:"title"`
	Year   *int    `json:"year"`
	URL    *string `json:"url"`
}

// getExplorerFaculty ranks faculty in the selected areas: by how well their NSF work matches
// ?q= when given, otherwise by recent publications in those areas.
func getExplorerFaculty(w http.ResponseWriter, r *http.Request) {
	db, err := GetDB()
	if err != nil {
		writeError(w, r, http.StatusInternalServerError, "database unavailable", err)
		return
	}
	areas := areasParam(r)
	q := strings.TrimSpace(r.URL.Query().Get("q"))
	universityID := strings.TrimSpace(r.URL.Query().Get("university"))
	limit := 50
	if n, err := strconv.Atoi(r.URL.Query().Get("limit")); err == nil && n > 0 {
		limit = min(n, maxFacultyLimit)
	}

	if q != "" && semanticAvailable() {
		depth := 2000
		if universityID != "" {
			depth = 800
		}
		matches, err := semanticFacultyMatches(q, areas, universityID, depth)
		if err == nil {
			faculty, err := facultyForMatches(db, matches, limit)
			if err != nil {
				writeError(w, r, http.StatusInternalServerError, "failed to load faculty", err)
				return
			}
			writeJSON(w, http.StatusOK, faculty)
			return
		}
		logger.Warnf(buildCollyContext(w, r), "⚠️ semantic matching failed, using keywords: %v", err)
	}

	rows, err := db.Query(`
		WITH goal AS (SELECT CASE WHEN $2 = '' THEN NULL ELSE websearch_to_tsquery('english', $2) END AS q),
		best AS ( -- each professor's single best-matching award or paper, favouring recent work:
		          -- the text match decays by half about every 5.5 years
			SELECT DISTINCT ON (d.name) d.name, d.kind, d.ref, d.title, d.year, d.url,
			       ts_rank_cd(d.doc, goal.q, 1)
			         * exp(-greatest(extract(year FROM current_date) - COALESCE(d.year, 2010), 0) / 8.0) AS score
			FROM explorer_work_docs d, goal
			WHERE goal.q IS NOT NULL AND d.doc @@ goal.q
			ORDER BY d.name, score DESC, d.year DESC NULLS LAST
		)
		SELECT f.name, f.university, u.id, u.country, f.homepage, f.scholar_id, f.areas, f.area_pubs, f.recent_pubs,
		       f.active_awards, f.total_awards, f.active_funding, f.last_award_date, f.funding,
		       best.score, best.kind, best.ref, best.title, best.year, best.url
		FROM explorer_faculty f
		CROSS JOIN goal
		LEFT JOIN best ON best.name = f.name
		LEFT JOIN explorer_universities u ON u.name = f.university
		WHERE (cardinality($1::text[]) = 0 OR f.areas && $1::text[])
		  AND ($3 = '' OR u.id = $3)
		  AND (goal.q IS NULL OR best.name IS NOT NULL)
		ORDER BY best.score DESC NULLS LAST, (f.active_awards > 0) DESC,
		         (SELECT COALESCE(sum((f.area_pubs ->> a)::real), 0) FROM unnest($1::text[]) a) DESC,
		         f.recent_pubs DESC
		LIMIT $4`, pq.Array(areas), q, universityID, limit)
	if err != nil {
		writeError(w, r, http.StatusInternalServerError, "failed to load faculty", err)
		return
	}
	defer rows.Close()

	faculty := []exploreFaculty{}
	for rows.Next() {
		var f exploreFaculty
		var areaPubs, funding []byte
		var match exploreWork
		var matchRef *string
		if err := rows.Scan(&f.Name, &f.University, &f.UniversityID, &f.Country, &f.Homepage, &f.ScholarID, pq.Array(&f.Areas),
			&areaPubs, &f.RecentPubs, &f.ActiveAwards, &f.TotalAwards, &f.ActiveFunding, &f.LastAward, &funding,
			&f.GoalScore, &match.Kind, &matchRef, &match.Title, &match.Year, &match.URL); err != nil {
			writeError(w, r, http.StatusInternalServerError, "failed to read faculty", err)
			return
		}
		f.AreaPubs, f.Funding = areaPubs, funding
		if match.Title != nil {
			if match.Kind != nil && *match.Kind == "award" && matchRef != nil {
				funder := funderOfRef(*matchRef)
				match.Funder = &funder
			}
			f.Match = &match
		}
		faculty = append(faculty, f)
	}
	if err := rows.Err(); err != nil {
		writeError(w, r, http.StatusInternalServerError, "failed to read results", err)
		return
	}
	writeJSON(w, http.StatusOK, faculty)
}

// facultyForMatches loads the explorer rows for the best semantic matches, keeping their order.
func facultyForMatches(db *sql.DB, matches []semanticMatch, limit int) ([]exploreFaculty, error) {
	if len(matches) > limit {
		matches = matches[:limit]
	}
	names := make([]string, len(matches))
	for i, m := range matches {
		names[i] = m.Name
	}
	rows, err := db.Query(`
		SELECT f.name, f.university, u.id, u.country, f.homepage, f.scholar_id, f.areas, f.area_pubs, f.recent_pubs,
		       f.active_awards, f.total_awards, f.active_funding, f.last_award_date, f.funding
		FROM explorer_faculty f LEFT JOIN explorer_universities u ON u.name = f.university
		WHERE f.name = ANY($1)`, pq.Array(names))
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	byName := map[string]exploreFaculty{}
	for rows.Next() {
		var f exploreFaculty
		var areaPubs, funding []byte
		if err := rows.Scan(&f.Name, &f.University, &f.UniversityID, &f.Country, &f.Homepage, &f.ScholarID, pq.Array(&f.Areas),
			&areaPubs, &f.RecentPubs, &f.ActiveAwards, &f.TotalAwards, &f.ActiveFunding, &f.LastAward, &funding); err != nil {
			return nil, err
		}
		f.AreaPubs, f.Funding = areaPubs, funding
		byName[f.Name] = f
	}
	if err := rows.Err(); err != nil {
		return nil, err
	}

	faculty := make([]exploreFaculty, 0, len(matches))
	for _, m := range matches {
		f, ok := byName[m.Name]
		if !ok {
			continue
		}
		score := m.Rank
		work := m.Work
		f.GoalScore = &score
		f.Match = &exploreWork{Kind: &work.Kind, Title: &work.Title, Year: work.Year, URL: work.URL}
		if work.Kind == "award" {
			funder := funderOfRef(work.Ref)
			f.Match.Funder = &funder
		}
		faculty = append(faculty, f)
	}
	return faculty, nil
}

type exploreAward struct {
	ID       string     `json:"id"`
	Funder   string     `json:"funder"`   // "nsf", "marsden", "arc", ...
	Currency string     `json:"currency"` // ISO 4217
	Title    string     `json:"title"`
	Amount   float64    `json:"amount"`
	Starts   *time.Time `json:"starts"`
	Ends     *time.Time `json:"ends"`
	Active   bool       `json:"active"`
	Role     *string    `json:"role"`
	Abstract string     `json:"abstract"`
	URL      string     `json:"url"`
}

func getExplorerFacultyProfile(w http.ResponseWriter, r *http.Request) {
	db, err := GetDB()
	if err != nil {
		writeError(w, r, http.StatusInternalServerError, "database unavailable", err)
		return
	}
	name := r.URL.Query().Get("name")

	var f exploreFaculty
	var areaPubs, funding []byte
	err = db.QueryRow(`
		SELECT f.name, f.university, u.id, u.country, f.homepage, f.scholar_id, f.areas, f.area_pubs, f.recent_pubs,
		       f.active_awards, f.total_awards, f.active_funding, f.last_award_date, f.funding
		FROM explorer_faculty f LEFT JOIN explorer_universities u ON u.name = f.university
		WHERE f.name = $1`, name).Scan(&f.Name, &f.University, &f.UniversityID, &f.Country, &f.Homepage, &f.ScholarID,
		pq.Array(&f.Areas), &areaPubs, &f.RecentPubs, &f.ActiveAwards, &f.TotalAwards, &f.ActiveFunding, &f.LastAward, &funding)
	if err == sql.ErrNoRows {
		writeError(w, r, http.StatusNotFound, "professor not found", nil)
		return
	}
	if err != nil {
		writeError(w, r, http.StatusInternalServerError, "failed to load professor", err)
		return
	}
	f.AreaPubs, f.Funding = areaPubs, funding

	rows, err := db.Query(`
		SELECT DISTINCT ON (a.id) a.id, a.award_title_text, COALESCE(a.award_amount, 0),
		       NULLIF(a.award_effective_date, '')::date, NULLIF(a.award_expiry_date, '')::date,
		       p.pi_role, left(COALESCE(a.abstract, '') || '', 700) -- detoast first; see semantic.go
		FROM nsf_investigators i
		JOIN award_pi_rel p ON p.nsf_id = i.nsf_id
		JOIN award a ON a.id = p.award_id
		WHERE i.professor IN (SELECT name FROM professor_variants WHERE canonical = $1 UNION SELECT $1)
		ORDER BY a.id`, name)
	if err != nil {
		writeError(w, r, http.StatusInternalServerError, "failed to load awards", err)
		return
	}
	defer rows.Close()

	awards := []exploreAward{}
	now := time.Now()
	for rows.Next() {
		var a exploreAward
		if err := rows.Scan(&a.ID, &a.Title, &a.Amount, &a.Starts, &a.Ends, &a.Role, &a.Abstract); err != nil {
			writeError(w, r, http.StatusInternalServerError, "failed to read awards", err)
			return
		}
		a.Active = a.Ends != nil && a.Ends.After(now)
		a.Abstract = strings.TrimSpace(strings.ReplaceAll(a.Abstract, "<br/>", " "))
		a.URL = "https://www.nsf.gov/awardsearch/showAward?AWD_ID=" + url.QueryEscape(a.ID)
		a.Funder, a.Currency = "nsf", "USD"
		awards = append(awards, a)
	}
	if err := rows.Err(); err != nil {
		writeError(w, r, http.StatusInternalServerError, "failed to read results", err)
		return
	}
	// Grants from other funders (Marsden, ARC, ...).
	frows, err := db.Query(`
		SELECT g.funder || ':' || g.grant_id, g.funder, COALESCE(g.currency, ''), g.title, COALESCE(g.amount, 0),
		       g.starts, g.ends, p.role, left(COALESCE(g.abstract, '') || '', 700), COALESCE(g.url, '')
		FROM funder_grant_people p JOIN funder_grants g USING (funder, grant_id)
		WHERE p.professor IN (SELECT name FROM professor_variants WHERE canonical = $1 UNION SELECT $1)`, name)
	if err != nil {
		writeError(w, r, http.StatusInternalServerError, "failed to load grants", err)
		return
	}
	defer frows.Close()
	for frows.Next() {
		var a exploreAward
		if err := frows.Scan(&a.ID, &a.Funder, &a.Currency, &a.Title, &a.Amount, &a.Starts, &a.Ends, &a.Role,
			&a.Abstract, &a.URL); err != nil {
			writeError(w, r, http.StatusInternalServerError, "failed to read grants", err)
			return
		}
		a.Active = a.Ends != nil && a.Ends.After(now)
		awards = append(awards, a)
	}
	if err := frows.Err(); err != nil {
		writeError(w, r, http.StatusInternalServerError, "failed to read grants", err)
		return
	}

	// Active first, then newest.
	sortAwards(awards)

	writeJSON(w, http.StatusOK, map[string]any{"faculty": f, "awards": awards})
}

func sortAwards(awards []exploreAward) {
	less := func(a, b exploreAward) bool {
		if a.Active != b.Active {
			return a.Active
		}
		if a.Starts == nil || b.Starts == nil {
			return a.Starts != nil
		}
		return a.Starts.After(*b.Starts)
	}
	for i := 1; i < len(awards); i++ {
		for j := i; j > 0 && less(awards[j], awards[j-1]); j-- {
			awards[j], awards[j-1] = awards[j-1], awards[j]
		}
	}
}

type dblpPaper struct {
	Title string  `json:"title"`
	Venue *string `json:"venue"`
	Year  int     `json:"year"`
	URL   *string `json:"url"`
}

// getExplorerFacultyPapers returns a professor's most recent publications, loaded from the
// DBLP dump by the "Load DBLP Papers" step (DBLP and CSRankings share person names).
func getExplorerFacultyPapers(w http.ResponseWriter, r *http.Request) {
	db, err := GetDB()
	if err != nil {
		writeError(w, r, http.StatusInternalServerError, "database unavailable", err)
		return
	}
	name := r.URL.Query().Get("name")
	rows, err := db.Query(`
		SELECT DISTINCT ON (year, title) title, venue, year, url FROM dblp_papers
		WHERE name IN (SELECT name FROM professor_variants WHERE canonical = $1 UNION SELECT $1)
		ORDER BY year DESC, title LIMIT $2`, name, maxRecentPapers)
	if err != nil {
		writeError(w, r, http.StatusInternalServerError, "failed to load papers", err)
		return
	}
	defer rows.Close()

	papers := []dblpPaper{}
	for rows.Next() {
		var p dblpPaper
		if err := rows.Scan(&p.Title, &p.Venue, &p.Year, &p.URL); err != nil {
			writeError(w, r, http.StatusInternalServerError, "failed to read papers", err)
			return
		}
		papers = append(papers, p)
	}
	if err := rows.Err(); err != nil {
		writeError(w, r, http.StatusInternalServerError, "failed to read results", err)
		return
	}
	writeJSON(w, http.StatusOK, map[string]any{
		"dblp_url": "https://dblp.org/search?q=" + url.QueryEscape(name),
		"papers":   papers,
	})
}

// mountExplorerRoutes registers the explorer API on the router.
func mountExplorerRoutes(r chi.Router) {
	r.Get("/explorer/areas", getExplorerAreas)
	r.Get("/explorer/universities", getExplorerUniversities)
	r.Get("/explorer/universities/{id}", func(w http.ResponseWriter, r *http.Request) {
		getExplorerUniversity(w, r, chi.URLParam(r, "id"))
	})
	r.Get("/explorer/faculty", getExplorerFaculty)
	r.Get("/explorer/faculty/profile", getExplorerFacultyProfile)
	r.Get("/explorer/faculty/papers", getExplorerFacultyPapers)
	r.Get("/explorer/grants", getExplorerGrants)
	r.Get("/explorer/scholarships", getExplorerScholarships)
	r.Get("/explorer/funders", getExplorerFunders)
}

type grantPerson struct {
	Name         string  `json:"name"`
	University   string  `json:"university"`
	UniversityID *string `json:"university_id"`
}

type exploreGrant struct {
	exploreAward
	Similarity float64       `json:"similarity"`
	People     []grantPerson `json:"people"` // CSRankings faculty on the award
}

// getExplorerGrants lists NSF awards on the goal's topic (?q=, required) held by faculty in the
// selected areas: active ones by default (?active=0 for all), most similar first.
func getExplorerGrants(w http.ResponseWriter, r *http.Request) {
	db, err := GetDB()
	if err != nil {
		writeError(w, r, http.StatusInternalServerError, "database unavailable", err)
		return
	}
	areas := areasParam(r)
	q := strings.TrimSpace(r.URL.Query().Get("q"))
	activeOnly := r.URL.Query().Get("active") != "0"
	limit := 40
	if n, err := strconv.Atoi(r.URL.Query().Get("limit")); err == nil && n > 0 {
		limit = min(n, maxFacultyLimit)
	}
	if q == "" {
		writeJSON(w, http.StatusOK, []exploreGrant{})
		return
	}

	var matches []grantMatch
	if semanticAvailable() {
		matches, err = semanticGrantMatches(q, areas, 1500)
		if err != nil {
			logger.Warnf(buildCollyContext(w, r), "⚠️ semantic grant search failed, using keywords: %v", err)
			matches = nil
		}
	}
	if matches == nil {
		rows, err := db.Query(`
			SELECT d.ref, max(ts_rank_cd(d.doc, websearch_to_tsquery('english', $2), 1)) AS score, array_agg(d.name)
			FROM explorer_work_docs d JOIN explorer_faculty f ON f.name = d.name
			WHERE d.kind = 'award' AND d.doc @@ websearch_to_tsquery('english', $2)
			  AND (cardinality($1::text[]) = 0 OR f.areas && $1::text[])
			GROUP BY d.ref ORDER BY score DESC LIMIT 1500`, pq.Array(areas), q)
		if err != nil {
			writeError(w, r, http.StatusInternalServerError, "failed to search grants", err)
			return
		}
		for rows.Next() {
			var m grantMatch
			if err := rows.Scan(&m.AwardID, &m.Similarity, pq.Array(&m.People)); err != nil {
				rows.Close()
				writeError(w, r, http.StatusInternalServerError, "failed to read grants", err)
				return
			}
			matches = append(matches, m)
		}
		rows.Close()
	}

	ids := make([]string, len(matches))
	for i, m := range matches {
		ids[i] = m.AwardID
	}
	rows, err := db.Query(`
		SELECT a.id, a.award_title_text, COALESCE(a.award_amount, 0),
		       NULLIF(a.award_effective_date, '')::date, NULLIF(a.award_expiry_date, '')::date,
		       left(COALESCE(a.abstract, '') || '', 400) -- detoast first; see semantic.go
		FROM award a WHERE a.id = ANY($1)`, pq.Array(ids))
	if err != nil {
		writeError(w, r, http.StatusInternalServerError, "failed to load grants", err)
		return
	}
	awards := map[string]exploreAward{}
	now := time.Now()
	for rows.Next() {
		var a exploreAward
		if err := rows.Scan(&a.ID, &a.Title, &a.Amount, &a.Starts, &a.Ends, &a.Abstract); err != nil {
			rows.Close()
			writeError(w, r, http.StatusInternalServerError, "failed to read grants", err)
			return
		}
		a.Active = a.Ends != nil && a.Ends.After(now)
		a.URL = "https://www.nsf.gov/awardsearch/showAward?AWD_ID=" + url.QueryEscape(a.ID)
		a.Funder, a.Currency = "nsf", "USD"
		awards[a.ID] = a
	}
	rows.Close()

	// Other funders' grants are referenced as "<funder>:<grant id>".
	rows, err = db.Query(`
		SELECT funder || ':' || grant_id, funder, COALESCE(currency, ''), title, COALESCE(amount, 0), starts, ends,
		       left(COALESCE(abstract, '') || '', 400), COALESCE(url, '')
		FROM funder_grants WHERE funder || ':' || grant_id = ANY($1)`, pq.Array(ids))
	if err != nil {
		writeError(w, r, http.StatusInternalServerError, "failed to load grants", err)
		return
	}
	for rows.Next() {
		var a exploreAward
		if err := rows.Scan(&a.ID, &a.Funder, &a.Currency, &a.Title, &a.Amount, &a.Starts, &a.Ends, &a.Abstract,
			&a.URL); err != nil {
			rows.Close()
			writeError(w, r, http.StatusInternalServerError, "failed to read grants", err)
			return
		}
		a.Active = a.Ends != nil && a.Ends.After(now)
		awards[a.ID] = a
	}
	rows.Close()

	var names []string
	for _, m := range matches {
		names = append(names, m.People...)
	}
	people := map[string]grantPerson{}
	rows, err = db.Query(`
		SELECT f.name, f.university, u.id FROM explorer_faculty f
		LEFT JOIN explorer_universities u ON u.name = f.university WHERE f.name = ANY($1)`, pq.Array(names))
	if err != nil {
		writeError(w, r, http.StatusInternalServerError, "failed to load grant people", err)
		return
	}
	for rows.Next() {
		var p grantPerson
		if err := rows.Scan(&p.Name, &p.University, &p.UniversityID); err != nil {
			rows.Close()
			writeError(w, r, http.StatusInternalServerError, "failed to read grant people", err)
			return
		}
		people[p.Name] = p
	}
	rows.Close()

	// NSF files a collaborative project as one award per university with the same title; show
	// it once, with every PI and the combined amount.
	grants := []exploreGrant{}
	byTitle := map[string]int{}
	for _, m := range matches {
		a, ok := awards[m.AwardID]
		if !ok || (activeOnly && !a.Active) {
			continue
		}
		key := strings.ToLower(strings.TrimSpace(a.Title))
		i, seen := byTitle[key]
		if !seen {
			if len(grants) >= limit {
				continue
			}
			grants = append(grants, exploreGrant{exploreAward: a, Similarity: m.Similarity})
			i = len(grants) - 1
			byTitle[key] = i
		} else {
			grants[i].Amount += a.Amount
			grants[i].Active = grants[i].Active || a.Active
		}
		for _, n := range m.People {
			if p, ok := people[n]; ok && !hasPerson(grants[i].People, p.Name) {
				grants[i].People = append(grants[i].People, p)
			}
		}
	}
	writeJSON(w, http.StatusOK, grants)
}

func hasPerson(people []grantPerson, name string) bool {
	for _, p := range people {
		if p.Name == name {
			return true
		}
	}
	return false
}

// funderOfRef: "marsden:20-UOA-001" -> "marsden"; a bare NSF award id -> "nsf".
func funderOfRef(ref string) string {
	if i := strings.Index(ref, ":"); i > 0 {
		return ref[:i]
	}
	return "nsf"
}
