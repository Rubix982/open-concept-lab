# TODO

Audit of the populated database on 2026-10-04 (pipeline steps 1–13, NSF 2025 only).
Numbers in brackets are what the audit measured; re-measure after each item.

## In order

1. **Separate universities from businesses and other organizations**
   [5,604 rows in `universities`; ~3,100 are companies from SBIR/STTR awards, `Inc`, `Llc`]
   - [x] `universities.institution_type`: `university` / `university_affiliate` / `business` / `organization`
   - [x] Pipeline step 14 "Classify Institutions" (`server/classify.go`), before dedup
         → university 2,515 · business 2,251 · organization 760 · university_affiliate 78
   - [x] Map view shows only `university` rows instead of matching `%university%` in the name
   - [x] Steps "Copy Labs" / "Copy Organizations" removed: they moved every `Inc`/`Llc` row out of
         `universities` (orphaning its awards) and filed Carnegie Institution / Mass General under CMU / MIT.
         `labs` and `organizations` tables are now unused; `institution_type` replaces them
   - [x] Individuals awarded directly ("Rosales, Detbra") are `individual` (51); a bare "Institute" no longer
         makes a university (Santa Fe, Broad → `organization`); degree-granting US institutes are promoted by IPEDS

2. **Merge duplicate universities**
   [386 groups differing only in case/punctuation; step 15 fails on an FK violation:
   renames Berkeley awards to `University of California, Berkeley`, which normalization never produces]
   - [x] One matching rule: SQL `institution_key()` (migrations/8). Display normalization stays at ingest
   - [x] `institution_aliases` table; curated pairs live in `backup/institution_aliases.csv` (70 rows);
         edit it, then `make pipeline-from STEP=15` (no rebuild — `backup/` is mounted)
   - [x] Affiliates / departments fold into their parent via `institution_parent_name()` (84 merges, reviewed)
   - [x] Step 15 "Merge Duplicate Institutions" (`server/merge.go`) replaces ~980 lines of dedup/labs/orgs code
   - [x] Pipeline completes all 15 steps → universities 5,604 → 4,906; 0 orphaned awards;
         awards at a CSRankings university 4,443 → 5,362 of 6,860 (184 universities)
   - [x] Texas A&M normalizer bug fixed (every campus collapsed into `Texas A&M`)
   - [x] Clean full reload from empty tables: all 15 steps pass in 3m49s; Texas A&M campuses separate
   - [x] `Georgia Tech Research Corporation` (96 awards) → Georgia Institute of Technology
   - [x] `utils_test.go` passes: tests match the display normaliser (keeps `&` and ` - `); a lone "Univ" now expands

3. **Link professors to NSF awards**
   [only 498 of 18,885 CSRankings faculty (2.6%) linked; exact-name match only, any institution]
   - [x] NSF investigators stored apart from `professors` (`nsf_investigators`, keyed by NSF person id,
         with structured first/last name; per-award email on `award_pi_rel`)
   - [x] Step 16 "Link NSF Investigators To Professors" (`server/link.go`): first + last name, plus evidence —
         an award at the professor's university, or email domain = homepage / university domain.
         Initial-only names need both. Linked per NSF id, so awards from earlier universities follow
   - [x] CSRankings name variants of one person ("Dawn Song" / "Dawn Xiaodong Song") grouped by scholar id / homepage
   - [x] → 916 faculty linked on 2025 data (848 with CSRankings publication data); samples reviewed, all correct
   - [x] Moved professors: step "Link NSF Investigators By DBLP Affiliation" links an unlinked investigator when
         full name matches and an award institution is in the professor's DBLP current/former affiliations (104).
         Remaining same-name pairs have no evidence and are left unlinked on purpose (different people)
   - [x] Name variants: `professor_variants` groups CSRankings spellings (shared Scholar id, or homepage + same
         first and last name); explorer shows one person (31,500 names → 25,722 people), grants and papers of all
         spellings count
   - [x] `Ronald J. Brachman` is kept (3 spellings, one explorer entry)

