# US STEM and medicine beyond CS — data sources

_Researched 2026-10-04. [V] = verified by a live probe or official page that day; [I] = inferred._

## Key finding
OpenAlex `/awards` (17.6M grants, incl. ~2.28M from NIH ExPORTER, 644k NSF, USDA, USAspending) carries
lead-investigator names, activity codes (e.g. T32), amounts, dates and institution ROR, CC0 [V].
Together with OpenAlex authors/topics/works it can supply faculty, field areas and papers outside CS.
Keep our own NSF tables as the source of truth (OpenAlex links only ~44k NSF awards to a US institution).

## Faculty rosters (no CSRankings equivalent)
- Seed: NSF + NIH principal investigators at universities. NIH records include the person's title
  ("ASSOCIATE PROFESSOR OF MEDICINE"), department and a stable `profile_id` [V]; NSF has no title.
- Fill-in: OpenAlex authors at US universities, filtered by heuristics (career ≥ ~8 y, ≥ ~25 works, h ≥ ~10,
  recent education affiliation, last-author share) [I]. OpenAlex API now needs a key: $1/day free;
  list call $0.0001, search $0.001; snapshot is free on S3 (authors ≈ 58.8 GB parquet) [V].
- ORCID dump: not recommended. ACS Directory of Graduate Research (chemistry) discontinued in 2016 [V].

## Field taxonomy
OpenAlex: 4 domains, 26 fields (Chemistry 16, Physics & Astronomy 31, Engineering 22, Medicine 27,
Materials 25, Earth & Planetary 19), ~250 subfields, ~4.5k topics; per-author topic counts [V].
Plan: hand-group ~150 STEM/medicine subfields into ~40–50 student-facing areas; keep CSRankings areas for CS.
Secondary: NSF programs (in DB), NIH RCDC categories (`spending_categories_desc`), CIP via IPEDS completions.

## Grant sources beyond NSF
| Source | Access | PI names | Notes |
|---|---|---|---|
| NIH RePORTER API v2 [V] | `POST https://api.reporter.nih.gov/v2/projects/search` | yes (+title, profile_id) | FY2025: 76,355 projects; 500/request, offset ≤ 14,999, ~1 req/s; public domain |
| NIH ExPORTER [V/I] | https://reporter.nih.gov/exporter/ (JS-generated links) | yes | yearly CSV zips; API is simpler |
| OpenAlex /awards [V] | `https://api.openalex.org/awards?filter=funder.id:…` | lead_investigator | funder_scheme (T32), ROR, linked works; CC0 |
| DOE Office of Science [V] | PAMS award search (Excel export) | yes | ~2014–present |
| NASA [V/I] | TechPort API (token) | partial | technology projects only; low priority |
| DoD [I] | none with PI names | no | — |
| USDA NIFA [V] | portal.nifa.usda.gov (manual export) | yes | agriculture/ecology |
| USAspending [V/I] | api.usaspending.gov | no | institution-level totals only |

## Papers outside CS
OpenAlex works by author: one list call per author (~$10 per 100k authors at published prices) [I].
PubMed only as a cross-check for medicine; Crossref not needed.

## Student-funding signals
- NIH T32 training grants: 1,682 active in FY2025 [V] — funded PhD/postdoc programmes with a named director.
- NIH F31: individual predoctoral fellowships (signals labs that take funded students) [I].
- NSF NRT traineeships: already in our NSF data (program element name to confirm) [I]; open to non-citizens.
- NSF GRFP: student-held, US citizens/PR only — general note, not per professor.

## Proposed phases
1. NIH RePORTER FY2021–2026 via API; NSF+NIH PIs as faculty; T32/NRT badges; interim areas from NSF programs / NIH institutes.
2. OpenAlex key; match PIs to OpenAlex authors (name + ROR); ~45 grouped areas; recent works.
3. OpenAlex faculty-like authors without grants (marked unverified); DOE Office of Science export.
4. Defer: NASA, DoD, USAspending, ORCID, CIP matching.
