# Oceania — research-grant data sources

_Researched 2026-10-04. "Verified" = live response; otherwise inferred._

## 1. Australian Research Council (ARC) Grants Search API — verified, ingest first
- List: `https://dataportal.arc.gov.au/NCGP/API/grants?page[size]=N&page[number]=P&filter=<urlencoded>` (JSON:API, no key, page size ≤ 1000; 34,960 grants 2001–2026).
- CS filters (from the portal's JS; send only the bracketed expression):
  - `(two-digit-for="46")` → 293 grants (FoR 2020, funding years 2022–2026)
  - `(two-digit-for="08")` → 1,784 grants (old FoR, to 2022)
  - also `four-digit-for`, `year-from`, `year-to`, `scheme`, `admin-org-name`, `status`, … combined with `AND`.
- List fields: code, scheme-name, funding-commencement-year, current-admin-organisation, grant-summary, lead-investigator,
  investigators ("Prof X; Dr Y"), current/announced funding (AUD), grant-status, primary-field-of-research, anticipated-end-date.
- Detail: `https://dataportal.arc.gov.au/NCGP/API/grants/{code}` (~6 KB): `investigators-current`
  `{title, firstName, familyName, roleCode, orcidIdentifier}`, dates, organisations, all FoR codes.
- Size: all CS grants ≈ 6 MB list JSON + ~6 KB per detail.
- Licence: no explicit open licence found; ARDC terms call it public and free; attribute "Australian Research Council".
- Gotchas: filter matches the primary FoR only (cross-disciplinary CS grants missed); 2026 round has empty
  `investigators` but `lead-investigator` set; strip titles from names; slow responses (1–30 s), throttle.

## 2. NHMRC outcomes — inferred, skip for CS
Yearly XLSX on nhmrc.gov.au (unreachable from this machine).

## 3. ARDC Research Activities API — needs free key; behind Cloudflare
Only useful to get NHMRC etc. with names through one API.

## 4. New Zealand
- Marsden Fund — yearly "announcement supplement" XLSX per year (PI names, institution, panel, abstract, amount);
  CS under panel **MIS**; Cloudflare-blocked from here → **manual browser download**.
- MBIE Endeavour (Smart Ideas) — HTML behind a bot wall, low yield; HRC — health, HTML only; NZRIS — no names. Skip.

## 5. Scholarships
- NZ Manaaki — **Pakistan not eligible** (verified on nzscholarships.govt.nz/check-eligible-countries/).
- Australian Government RTP — open to international PhD students, applied for through each university (inferred; ~AUD 39k/yr).
- Australia Awards Pakistan — **master's only**, priority sectors, 5 years' work experience, age ≤ 45 (from 2026 checklist PDF; not fetched).
- NZ university doctoral scholarships — per university, open to international students.