4. **Load older NSF years**
   [2010–2025 on disk, 2.3 GB; config loaded 2025 only (`NSFAwardsStartYear`)]
   - [x] `NSFAwardsStartYear = 2010` → 192,089 awards (2008–2026 effective dates), 0 orphaned;
         full reload 7m55s (NSF load 4m). Indexes on `award.institution` etc. (migrations/10)
   - [x] Linkage: **4,961 of 6,882 US CSRankings faculty (72%)** have NSF awards (5,742 people overall);
         75% of awards are at a CSRankings university
   - [x] Remaining unlinked NSF universities are not in CSRankings (Alaska Fairbanks, UNC Charlotte, …): no faculty
         to link, by design
   - [x] CUNY: senior colleges and the Graduate Center alias to CSRankings' single `CUNY`; community colleges stay separate
   - [x] Small aliases: CU Denver downtown → University of Colorado - Denver; CSUN's corporation → CSUN
         (SIU Carbondale was already merged)

5. **Use IPEDS records**
   [2023 parquet cache in `data/ipeds_cache/2023/`; ingest expected CSVs; nces.ed.gov unreachable]
   - [x] `server/scripts/ipeds/parquet_to_csv.py` (own venv) → `data/ipeds_data/2023/<dataset>/`;
         `SKIP_IPEDS=1` now skips only the download, cached data is always ingested
   - [x] All 14 `ipeds_*` tables load (institutions first; `.` = NULL; salary and Pell loaders rewritten for
         the current wide layout). Carnegie from `C21BASIC` (15 = R1, 16 = R2)
   - [x] Step 15 "Link IPEDS Institutions" (`server/ipeds_link.go`) → `universities.ipeds_unitid`: name + city/ZIP,
         unique name, or domain + place. Linked rows become `university`, take IPEDS website / coordinates
   - [x] Two rows matched to one IPEDS institution by full name + place are merged
         (Caltech, Ucla, OHSU, NJIT, UNC Charlotte, …)
   - [x] → 179 of 198 US CSRankings universities and 136 of 146 R1s linked; no wrong merges
         (UNLV / UNR, Wichita State / WSU Tech stay separate)
   - [x] Campus-suffix collisions closed by `backup/ipeds_links.csv` (Pitt, UW, UNM, …; + IUPUI, LIU Post): every US
         CSRankings university is linked to IPEDS
   - [x] IPEDS-linked rows take IPEDS's address and coordinates (University of Nevada: Reno 89557)
   - [x] CSRankings' `country-info.csv` sets the country of its own institutions (Babeș-Bolyai was US via geocoding)
   - [x] IPEDS fields in the university drawer (R1/R2, graduate tuition and enrollment)

## Student explorer (v1, "Advisor Atlas")
Flow: pick research areas → universities and faculty → their recent work, ranked by the student's goal
→ funding. Backend: steps 18–19 + `server/explorer_api.go` (`/explorer/*`, all < 100 ms).
Frontend: `web/src` rewritten (area picker, map, results, university drawer, professor view).
- [x] Map loads in ~2 s (was 15.7 s); popup showed no faculty (fixed: university drawer lists them)
- [x] 27 CSRankings areas served from `research_area_venues` (single copy of the taxonomy)
- [x] Goal matching: Postgres full-text over each professor's NSF grants and recent papers; best single
      match, decayed by age (halves ~every 5.5 years)
- [x] Funding: active NSF grants per professor and per university, graduate tuition (in-state / out-of-state),
      GRFP note with eligibility
