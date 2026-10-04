# Europe — research-grant data sources

_Probed 2026-10-04. "Verified" = real response seen; otherwise inferred._

| Rank | Source | Access | Named PIs | Licence | CS filter | Size |
|---|---|---|---|---|---|---|
| 1 | **France ANR** — verified | data.gouv.fr dataset `60ca2086030c7b7e52e2c02e`: partners CSV (`…-partenaires.csv`) and projects CSV (FR+EN abstracts) | yes — `Responsable_scientifique.Nom/.Prenom/.ORCID` per partner, `Est_coordinateur` | ODbL | committee in `Code_Decision` (e.g. ANR-21-**CE23**-…: AI; CE25, CE39, CE48, CE33, CE46 inferred) | partners 18.6 MB; projects 140 MB |
| 2 | **UK UKRI GtR** — verified | CSV export `https://gtr.ukri.org/search/project/csv?term=*&selectedFacets=<base64 facets>` (EPSRC `ZnVuZGVyfEVQU1JDfHN0cmluZw==`, Research Grant `Y2F0fFJlc2VhcmNoIEdyYW50fHN0cmluZw==`, Fellowship `Y2F0fEZlbGxvd3NoaXB8c3RyaW5n`); per-project JSON `https://gtr.ukri.org/api/projects?ref=EP%2FX036820%2F1` (persons, org, fund, abstract inline) | yes — PISurname, PIFirstName, ORCID | Open Government Licence v2.0 | `Department` column or per-project researchSubjects ("Info. & commun. Technol.") | EPSRC grants ≈ 12–15 MB CSV |
| 3 | **EU CORDIS** — verified | `https://cordis.europa.eu/data/cordis-HORIZONprojects-csv.zip` (36.9 MB), `cordis-h2020projects-csv.zip` (55.2 MB); ERC PIs (H2020 only) `https://cordis.europa.eu/data/cordis-h2020-erc-pi.xlsx` (0.5 MB, 8,044 rows) | organisations only, except the ERC PI xlsx; Horizon Europe ERC PIs only in per-call PDFs (panel **PE6** = CS) | Commission Decision 2011/833/EU | euroSciVoc `/23/47` (3,351 of 20,145 HE projects) | see left |
| 4 | **Switzerland SNSF** — verified | `https://data.snf.ch/datasets/grants.csv` (64.3 MB), `persons.csv` (47.2 MB), xlsx smaller | yes — persons with ORCID | open use with source attribution | `MainDisciplineNumber` 20506 "Information Technology" (others possible) | ~110 MB CSV |
| — | CORDIS MSCA Doctoral Networks | `fundingScheme` HORIZON-TMA-MSCA-DN(-JD/-ID); H2020 MSCA-ITN(-EJD/-EID) | organisations only | as CORDIS | — | — |
| ✗ | Italy PRIN (MUR) | per-sector "Allegato A" PDFs; mur.gov.it Cloudflare-blocked; no CSV on dati.gov.it | PDF only | — | PE6 | — |
| ✗ | Germany DFG GEPRIS | robots `Disallow: /`; no export/API | — | — | — | do not scrape |

## Notes
- CORDIS amounts in EUR with comma decimals; files semicolon-separated.
- GtR legacy API v7 links persons/funds by URL; the newer `/api/projects?ref=` JSON has everything inline (~15 KB).
- ANR has a start date but no end date.

## DAAD scholarship database (Germany) — verified
No API, but the database ships as static JSON-in-JS:
`https://www2.daad.de/bundles/daadstipendiendatenbanklsh/data/a/js/scholarships.js` (682 KB, 150 programmes)
with lookups `origin.js` (Pakistan = 194), `status.js` (1 undergrad, 3 graduates, 4 doctoral, 2 postdoc, 5 faculty).
Pakistan + graduate/doctoral → 71 programmes. Could feed the scholarship list per country of origin.
