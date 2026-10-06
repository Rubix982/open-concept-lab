# Funder survey for Advisor Atlas (2026-10-06)

## Headline finding

**OpenAlex `awards` could replace most new per-country loaders, though not all.** I checked this live. OpenAlex holds 17.6M awards. They are free as a CC0 S3 snapshot: `s3://openalex/data/jsonl/awards/` exists, last updated 2026-09-23. The API is metered at about $1/day free per key. OpenAlex now pulls award data directly from about 250 funder sources (field `provenance`), and that list includes most funders below: `gepris`, `nsfc_kd`, `grb_most_projects`, `trdizin_tubitak_projects`, `mur_prin_portal`, `ncn_ranking_lists`, `isf_grant_search`, `hec_pakistan_nrpu`, `swedish_research_council`, `fct`, `anid_github`, `cihr_opendata`, `sshrc_opendata`, `fapesp_bv` and more.

Caveats:
- 7.3M of the 17.6M are `crossref_work_funders` stubs. These have a grant number only, with no title and no PI. Filter by provenance.
- PI is missing completely for some sources (see the table).
- OpenAlex calls itself CC0, but that does not remove any restriction the original source puts on its data.

Recommendation: write one OpenAlex-awards loader. Filter it to the provenance list in the table, deduplicate it against the 12 funders already loaded, and write bespoke loaders only where OpenAlex lacks the PI.

## Summary table

PI% is the share of that source's OpenAlex awards that have a lead investigator, as I measured it today.