- [x] Curated IPEDS links (`backup/ipeds_links.csv`): UW, Pitt, Penn State, Ohio State, … now show R1 / tuition
- [x] Fixed: IPEDS graduate tuition columns were shifted (out-of-state showed in-state)
- [x] Phone layout; shareable URLs (`?areas=ml,nlp&q=…&u=…&p=…`); old offline service worker removed
- [x] Recent papers: DBLP dump (`data/dblp/dblp.xml.gz`, 1.1 GB) loaded; then
      `make pipeline-from STEP=18`. The DBLP API is rate-limited and bot-guarded, so no live calls
- [x] Semantic goal matching (`server/semantic.go`): grants and papers embedded with all-MiniLM-L6-v2
      (embedder service) into Qdrant `explorer_work`, filtered by area/university; step 20 is incremental.
      Cosine ≥ 0.35 counts as a match; recency half-life 5.5 y; event grants (conference/workshop) × 0.6.
      Falls back to keyword matching if the embedder or Qdrant is down. ~150 ms per search
- [x] Map waits for all data (loading state, retry on error); old offline service worker replaced by a
      self-removing `sw.js` (browsers that cached the old app get the new one)
- [x] Explicit search (Enter / Search button); results view with Faculty, Grants (active by default,
      collaborative awards merged) and Universities tabs; map fits to matching universities (`/explorer/grants`)

## Also found

- [x] Legacy API routes (10 of 15 failing, none used by the frontend) removed with `routes.go`; the app uses `/explorer/*`
- [x] Country codes come from the `countries` table (NSF step and the step-10 fill-in); unknown countries stay empty instead of `us` (server and frontend)
- [x] Data links go through `webUrl()`: http(s) only (no `javascript:`), bare domains get https://
- [x] `in-progress` / `in_progress` mismatch was in the old frontend, deleted in the rewrite
- [x] Map popups are built with textContent (old raw-HTML popups were in the deleted frontend)
- [x] Map coordinates: 64 universities were in the wrong place (UCLA in Ann Arbor, RWTH Aachen near St. Louis)
      because geocoding matched town names. Explorer now prefers `backup/university_coordinates.csv`
      (`server/scripts/geo/check_coordinates.py`: OpenStreetMap, then Wikidata), then IPEDS, then geocoding
- [x] Search index: area order made 90k payloads look changed; areas now ordered deterministically, change
      checks compare content, lost points are re-embedded. Qdrant 1.3 (4 GB) runs out of memory on large
      payload rewrites and scrolls, so these are paged small
- [x] Qdrant upgraded to 1.12.6 on a new volume `qdrant_data_v112` (1.3.0 ran out of memory on bulk updates;
      the old volume stays for rollback). Full re-embed: 646,857 items
- [x] The old scraper's semantic search (no API route) is superseded by the explorer's goal search

## Done

- [x] IPEDS download failures no longer stop the pipeline; `SKIP_IPEDS` switch
- [x] IPEDS step no longer closes the shared DB pool (broke every later step)
- [x] Per-step checkpoints: `make pipeline` resumes, `make pipeline-from STEP=N` reruns from N

## Funding beyond the US
Research reports: `docs/data-sources/` (europe.md, oceania.md, east-asia.md, us-stem-and-medicine.md).
- [x] Curated scholarships (`backup/scholarships.csv`, 29 programmes, official links), served by destination and
      nationality (`/explorer/scholarships`); "Applying from" in the filter bar; drawer section per university
- [x] NSF wording only for US universities; non-US faculty no longer show "no NSF grants"
- [x] Generic funder model: `funder_grants` + `funder_grant_people` (migration 13), common CSV from
      `server/scripts/grants/*.py`, steps 18 (Load Funder Grants) and 19 (Link Funder Grants: name + institution,
      initial-only names need a CS field or an uncommon surname). UI names the funder and its currency.
- [x] ARC (Australia, FoR 46 + 08): 2,077 grants → 328 faculty (147 with an active grant)
- [x] Marsden (NZ, manual xlsx in `data/marsden/`): 1,313 grants → 41 faculty
- [x] SNSF (Switzerland, FoR 46 / IT disciplines): 1,518 grants → 135 faculty (123 of 163 Swiss faculty funded)
- [x] ANR (France, CE23/25/33/39/46/48 or PE6 labs): 1,795 grants → 124 faculty. Investigators are listed by
      lab; the RNSR register maps each lab to its parent institutions, joined with " | " for the linker
