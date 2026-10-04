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
   - [ ] 8 pre-existing failures in `utils_test.go` expect `&`→`and` from the display normalizer

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
- [ ] Recent papers: DBLP dump (`data/dblp/dblp.xml.gz`, 1.1 GB) — download in progress; then
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
- [x] Explicit search (Enter / Search button); results view with Faculty, NSF grants (active by default,
      collaborative awards merged) and Universities tabs; map fits to matching universities (`/explorer/grants`)
- [ ] Publishing: not deployed anywhere public yet
- [ ] Europe: see "European funding data" below

## Also found

- [ ] ~9 of 17 API routes query tables/columns that don't exist (`nsf_awards`, `professors.area`)
- [ ] Country codes disagree: Germany is `gr` in one step, `de` in another; unknown countries default to `us`
- [ ] Homepage view prefixes `https://` onto `http://` URLs
- [ ] Frontend checks `"in-progress"` vs constant `"in_progress"`
- [ ] Popups build HTML from raw strings (XSS)
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
- [ ] Generic funder model (grants + named investigators + link to faculty), then importers in order:
      ANR (France), UKRI GtR (UK), ARC (Australia), CORDIS ERC PIs (EU), SNSF (Switzerland)
- [ ] Needs the user: RGC Hong Kong reuse permission; CiNii app ID (KAKEN Japan); Marsden (NZ) manual download
- [ ] US STEM + medicine: NIH RePORTER, OpenAlex (key from the user), ~45 field areas
- [ ] DAAD database JSON (71 programmes for Pakistan) as a scholarship feed
- [ ] Skip: China NSFC, Singapore, Italy PRIN (blocked PDFs), DFG GEPRIS (disallowed), Korea NTIS (key needs Korean affiliation)
