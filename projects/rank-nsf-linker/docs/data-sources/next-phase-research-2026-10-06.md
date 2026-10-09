# Advisor Atlas: next-phase research (2026-10-06)

Method: I read the code; scanned the local OpenAlex awards snapshot already in `data/openalex_awards/` (210 files, read-only, no API calls); and read the official funder pages, through a helper agent. Anything marked UNVERIFIED is inference.

## A. Plan B/C funders

### A1. Austria FWF: build a direct loader, because OpenAlex has no FWF investigators
- **What OpenAlex has.** Provenance `openaire_fwf` holds 9,813 awards: titles 100%, amount 99.9%, abstract 90%. **Lead investigator 0% and institution 0%.** This comes from my scan of the local snapshot. FWF is not in `SOURCES`, and it should stay out.
- **The FWF Open API** is a Meilisearch instance at `https://openapi.fwf.ac.at` with indexes `projects`, `output` and `further-funding`.
  - Calls: `GET /indexes/projects/documents?limit=1000` or `POST /indexes/projects/search`, with header `Authorization: Bearer <key>`.
  - Docs: https://www.fwf.ac.at/en/discover/open-api, and documentation PDF v1.1 (effective 17 Mar 2026).
- **Key.** "The key for read access to the API is available at https://openapi.fwf.ac.at/fwfkey." It is one shared read key with no registration. Keep it in `server/.env` like the others anyway.
- **Fields:**
  - PI: first and last name, ORCID, `researchinstitute.name` and `.ror`.
  - Key and associate researchers.
  - Dates: start, end and approval.
  - `approvedamount`.
  - Summary in English and German, title, programme, disciplines and keywords.
  - Coverage: 1995 onward, updated daily.
  - Quote: "All attributes … are searchable, but are neither filterable nor facetable." So page through all documents and filter locally.
- **Licence.** "FWF Open API data is freely reusable under a CC0 license."
- **Rate limit.** No number is published. The terms forbid "automated mass access beyond the intended limits". Use 1 request/s with 1,000-row pages, which is about 30–40 calls in total (UNVERIFIED count). Contact: openapi(at)fwf.ac.at.
- **Next step:** write `grants/fwf.py` on the NWO pattern (cached pages, `common.write`), add it to the fetcher `SOURCES` with a 30-day age, and match institutions through ROR. **Effort: 2–3 h.**