- [x] ERC (Horizon 2020 PIs, CORDIS): 2,029 computing grants → 239 faculty across Europe and Israel.
      Legal host names mapped to CSRankings names in `erc.py`. Horizon Europe ERC PIs are PDF-only (not loaded)
- [x] UKRI GtR (EPSRC research grants + fellowships in computing, ending 2015+): 2,593 grants → 718 faculty
      (481 of 1,160 UK faculty now have grant data)
- [x] Linker: compares unaccented institution names (`institution_key` drops accented letters) and accepts
      several " | "-separated institutions per investigator
- [x] Funder coverage per country comes from the loaded grants (`/explorer/funders`), not a static list
- [x] KAKEN (Japan): 16,268 Informatics projects (2015+), English names and institutions (KAKEN institution
      master); throttled, cached, facts only, attribution "based on KAKEN (NII)" (`scripts/grants/kaken.py`)
- [x] RGC Hong Kong (user approved 2026-10-05): 914 computing projects (GRF, ECS; 2015–2026), facts only, no
      abstracts, 1 request/s, cached (`scripts/grants/rgc.py`) → 204 faculty; 66% of Hong Kong CS faculty have grant data
- [x] CSRankings refreshed each run from gh-pages (34,655 rows, ORCIDs); `institutions.csv` replaces
      country-info (written as country-info.csv); professors / professor_areas are replaced, not upserted
- [x] `institution_key()` transliterates accents (migration 16)
- [x] DAAD scholarship feed: 69 graduate/doctoral programmes open to Pakistani applicants
      (`scripts/scholarships/daad.py` → data/scholarships/daad.csv); curated entries win on duplicates

## State (2026-10-05, morning)
- Pipeline 26 steps, all succeeded; semantic index stable (a rerun embeds nothing).
- 48,077 people at 676 universities in 61 countries: 18,015 CS faculty (CSRankings) + 30,062 researchers in
  14 other fields at US R1s (OpenAlex). 18,647 with grant records, 8,297 active.
- Funders: NSF, NIH, UKRI, KAKEN, ARC, ERC (H2020 + Horizon Europe), SNSF, ANR, Marsden.
- 646,857 searchable items (76,472 grants, 570,385 papers; 290,485 papers with abstracts). Qdrant 1.12.6: 537 MB.
- Known data caveat: OpenAlex affiliations are sometimes stale (a researcher can show at a previous university).

## Subfields: finish tomorrow (2026-10-06, after the OpenAlex allowance resets)
- [ ] `fields.py works` for the ~65 groups of new researchers still without papers (saved groups,
      resumes on cache), then pipeline from step 22
- [x] 11 more fields and ~210 subfields as research areas (70,290 people, 234 areas)

## Next: grant data for many more countries (asked 2026-10-05, to plan)
- [ ] Survey national funders with open, reusable award data per country (by students affected),
      check each licence, then add importers to the fetcher one by one

## Next: the pipeline fetches everything (agreed 2026-10-05, after subfields)
Today only CSRankings, NSF and IPEDS are fetched by the pipeline; everything else is fetched by hand
and only loaded. On a fresh pod those steps skip or fail. Goal: the pipeline fetches, extracts and
loads every source it serves, and heals itself.
- [x] Separate fetcher container (Python, the existing scripts); the pipeline runs one fetch step per
      source before the load steps
- [x] Sources to move in: the 11 grant importers (scripts/grants, incl. ERC Horizon Europe PDFs listed
      in data/erc_he/sources.txt), DBLP dump, OpenAlex works.py / fields.py / extra_universities.py
      (and the universities.csv export it needs, done from the database inside the step), DAAD
      scholarships, geocoding caches, coordinate checks