| # | Country / funder | Best source | PI | Inst | Amt | Abstract | Licence | Verdict |
|---|---|---|---|---|---|---|---|---|
| 1 | Germany, DFG | GEPRIS (HTML only); OpenAlex `gepris` 144k | **No in OpenAlex** (0%); yes on GEPRIS pages | Y | Y | Y | Not stated | MAYBE |
| 2 | Canada, CIHR / SSHRC | open.canada.ca CSVs; OpenAlex 82k / 114k | Y (~100%) | Y | Y | partial | Open Government Licence – Canada | **LOAD** |
| 3 | China, NSFC | kd.nsfc.gov.cn (no official bulk); OpenAlex `nsfc_kd` 231k | Y (100%, names in Chinese script) | Y (ROR-matched) | Y | ? | Not stated | MAYBE (via OpenAlex) |
| 4 | South Korea, NRF / NTIS | data.go.kr NRF CSV (11.8k rows); NTIS OpenAPI (key) | Y | Y | not listed | N | "이용허락범위 제한 없음" (no restriction on use) | MAYBE |
| 5 | Turkey, TÜBİTAK | TR Dizin projects; OpenAlex 27k | Y (+co-Is) | sparse | N | N | Unverified | MAYBE |
| 6 | Sweden, VR + Vinnova/Formas/Forte | SweCRIS API, swecris-api.vr.se | Y (99%) | Y | Y (SEK) | Y | Unverified | **LOAD** |
| 7 | Italy, PRIN | prin.mur.gov.it; OpenAlex 11k | Y (+co-Is) | Y | Y | N | Unverified | MAYBE |
| 8 | Taiwan, NSTC | GRB catalogue on data.gov.tw/dataset/18707, 1993– | Y | Y | Y | abstract URL | Government Data Open License v1 | **LOAD** |
| 9 | Norway, RCN | GitHub `Forskningsradet/open-data` CSV, 2004– | Y (`prosjektleder`) | Y | Y | N | NLOD 2.0 | **LOAD** |
| 10 | Austria, FWF | FWF Open API (Meilisearch), 1995– | Y | Y | Y | Y | CC0 | **LOAD** |
| 11 | Ireland, SFI / Research Ireland | data.gov.ie CSV, 2000– | Y (Lead Applicant + ORCID) | Y | Y | N | CC BY 4.0 | **LOAD** |
| 12 | Chile, ANID | GitHub `ANID-GITHUB/Historico-de-Proyectos-Adjudicados`, 1982–2025 | Y | Y | Y (CLP thousands) | N (keywords) | CC0 | **LOAD** |
| 13 | Brazil, FAPESP | BV FAPESP CSV, 1992– | Y | Y | ? | Y | Unverified (SP open-data catalogue) | **LOAD** |
| 14 | Brazil, CNPq | CNPq panels (CSV/XLSX export) | Unverified | Y | Y | N | Unverified | MAYBE |
| 15 | Portugal, FCT | PTCRIS sciproj; OpenAlex 104k | Y (92%) | sparse | Y | Y | Unverified | MAYBE |
| 16 | Israel, ISF | isf.org.il grant search; OpenAlex 16k | Y | Y | Y | Y | Unverified | MAYBE |
| 17 | Poland, NCN | projekty.ncn.gov.pl (no API); OpenAlex 24k | Y | Y | Y | N | Unverified | MAYBE |
| 18 | Spain, AEI | BDNS (OpenAlex `bdns_aei` 29k) | **N** | Y | Y | N | — | MAYBE (institution level only) |
| 19 | Czechia, CEP | isvavai.cz export (CSV/XML) + rvvi.cz/api | Unverified (0% in OpenAlex) | Y | Y | Y | Unverified | MAYBE |
| 20 | Finland, RCF | research.fi public API (CSCfi/research-fi-publicapi), 2020– | Y | Y | Y | Y | API use "requires approval" | MAYBE |
| 21 | Denmark, DFF + foundations | forskningsportal.dk export (JSON/XLSX), 2016– | Y | Y | Y | ? | Unverified | MAYBE |
| 22 | Belgium, FWO | FRIS researchportal.be open APIs; OpenAlex 23k | Y | partial | N | Y | Unverified | MAYBE |
| 23 | Belgium, FNRS | nothing found | — | — | — | — | — | NO (unverified) |
| 24 | UK, Wellcome | Wellcome grants file / 360Giving GrantNav; OpenAlex 19.6k | Y (100%) | Y | Y | Y | CC BY 4.0 | **LOAD** |
| 25 | UK, other charities | 360Giving GrantNav bulk | N (individuals anonymised) | Y | Y | partial | Per publisher, mostly CC BY | MAYBE (low value) |
| 26 | EU, Horizon Europe (non-ERC) | CORDIS bulk on data.europa.eu | **N** (organisations only) | Y | Y | Y | EC reuse (CC BY 4.0) | MAYBE |
| 27 | Pakistan, HEC NRPU | nrpuonline.hec.gov.pk (scrape); OpenAlex 1.9k | Y | Y | N | Y | Unverified | MAYBE |
| 28 | India, ANRF/SERB, DST | prism.serbonline.in (portal) | Y on portal | Y | ? | ? | Unverified | MAYBE / scrape |
| 29 | US, DOE/DOD | USAspending API (no key) | **N** | Y | Y | Y | Public domain | NO for advisors |
| 30 | Gates Foundation | bmgf-grants.csv | **N** (grantee org) | Y | Y | purpose | Unverified | NO for advisors |
| 31 | Mexico, CONAHCYT | SNII registry (what OpenAlex ingests) | Y | Y | N | N | — | NO: SNII is a researcher membership list, not grants |
| 32 | Singapore, NRF / A*STAR | data.gov.sg: aggregated totals 2007–2015 | N | N | totals only | N | — | NO |
| 33 | Malaysia, Saudi (KACST), UAE, Qatar (QNRF), South Africa (NRF) | press releases, PDFs, QNL publication search | N | — | — | — | — | NO |

## Notes per funder (only where they matter)

- **DFG.** The relaunched GEPRIS (July 2026) shows researchers together with their institutions. But I found no official API, bulk export or licence. OpenAlex's copy has title, abstract, institution and amount but **no PI**. Getting PIs means scraping about 150k pages. Third-party crawlers exist (GitHub `primeapple/dfg-gepris-crawler`, a Kaggle snapshot). Ask DFG (contact named on the relaunch page) before scraping.
- **NSFC.** The only practical source is OpenAlex's ingest of kd.nsfc.gov.cn: 231k awards with PI, affiliation, a ROR-matched institution and amount (CNY). A sample showed PI 董燎原, CAS IHEP, ¥3.2M. Names are in Chinese characters, so matching them to OpenAlex authors needs transliteration. NSFC's own terms are not stated.
- **Korea.** The NRF file on data.go.kr has project, PI, researcher ID and institution, with no amount. The richer NTIS OpenAPI needs a data.go.kr key and is in Korean. OpenAlex's 115k NRF Korea awards are Crossref stubs only.
- **Sweden.** SweCRIS offers a public rotating token ("VRSwecrisAPI2026-1") or a registered key, approved within about a week. **The public token returned 401 when I probed it, so register a key.**
- **Norway.** I verified the CSV header: `prosjekttittel, prosjektleder, prosjektansvarlig_navn, tildelt_belop, prosjektstart, prosjektslutt`. It is updated quarterly.
- **Chile.** I verified the header: `NOMBRE_RESPONSABLE, INSTITUCION_PRINCIPAL, MONTO_ADJUDICADO, AGNO_FALLO, DURACION_MESES`. The file is semicolon-delimited and the repo licence is CC0.
- **Canada.** CIHR data runs from 2000-01 and SSHRC has payment and co-applicant CSVs; both are on open.canada.ca under the Open Government Licence. NSERC is already loaded, so this reuses that pattern.
- **Finland.** A public API is under active development (a Sept 2026 PR added FundedPerson). research.fi says API use "requires approval from the controller". Coverage starts in 2020.
- **CORDIS (non-ERC).** Good data but organisation-level. It is useful for "which labs host EU projects", not for naming advisors. MSCA projects do not name the supervisor.
- **US DOE/DOD.** USAspending names only the recipient institution. NIH and NSF, already loaded, carry most US academic PIs.