### A2. Germany DFG GEPRIS: ask first; meanwhile show grants at institution level
- **robots.txt** at https://gepris.dfg.de/robots.txt reads `User-agent: *` / `Disallow: /`. It allows only named search and AI-search bots.
- **The site is a JavaScript app** since the relaunch on 2 Jul 2026 (dfg.de notice ifw-26-43).
- **Imprint** (read from the site's JS bundle): "Any use of the project abstract texts …, whether for commercial or non-commercial purposes, requires the consent of the respective authors." I found no explicit text about crawling and no licence for the metadata.
- **Export.** The app calls internal endpoints, including `/backend/project/export`, which returns a file for a search. This suggests a "download results" feature, but it is UNVERIFIED as a supported service and I did not call it. There is no documented API or open-data offer.
- **Contact:** gepris@dfg.de (in the imprint and on dfg.de/…/informationssysteme). The relaunch notice names Markus Jagsch (Markus.Jagsch@dfg.de) and Holger Hahnen (Holger.Hahnen@dfg.de).
- **What OpenAlex `gepris` has** (my scan): 144,460 awards, 72,076 of them running in 2015 or later.
  - No PI in any record.
  - Amount 99.6%; abstract and title ~100%.
  - Institution: only 2,584 have `institution_awarded`, and another 26,633 carry only an affiliation name. **So about 20% have an institution.** The survey said "Inst Y", which was too generous.
  - Abstracts fall under DFG's consent clause, so **do not show the GEPRIS abstracts**.
- **What we could show without a PI.** On the university page: "DFG-funded projects here: N running, €X total". Add the titles of the most recent projects, each linking to GEPRIS, as a lab-activity signal. Without matching to people, only the ~29k records with an institution work. This covers Germany's 70 universities, the largest group of the 10 countries.
- **Draft email** (to gepris@dfg.de, cc Markus Jagsch):
  > Dear GEPRIS team, I run Advisor Atlas, a free, non-commercial map that helps students, mainly from Pakistan, find PhD supervisors through their papers and grants. I would like to show, for DFG-funded projects, the project title, the principal investigators, their institution, the funding period and a link back to the GEPRIS page. I would not show the abstracts. Could you tell me whether this reuse is permitted? Is there a data export (for example the new export function, or a periodic file) that you would prefer we use rather than any automated access to the site? We are happy to credit DFG/GEPRIS in whatever form you ask.
- **Next step:** send the email now (**10 min**). Then build the institution-only DFG line from `gepris` records with an institution and no abstract (**2–3 h**, mostly UI). Add PIs only after DFG says yes.

### A3. Sweden SweCRIS: a key is not needed
- **What OpenAlex has** (my scan):

  | Provenance | Awards | With lead investigator | With amount |
  |---|---|---|---|
  | `swedish_research_council` | 23,080 | 22,858 | 22,924 |
  | `swecris_vinnova` | 24,247 | 23,893 | 23,954 |
  | `formas` | 7,311 | 7,289 | — |
  | `forte` | 2,656 | 2,636 | — |

  The institution is mostly the lead's affiliation name; `institution_awarded` is rare. **`forte` is missing from `SOURCES` in openalex_awards.py; add it.**
- **SweCRIS itself.**
  - Personal-key form: https://www.vr.se/english/swecris/swecris-api/request-for-api-token.html. It asks for first name, surname, organisation and email, plus consent to VR's data policy. The key comes "on e-mail to you within a week".
  - Public test token: "VRSwecrisAPI2026-1". It rotates.
  - Terms: "All data in Swecris is openly accessible. You may use the information … internally and publicly, but we appreciate it if you … tell that it comes from Swecris." No formal licence is named.
- **Next step:** add `"forte"` to `SOURCES` and record the terms string as the quote above for all four sources (**5 min**). Don't build a SweCRIS loader. Register a key only if the institution-name matching proves poor (**form: 5 min, wait: up to a week**).

### A4. Korea NRF / NTIS
- **The NRF file on data.go.kr:** 한국연구재단_이알앤디_과제정보, https://www.data.go.kr/data/3049029/fileData.do
  - CSV with 11,788 rows, downloadable without login.
  - Licence: "이용허락범위 제한 없음" (no restriction).
  - Updated yearly; last changed 2026-08-28.
  - Fields: business year, selection year, programme levels, project title, **PI name (연구책임자명)**, researcher number, host institution, security flag.
  - **No amount, dates or abstract.** Described as "일부" (some projects), so it is not complete.
- **NTIS project-search API.** On data.go.kr (15077315, run by KISTI): attribution licence (공공누리 Type 1), auto-approval for development, reviewed approval for production. It needs a data.go.kr account, and the signup page limits individual members to "만 14세 이상 내국인" (Korean nationals). NTIS's own OpenAPI says "모든 신청자는 회원정보에 소속기관 정보를 등록해야" (all applicants must register an affiliation), which is then checked. Whether a foreigner without a Korean phone or affiliation can verify is UNVERIFIED, and unlikely. **This matches TODO's "key needs a Korean affiliation".**
- **OpenAlex** has no Korean direct-source provenance. NRF there is Crossref stubs only.
- **Next step:** a small `grants/nrf_kr.py` that downloads the CSV. Dates come from the selection year, assuming 3 years (an assumption). Romanising Hangul names is the hard part: PI names are in Korean script, while OpenAlex and CSRankings use romanised names. Match on institution plus a revised-romanisation table, and expect a modest match rate. **Effort: 3–4 h.** Lower priority than FWF.

## B. More researchers outside CS (item 9)

**Current state** (from `data/openalex/`):
- `universities.csv` has 414 rows: 144 US R1s plus 270 in the 10 countries. Only the 144 US institutions are resolved so far (144 cached lookups), so **the 10-country cut has not spent its author calls yet.**
- `fields_people.csv` has 56,369 researchers at 165 universities.
  - US: about 364 per university (min 74, median 391, max 500).
  - Pakistan (lower thresholds): median about 200, range 27–415.

**Name resolution is already wrong in English.** I recomputed the cached lookups for the 144 US R1s:
- **No hit (3):** "California Inst of Technology", "Massachusetts Inst of Technology", "The University of Alabama".
- **Wrong hit (4):**
  - UIUC resolved to "Lemann Center for Brazilian Studies", so it has 0 researchers.
  - "Ohio University" resolved to The Ohio State University. **On screen now, 374 Ohio State researchers (e.g. John Beacom, Eric Braaten) are labelled Ohio University.**
  - "University of Arkansas" resolved to UAMS (182 researchers).
  - "University of Texas at San Antonio" resolved to the UT Health Science Center (288).

That is about 5% wrong or missing. `resolve_institutions` takes the first education or facility hit with no name check. The cause is CSRankings' short names, and outside the US they are worse:
- India: "CMI", "IMSc", "IACS", "NISER", "DAIICT", "IGDTUW", "IIT (BHU) Varanasi", "Jaypee Univ. of Info. Tech."
- China: "BUPT", "HUST", "NWPU", "CUHK (SZ)"
- Australia: "UNSW"
- Brazil: "UFMG", "USP-ICMC"
- France: "CNRS", "INRIA", "CRIStAL". These are labs or government bodies, so the type filter either drops them or a random lab matches.

On IIT campuses: OpenAlex has one institution per IIT, so pinning the id works. It is the abbreviated search that is fragile (UNVERIFIED, since I could not query).

Affiliation staleness: `last_known_institutions[0]` lags moves by months. The 3-year activity filter limits the damage, but a recent mover will show at the old university.

**Size and budget** (estimates). Calls per university are 1 lookup + 25 field pages + works (1–3 calls per 50 people), about 35–60.

| Batch | Universities | Calls | Researchers (UNVERIFIED) |
|---|---|---|---|
| Current 10-country cut | 270 | ~16k | — |
| India | ~42 on the map (52 in CSRankings) | ~2.5k | 4k–10k (100–250 each; new IITs are small) |
| Other ~49 countries | ~185 | ~11k | 20k–55k |

The fetcher caps `openalex-fields` at 5,000 calls per run and the scheduler reruns about daily. So: the current cut takes ~3–4 days, India ~1 day, and the rest ~2–3 more days. Works.py shares the same 9k.

**Recommended order by student benefit.** Value is highest where we have nothing else:
1. Saudi Arabia, Malaysia, UAE, Qatar (~12 universities). No grant data exists there, so researchers and papers are the only signal.
2. European destinations: Sweden, France, Switzerland, Austria, Ireland, Finland, Norway, Denmark, Belgium. Grant data now exists for most of them.
3. Hong Kong, Singapore, Taiwan, New Zealand.
4. India. Many universities, but Pakistani students rarely study there because of visas. Its value is for South Asian users in general.
5. Brazil, Bangladesh, Iran, the rest.

**Next steps:**
1. **Before the 10-country author fetch spends calls:** add a curated override file (e.g. `backup/openalex_institutions.csv`, name → OpenAlex id, like `extra_universities.csv`). Make `fields.py` reject a hit whose name shares no distinctive word with the input, and write `data/openalex/resolution_review.csv` (input, OpenAlex name, type) to read before the authors step. Fix the 7 US cases. **Effort: 2 h, plus 1 h to review ~500 names.**
2. Then widen `fieldsCountries` in the order above. **Effort: 5 min per batch, plus calls.**

## C. Fresh-pod test (item 10)

### What each step needs on an empty `data/`

**Fetched automatically:**
- Go: CSRankings `csrankings.csv`, `generated-author-info.csv`, `countries.csv`, and `institutions.csv` → `country-info.csv`; NSF 2010–2025; IPEDS.
- Fetcher: NIH, UKRI, KAKEN API pages, ARC, ANR (+RNSR), SNSF, CORDIS + ERC HE PDFs (from `backup/erc_he_sources.txt`), RGC, NSERC, NWO, DAAD, DBLP, the OpenAlex awards snapshot from S3, OpenAlex works and fields.
- Pipeline-exported inputs: `universities.csv` and `dois.txt`.

**Curated and committed (fine):**
- `backup/`: `geolocation.csv`, `country-info.csv`, `university_coordinates.csv`, `ipeds_links.csv`, `institution_aliases.csv`, `universities_against_homepages.csv`, `extra_universities.csv`, `scholarships.csv`, `marsden/*.xlsx`, `erc_he_sources.txt`.
- `server/scripts/geocoding/*_cache.csv`, which is baked into the image.

**Gaps (by code reading, not yet run):**
1. **Blocking: `data/geolocation.csv`.** CSRankings no longer publishes it (paths.go says so). `populatePostgresFromCSVs` reads the `data/` copy first and **returns an error if it is missing** (db.go:213–222). The `backup/` copy is only merged afterwards. **The pipeline stops at step 5.** Fix: fall back to the backup copy when the data copy is missing. **15 min.**
2. **KAKEN master XMLs.** `kaken.py` exits when `data/kaken/review_section_master_kakenhi.xml` is missing. `institution_master_kakenhi.xml` is optional, but without it institutions stay in Japanese. Nothing downloads either file. The source then "fails" every run, and the scheduler reruns the pipeline daily. Fix: download them from bitbucket.org/niijp/grants_masterxml_kaken (raw URL UNVERIFIED) or commit them to `backup/kaken/`. **30 min.**
3. **IPEDS in dev.** `SKIP_IPEDS=1` (nces.ed.gov is unreachable here) plus an empty `data/` means no Carnegie codes. **The US R1 rows then vanish from `universities.csv`, and with them ~51k of the 56k OpenAlex researchers**, plus tuition. Fix: test on a network that reaches NCES, or seed `data/ipeds_*` (about 340 MB). **Decision only.**
4. **Prod compose has no `fetcher` service and no `FETCHER_URL`.** A fresh prod server fetches only CSRankings, NSF and IPEDS. **30 min.**
5. **Scheduler blind spot.** `pipelineDue` reacts only to `partial`, `failed` or `interrupted`. A source still `running` when the 6 h `FETCH_WAIT_HOURS` runs out (NIH, KAKEN and RGC allow 12 h) finishes `ok` later, but nothing reloads it for 7 days. Fix: also treat "a source finished after the last pipeline run" as due. **30 min.**
6. **Secrets.** `OPENALEX_API_KEY` and `CINII_APP_ID` (in `server/.env`) are required. Document this.
7. **Minor:**
   - `NSFAwardsEndYear = 2025` is hard-coded, so FY2026 awards are missing.
   - `server/scripts/geocoding/.env.local` is committed and names `MAPBOX_TOKEN`/`POSTGRES_PASSWORD`. I did not read the values; check that they are not real.
   - `openalex_awards.py` is still untracked in git.
8. **OpenAlex cost.** From empty, the pod needs about 16k field calls for the current list plus about 6k for works, roughly 4 days on the shared key.

### How to run it without touching the live stack
- **Why the live compose can't be reused.** The dev compose hard-codes `container_name` (`pg17-local`, `go-server`, `fetcher`, …), host ports (5432, 8080, 3000, 6333) and `./data`. The Qdrant collection name `explorer_work` is hard-coded too. Running a second copy with only `-p` changed would collide or overwrite.
- **Setup:** write a standalone `docker-compose.fresh.yaml`, run as `docker compose -p atlas-fresh -f docker-compose.fresh.yaml up`. It defines `postgres`, `qdrant`, `embedder`, `fetcher` and `go-server`:
  - no `container_name`, and its own named volumes;
  - only go-server published, on 18080;
  - `./fresh/data:/app/data`, plus `./backup:/app/backup:ro` (read-only also proves nothing writes there) and `./fresh/target`;
  - `POSTGRES_HOST=postgres`, `POSTGRES_DB_NAME=atlas_fresh`, `QDRANT_HOST`/`QDRANT_REST_URL` pointing at its own qdrant, `FETCHER_URL=http://fetcher:8090`, `FETCH_WAIT_HOURS=14`;
  - reuse the already-built images (`--pull never`, no rebuild).
- **`server/.env` caveat.** It is still mounted for the keys. godotenv does not override variables already set, but check that `.env` holds no DB host or name that the compose file doesn't set (UNVERIFIED).
- **OpenAlex.** To avoid spending the live allowance, seed only the call caches: `cp -al data/openalex/fields data/openalex/works fresh/data/openalex/`. Those files are only ever created, never rewritten, so hard links are safe. **Don't link the top-level CSVs**: fields.py rewrites them in place. Everything else starts empty.
- **Time and space.** About 25 GB of disk. The first pass should take ~14–20 h: NSF 2.3 GB, DBLP 1 GB, OpenAlex awards 4.3 GB, NIH/KAKEN/RGC up to 12 h, then hours of embedding. A second scheduler pass follows about 1 day later.
- **Checks at the end:**
  - every `pipeline_status` step is `completed`;
  - every `fresh/data/fetch_state/*.json` is `ok`;
  - row counts equal or come close to live: `professors`, `explorer_faculty` by country, `explorer_universities` by country, funder grants and people by funder, `explorer_work_docs`, scholarships, Qdrant points;
  - a diff of `SELECT funder, count(*)` between the two databases;
  - spot-check 3 universities in the UI on :18080.
- **Next step:** fix gaps 1, 2 and 5 first, since the test would just rediscover them, then run. **Effort: 1.5 h of fixes, 1 h for the compose file, ~1–2 days of wall clock.**

## Threads
- opened → T-a · DFG reply: does `/backend/project/export` count as permitted bulk access?
- opened → T-b · Matching Hangul PI names (NRF) and Chinese-script names (NSFC) to romanised authors
- opened → T-c · Labelling researchers whose last known institution is stale (moved recently)