- [x] Each fetch: skip when fresh (age threshold per source), resume from its cache, retry next run
      on failure; never replace good data with a partial result
- [x] Limits inside the pipeline: OpenAlex 10k calls/day (a fetch can span days: finish later, don't
      fail), NIH / RGC / KAKEN ~1 request/s; API keys from the server environment only
- [x] Serving keeps the last good data while a fetch runs; a scheduler reruns the pipeline when data is
      older than PIPELINE_REFRESH_DAYS or a fetch was left partial
- [ ] Prove it: a fresh pod with an empty data/ ends up complete (not yet tried end to end)
- [ ] Geocoding and the Pakistani-universities list stay curated inputs (committed), not fetched

## Parked after v1 (2026-10-04)
- [x] v1 finish: UKRI loaded, go-server + web deployed, screenshots checked (US, UK, CH, AU)
- [x] Shared links (?u=...) open the map on that university instead of the US
- [ ] Share with 5–10 students and collect feedback (did it help them find someone to email? was the
      funding section useful?) before adding more data sources
- [ ] Public deploy: planned for the week of 2026-10-12; ask the user first (hosting, domain, KAKEN/RGC terms if loaded)
- [x] OpenAlex abstracts: 261,250 of 291,106 DOIs found, 223,804 with abstracts (5,822 calls, free allowance);
      paper texts embed title + abstract (re-embedded only where the text changed)
- [x] Horizon Europe ERC PIs: 15 result PDFs (2021–2025 StG/CoG/AdG, `data/erc_he/sources.txt`), PE6 rows
      joined with CORDIS Horizon Europe projects by call + acronym (209 grants). UK-hosted 2021–2023 winners
      were funded by UKRI's guarantee and come through UKRI
- [x] Fields beyond computing, first cut: 14 OpenAlex fields (Sciences / Engineering / Medicine groups) at 140 US R1
      universities; the 20 most-cited researchers per university and field who look like faculty (main
      institution, 30–1,500 works, h-index ≥ 15, publishing recently) → 30,062 researchers, 10 recent papers each.
      Labelled "Researcher (OpenAlex)", not verified faculty (`scripts/openalex/fields.py`, migration 17)
- [x] NIH RePORTER: 77,190 projects active in FY2025–26 → 3,488 people (`scripts/grants/nih.py`)
- [ ] Researchers outside CS beyond US R1 and Pakistani universities (more fields: done, 25 fields)
      (Pakistan done: 25 universities via backup/extra_universities.csv; other countries and fields open)
- [x] Professor's papers ordered by the student's goal (semantic, keyword fallback); matches marked

## Decisions
- 2026-10-05: Israeli universities stay in the app (map, search, counts); the shareable overview page doesn't name Israel

## Known limitations (not tasks)
- Postgres 18.2: `left()`/`substr()` on TOASTed text can split a UTF-8 character; worked around with `|| ''`
  (detoast first) in semantic.go and explorer_api.go. Remove once Postgres fixes it
- Non-US universities have no tuition / R1 data (IPEDS is US-only)
- France is thin in CSRankings itself (no Sorbonne / Paris-Saclay entries), so ANR links stay limited
- Germany has no national grant data (DFG GEPRIS disallows collection); ERC is the only signal there
- Funders not loaded, by decision: China NSFC, Singapore, Italy PRIN (blocked PDFs), DFG GEPRIS (disallows
  collection), Korea NTIS (key needs a Korean affiliation)
- Same-name NSF investigators with no institution, email or DBLP-affiliation evidence stay unlinked on purpose

## Milestone 3: show what we have (UI audit, 2026-10-05)

Walked the UI across 12 countries (US, UK, DE, FR, CN, JP, KR, IN, SG, BR, AE, PK) and compared the database with
what the API returns and the pages render. The data is far richer than the pages.

