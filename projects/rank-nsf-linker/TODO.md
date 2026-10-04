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
   - [ ] Known gaps: individuals as awardees (`Fu, Beverly`) land in `organization`;
         research institutes (`Broad Institute`) and `University Corporation For Atmospheric Res` count as
         `university` — IPEDS (item 5) can confirm US rows

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
   - [ ] 47 exact-name pairs stay unlinked: ~half are different people (two Eric Larsons), ~half moved
         universities after CSRankings recorded them (Jiayu Zhou MSU → UMich) — nothing confirms them
   - [ ] CSRankings name variants inflate counts: `professors` has 31,500 rows for 25,283 people
   - [ ] Old dedup deleted `Ronald J. Brachman`; he is now kept (and his variants group by homepage)

4. **Load older NSF years**
   [2010–2025 on disk, 2.3 GB; config loaded 2025 only (`NSFAwardsStartYear`)]
   - [x] `NSFAwardsStartYear = 2010` → 192,089 awards (2008–2026 effective dates), 0 orphaned;
         full reload 7m55s (NSF load 4m). Indexes on `award.institution` etc. (migrations/10)
   - [x] Linkage: **4,961 of 6,882 US CSRankings faculty (72%)** have NSF awards (5,742 people overall);
         75% of awards are at a CSRankings university
   - [ ] Remaining unlinked NSF universities are mostly not in CSRankings (Alaska Fairbanks, UNC Charlotte,
         San Diego State, Howard, Villanova) — nothing to link to
   - [ ] Decide: CSRankings has one `CUNY`; NSF has `Cuny City College`, `Cuny Queens College`, … Aliasing them
         links faculty but collapses campuses into one map dot
   - [ ] Small aliases left: `University Of Colorado At Denver-Downtown Campus`, `Southern Illinois University
         At Carbondale`, `The University Corporation Northridge` (CSUN)

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
   - [ ] Campus-suffix names collide across campuses (Pitt-Pittsburgh vs Pitt-Johnstown → both
         "University of Pittsburgh"), so Pitt, UNM, UNH, Kent State, Indiana stay unlinked — a small curated
         IPEDS map (university → UNITID) would close the gap
   - [ ] Some rows carry another campus's address (`University of Nevada` has a Las Vegas ZIP)
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
- [ ] Postgres 18.2: `left()`/`substr()` on TOASTed text can split a UTF-8 character; worked around with
      `|| ''` (detoast first) in semantic.go and explorer_api.go
- [ ] Non-US universities have no tuition / R1 data (IPEDS is US-only)
- [x] Explicit search (Enter / Search button); results view with Faculty, Grants (active by default,
      collaborative awards merged) and Universities tabs; map fits to matching universities (`/explorer/grants`)
- [ ] Publishing: not deployed anywhere public yet
- [ ] Europe: see "European funding data" below

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
- [ ] Qdrant 1.3.0 is old and fragile under bulk updates; consider upgrading (needs a re-embed)
- [ ] Semantic search (scraper → Qdrant) has no API route

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
- [ ] KAKEN (Japan, throttled, non-profit terms, attribution), RGC Hong Kong (facts only)
- [ ] Our CSRankings copy (Aug 2025, 31,500 rows) is behind upstream (per-letter `csrankings-[a-z].csv`,
      32,444 rows); step 1 should download the split files
- [ ] France is thin in CSRankings itself (no Sorbonne / Paris-Saclay entries), so ANR links stay limited
- [ ] `institution_key()` drops accented letters ("École" → "cole"); fixing it changes keys used by the
      merge steps, so it needs a full re-run from step 14
- [ ] US STEM + medicine: NIH RePORTER, OpenAlex (key from the user), ~45 field areas
- [ ] DAAD database JSON (71 programmes for Pakistan) as a scholarship feed
- [ ] Skip: China NSFC, Singapore, Italy PRIN (blocked PDFs), DFG GEPRIS (disallowed), Korea NTIS (key needs Korean affiliation)

## v1 state (2026-10-04, night)
- Deployed locally: pipeline 23 steps, all succeeded. 15,667 faculty at 635 universities in 58 countries;
  7 funders (NSF, ARC, Marsden, UKRI, ANR, SNSF, ERC); 536,907 DBLP papers; 416,312 items in semantic search.
- OpenAlex step is in the pipeline but skips until `server/scripts/openalex/works.py` has run (no calls made).
- Postgres `shm_size: 1gb`; go-server image has curl for its healthcheck.

## Parked after v1 (2026-10-04)
- [x] v1 finish: UKRI loaded, go-server + web deployed, screenshots checked (US, UK, CH, AU)
- [x] Shared links (?u=...) open the map on that university instead of the US
- [ ] Share with 5–10 students and collect feedback (did it help them find someone to email? was the
      funding section useful?) before adding more data sources
- [ ] Public deploy: ask the user first (hosting, domain, KAKEN/RGC terms if those are loaded)
- [ ] OpenAlex v2: run `server/scripts/openalex/works.py`, deploy steps 21–23, re-embed papers with abstracts
- [ ] Germany: no national funder data (DFG GEPRIS disallows crawling); ERC is the only signal there
- [ ] Horizon Europe ERC PIs (PDF-only per call; panel PE6 = computer science)
- [ ] Fields beyond computing (science, engineering, medicine) via OpenAlex + NIH RePORTER
- [ ] Semantic search for the paper list on the professor page (currently recency order)

