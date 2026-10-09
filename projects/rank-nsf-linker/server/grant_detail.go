package main

import (
	"database/sql"
	"encoding/json"
	"net/http"
	"strings"
	"time"

	"github.com/lib/pq"
)

// grantDetail is one grant in full, for Advisor Atlas's own grant page. Funders' sites can be out of
// reach (NSF's award pages are blocked from Pakistan), so everything a student needs to judge the
// grant is shown here, and the funder's record is the second step.
type grantDetail struct {
	Funder       string          `json:"funder"`
	ID           string          `json:"id"`
	Title        string          `json:"title"`
	Abstract     string          `json:"abstract"`
	Amount       *float64        `json:"amount"`
	Currency     *string         `json:"currency"`
	AmountUSD    *float64        `json:"amount_usd"`
	Starts       *time.Time      `json:"starts"`
	Ends         *time.Time      `json:"ends"`
	Active       bool            `json:"active"`
	URL          string          `json:"url"`
	Institution  string          `json:"institution"`
	UniversityID *string         `json:"university_id"`
	Country      *string         `json:"country"`
	Programs     []string        `json:"programs"` // NSF programme names, or the funder's scheme
	Signal       *string         `json:"signal"`   // new_lab / training
	Team         json.RawMessage `json:"team"`     // [{name, role, profile}]; profile set when they're in the explorer
}

// GET /explorer/grant?funder=nsf&id=2347472 (other funders: their own grant id, as explorer_grants
// holds it; "marsden:22-UOA-123" is accepted too).
func getExplorerGrant(w http.ResponseWriter, r *http.Request) {
	funder := strings.ToLower(strings.TrimSpace(r.URL.Query().Get("funder")))
	id := strings.TrimSpace(r.URL.Query().Get("id"))
	id = strings.TrimPrefix(id, funder+":") // a profile's grant ids carry the funder
	if funder == "" || id == "" {
		writeError(w, r, http.StatusBadRequest, "funder and id are required", nil)
		return
	}
	db, err := GetDB()
	if err != nil {
		writeError(w, r, http.StatusInternalServerError, "database unavailable", err)
		return
	}
	g := grantDetail{Funder: funder, ID: id}
	if funder == "nsf" {
		var amount sql.NullFloat64
		err = db.QueryRow(`
			SELECT a.award_title_text, COALESCE(a.abstract, '') || '', a.award_amount,
			       NULLIF(a.award_effective_date, '')::date, NULLIF(a.award_expiry_date, '')::date,
			       COALESCE(a.institution, ''),
			       COALESCE((SELECT array_agg(DISTINCT pe.name) FROM program_element pe
			                 WHERE pe.award_id = a.id AND COALESCE(pe.name, '') <> ''), '{}'),
			       COALESCE((SELECT jsonb_agg(jsonb_build_object(
			                   'name', o.first_name || ' ' || o.last_name,
			                   'role', CASE WHEN r2.pi_role ~* 'co-' THEN 'Co-PI' ELSE 'PI' END,
			                   'profile', (SELECT ef.name FROM explorer_faculty ef
			                               JOIN professor_variants v ON v.canonical = ef.name
			                               WHERE v.name = o.professor LIMIT 1))
			                   ORDER BY r2.pi_role ~* 'co-', o.last_name)
			                 FROM award_pi_rel r2 JOIN nsf_investigators o ON o.nsf_id = r2.nsf_id
			                 WHERE r2.award_id = a.id), '[]')
			FROM award a WHERE a.id = $1`, id).Scan(&g.Title, &g.Abstract, &amount, &g.Starts, &g.Ends,
			&g.Institution, pq.Array(&g.Programs), &g.Team)
		if amount.Valid {
			g.Amount = &amount.Float64
		}
		usdCode := "USD"
		g.Currency = &usdCode
		g.URL = "https://www.nsf.gov/awardsearch/showAward?AWD_ID=" + id
		g.Abstract = strings.TrimSpace(strings.ReplaceAll(g.Abstract, "<br/>", "\n"))
	} else {
		var amount sql.NullFloat64
		var currency, scheme, url sql.NullString
		err = db.QueryRow(`
			SELECT g.title, COALESCE(g.abstract, '') || '', g.amount, g.currency, g.starts, g.ends,
			       g.url, g.scheme,
			       COALESCE((SELECT split_part(p.institution, ' | ', 1) FROM funder_grant_people p
			                 WHERE p.funder = g.funder AND p.grant_id = g.grant_id AND COALESCE(p.institution, '') <> ''
			                 ORDER BY p.role <> 'PI' LIMIT 1), ''),
			       COALESCE((SELECT jsonb_agg(jsonb_build_object(
			                   'name', o.full_name, 'role', o.role,
			                   'profile', (SELECT ef.name FROM explorer_faculty ef
			                               JOIN professor_variants v ON v.canonical = ef.name
			                               WHERE v.name = o.professor LIMIT 1))
			                   ORDER BY o.role <> 'PI', o.full_name)
			                 FROM funder_grant_people o
			                 WHERE o.funder = g.funder AND o.grant_id = g.grant_id), '[]')
			FROM funder_grants g WHERE g.funder = $1 AND g.grant_id = $2`, funder, id).Scan(
			&g.Title, &g.Abstract, &amount, &currency, &g.Starts, &g.Ends, &url, &scheme, &g.Institution, &g.Team)
		if amount.Valid {
			g.Amount = &amount.Float64
		}
		if currency.Valid {
			g.Currency = &currency.String
		}
		g.URL = url.String
		if scheme.Valid && scheme.String != "" {
			g.Programs = []string{scheme.String}
		}
	}
	if err == sql.ErrNoRows {
		writeError(w, r, http.StatusNotFound, "grant not found", nil)
		return
	}
	if err != nil {
		writeError(w, r, http.StatusInternalServerError, "failed to load the grant", err)
		return
	}
	// Where it is on the map, and whether it's a new-lab or training grant (explorer_grants)
	_ = db.QueryRow(`SELECT university_id, country, signal FROM explorer_grants WHERE funder = $1 AND id = $2`,
		funder, id).Scan(&g.UniversityID, &g.Country, &g.Signal)
	g.Active = g.Ends != nil && g.Ends.After(time.Now())
	g.AmountUSD = usd(g.Amount, g.Currency)
	if g.Programs == nil {
		g.Programs = []string{}
	}
	writeJSON(w, http.StatusOK, g)
}