### A. Wrong or misleading on screen (fix first)
- [x] Same-name people at two universities are merged: CSRankings lists "Yang Zhang" at UNC and at NUS; the NUS
      row shows the UNC person's NSF grant. Key people by name + affiliation when names collide
      (Not a merge: that Yang Zhang moved from Michigan to NUS. Grants now say "Held at <institution>" when it
      differs from the current university)
- [x] ORCID placeholder `0000-0000-0000-0000` on 15,526 CSRankings rows: treat as missing
- [x] HTML entities in grant titles (`&quot;`): 58 funder grants, 10 NSF awards. Unescape at load
- [x] Per-person funding sums whole grant amounts (Bronstein: £8.6M programme grant). Show role (PI / co-investigator)
      and the grant's amount, not a personal total
- [x] Map tooltip and university list say "0 with an active research grant" in countries with no grant data
      (China, Singapore, Korea, …). Say "no grant data for <country>" instead
- [x] Scholarship copy: "Covers see official page." / "Application window: see official page." Hide empty fields
- [x] Scholarship order: the generic HEC programme leads every country; show programmes for that country first

### B. Data we have but don't show
- [x] Faculty rows are name + area tags only. Add their newest (or goal-matched) paper title and the funding line
- [x] Paper abstracts (95–98% of CS faculty papers): expandable preview on the profile
- [x] OpenAlex per paper: topic (256,885 papers) and citation count; topic tags on the profile ("working on now")
- [x] Collaborators: 67,706 co-author pairs inside the dataset (26,100 people). "Works with" on the profile, linked
- [x] Former affiliations from DBLP (3,136 people): "previously at …"
- [x] Grant co-investigators and roles (funder_grant_people): show who else is on each grant
- [x] University panel: area strengths (`area_faculty`, already in the API, not rendered); grants by funder; PhD
      degrees awarded per year (IPEDS completions, US); list of faculty with grants started in the last 12 months
- [x] Early-career faculty (4,122 CS faculty whose first top-venue paper is 2019+): usually building labs and
      recruiting. Badge + filter (badge and profile line done; the filter is in C)
- [x] "Researchers with similar work": nearest people in the semantic index, from a profile
- [x] OpenAlex researchers: abstracts are in the cached works responses but were not saved (1% have abstracts);
      34% have no papers (50 authors per call capped at 200 works). Save abstracts; page per author group.
      Link their OpenAlex and ORCID pages (no homepage or Scholar link today)
      (done: 429,168 author-paper rows, 74% with abstracts; 83% of researchers have papers)
- [x] Found on the way: IPEDS "PhD degrees" counted program rows, not degrees (Georgia Tech 38 → 556). Now sums
      CTOTALT from the all-programs rows, research doctorates only

### Unattended run, 2026-10-05 (work order; each step committed and pushed on its own)
1. [x] Finish B: load the OpenAlex researcher abstracts when `fields.py works` ends; pipeline from step 13; verify
2. [x] C1 filters + sort on search results and university lists (+ 17 misplaced universities fixed)
3. [x] C3 "Before you write" checklist on a profile
4. [x] Funding landscape (asked 2026-10-05): ~90% of active grant money (NIH 64,515 active grants, KAKEN,
   ANR, ERC, …) isn't linked to anyone on the map, and the Grants tab only searches linked grants. For a search:
   money by funder, grants started per year, universities receiving it, the grants with PI and institution
4b. [x] Second visibility audit (design note below; building G1–G6, G7 waits for Saif) (asked 2026-10-05): data we hold but don't surface, and calm exploration:
   browse without a search, progressive disclosure, no walls of numbers. Write up as a design note with
   action items; build the clearly safe ones
5. [x] C4 scholarships: level filter and deadline view (open now / opens in, read from the window text)
6. [x] C2 shortlist and compare (browser storage only): "Save to your list" on profiles and universities, "Your list" compares people
7. [x] C5 Pakistan path: 25 universities from OpenAlex (researchers in 15 fields incl. CS), HEC
   Indigenous PhD Fellowship