## Aggregators

| Aggregator | Verdict | Why |
|---|---|---|
| **OpenAlex awards** | **LOAD (primary)** | CC0, free snapshot, about 250 direct funder sources. PI, co-I, ROR institution, amount, dates and landing URL where the source has them. It already links awards to works, which matches the tool's paper view. Fill varies by source, so filter by `provenance`. |
| OpenAIRE Graph | MAYBE | CC BY. Projects API (`api.openaire.eu/graph/v3/projects`) and dumps. Strong on EU and some national funders, but PI names are rarely present. Use it for cross-checking. |
| Crossref grant DOIs | MAYBE (small) | CC0 and includes investigators, but few funders register them. OpenAlex already ingests them. |
| Dimensions | NO | Commercial; redistribution in a public tool is not allowed (not re-verified today). |

OpenAlex already covers some loaders you have (KAKEN, NSF, NIH, GtR, CORDIS, SNSF, ARC, ANR, NWO, RGC). It could eventually replace them too, but keep the bespoke loaders where they carry richer co-investigator data.

## Ranking by "students helped"

Score = destination popularity for Pakistani/South Asian students × data quality (PI + institution + amount + licence).

1. **Canada, CIHR + SSHRC** (LOAD). Top-4 destination, clean licence, PI included.
2. **China, NSFC via OpenAlex** (MAYBE). Very popular destination and 231k awards with PI. Licence ambiguity is the only drag.
3. **Germany, DFG** (MAYBE). Top-3 destination, but the PI is missing in the only bulk source. Get it from DFG or by scraping, after asking. Highest value if solved.
4. **South Korea, NRF** (MAYBE). Popular destination, PI available, open terms. Small file, no amounts.
5. **Turkey, TÜBİTAK via OpenAlex** (MAYBE). PI and co-Is, but no amount or institution.
6. **Sweden, SweCRIS** (LOAD). Full fields; just register a key.
7. **Italy, PRIN via OpenAlex** (MAYBE). PI, co-Is, institution and amount.
8. **Austria, FWF** (LOAD). CC0 with full fields; smaller destination.
9. **Taiwan, GRB** (LOAD). Full fields, open licence.
10. **Norway, RCN** (LOAD).
11. **Ireland, Research Ireland** (LOAD).
12. **Wellcome** (LOAD). Adds UK biomedical PIs that UKRI misses.
13. **Brazil FAPESP, Chile ANID, Portugal FCT, Israel ISF, Poland NCN, Finland, Denmark, Belgium FWO** (LOAD/MAYBE). Good data, low destination weight.
14. **Pakistan HEC NRPU** (MAYBE). Low "abroad" weight, but it gives home-country context and only 1.9k awards.

Not worth doing now: Malaysia, Saudi Arabia, UAE, Qatar, Singapore, South Africa, Mexico, Gates, DOE/DOD. Malaysia and Saudi Arabia rank high as destinations, but **no award-level public data exists**, so they cannot be served by grants. Papers and authors from OpenAlex works remain the only signal there.

## Uncertainty / unverified

- Licences marked "Unverified" or "Not stated": I found no terms page. Treat these as "check before publishing".
- The PI% figures come from today's OpenAlex API. Amount, abstract and institution fill comes from one sampled record per source, not full counts.
- Not checked: CNPq PI fields, the Czech CEP PI field, the India PRISM export, FNRS, Dimensions' current terms, and whether OpenAlex's free API budget suffices. The snapshot avoids that question.