8. [x] D1 NSERC (Canada, Open Government Licence): 4,029 computing grants FY2022–2024
   [x] D2 NWO (Netherlands, CC0, NWOpen API): all projects since 2016. SweCRIS left out: no published
   reuse terms found (revisit if the Swedish Research Council publishes a licence)
9. Loose ends: [x] MIT, Caltech, RIT, AFIT linked to IPEDS; [x] semantic index in RAM (int8 quantization): cold "similar" 3.6 s -> 0.1–0.6 s
Rules: no accounts, payments, public deploys or merges to main; free data and allowances only.

### Design note: calm exploration (second visibility audit, 2026-10-05)
The data answers more questions than the screens ask. The aim is to show more of it without
walls of numbers.

Principles
- One question per view: the map says where, Faculty says who, Funding says where the money goes, a
  profile says whether to write. A view that tries to answer two questions answers neither.
- A sentence first, numbers second. Lists open at 5–8 rows; the rest is one click away.
- Signals, not statistics: turn a table into one short tag a student acts on ("new lab, funded",
  "funded PhD programme"). A tag is earned only when it changes what the student does next.
- Browsing must work without knowing the right words: example searches and topics to start from.
- Say plainly what's missing (no grant data for a country, NIH running projects only) where it matters,
  once, not on every row.
- Leave out what doesn't help a PhD applicant, on purpose: IPEDS undergraduate admissions, graduation
  rates, faculty salaries, libraries and finances are loaded but stay off the screen.

What we hold and don't show (by value to a student)
- [x] G1 Hiring signals from grant schemes: a new PI with money. NSF CAREER (12,310 via programme reference 1045; 3,320 running), ERC
      Starting (794), ARC DECRA (194), NIH K99/R00 (2,419), KAKEN early-career (3,071). Tag on faculty
      rows and profiles; "Starting a lab" filter
- [x] G2 Funded PhD programmes: NIH T32 training grants (1,821), NSF Research Traineeships (400, 96
      running). These pay PhD students directly. "Funded PhD programmes here" on the university panel
- [x] G3 NSF programme names (248k rows: "Robust Intelligence", "Secure & Trustworthy Cyberspace"):
      "Programmes that fund this" in the Funding tab, the program on each NSF grant
- [x] G4 Funding on the map: in the Funding tab, size dots by running grants on the search, not faculty
- [x] G5 Starting points without a search: a few example searches under the intro; topic chips
- [x] G6 Country summary when a country is chosen: one paragraph (universities, people, which funders
      are covered, scholarships)
- [x] G7 (Saif: yes, 2026-10-05) Grants and Funding tabs overlap: Funding lists every grant, Grants only
      those linked to people. Recommend folding Grants into Funding: three tabs instead of four
- Deferred: research-area trends per university over time (professor_areas by year): noisy at small
  counts, easy to over-read

### C. Student use cases not served yet
- [x] Filters: country / region, "has an active grant", early-career, R1; sort by recent activity or funding
- [x] Shortlist and compare (kept in the browser): save professors and universities, compare side by side
- [x] "Before you write" checklist on a profile: their newest relevant paper, active grants, overlap with your goal
      (no email sending)
- [x] Scholarships: filter by level (master's / PhD), deadlines view
- [x] Pakistan: LUMS and other Pakistani faculty are in the data; a "study in Pakistan first" path (MS + HEC)

### D. Coverage gaps worth closing (by students affected)
- [x] Canada: 791 CS faculty, 3% with grant data (now 73%, NSERC). NSERC awards are open data (open.canada.ca)
- [x] Sweden (SweCRIS API, open), Netherlands (NWO project database): check terms (NWO loaded, CC0; SweCRIS: no published terms)
- [ ] China, Korea, India, Singapore, Brazil, Taiwan: no usable national grant data (see Known limitations)

