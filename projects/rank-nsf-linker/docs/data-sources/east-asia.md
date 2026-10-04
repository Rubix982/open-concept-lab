# East Asia — research-grant data sources

_Researched 2026-10-04. "Verified" = live response; otherwise inferred._

| Rank | Source | Access | PI names | Licence / terms | PI match to CSRankings |
|---|---|---|---|---|---|
| 1 | **Hong Kong RGC** (GRF, ECS, …) — verified | Search `POST https://cerg1.ugc.edu.hk/cergprod/scrrm00541.jsp` (institution, award years 2006–2026, subject); detail `scrrm00542.jsp?proj_id=…` (HTML) | English "Prof WANG, Yu" + Chinese, co-investigators | No reuse licence found; pages `noindex`; **ask RGC before crawling** | High (match HK spellings literally) |
| 2 | **Japan KAKEN** (JSPS) — verified | OpenSearch API needs free CiNii appid; ResourceSync at `https://kaken.nii.ac.jp/.well-known/resourcesync` → 23 lists × ~7.5k per-grant XML (`/grant/KAKENHI-PROJECT-….xml`, 5–10 KB) | Kanji + katakana readings; e-Rad number; romanised on nrid.nii.ac.jp | CC BY 4.0-compatible ("Source: KAKEN (NII)"); robots allows `/grant/*.xml` | Medium-high (katakana → Hepburn + institution) |
| 3 | **Taiwan GRB** (NSTC) — verified | Yearly XML zips via index `https://mas.nstc.gov.tw/OPENDATA/GetFile?format=csv&serialno=527&fileodr=1` (2025: 7.1 MB zip) | Chinese only | Taiwan Open Government Data Licence | Low-medium |
| 4 | Korea NTIS — endpoint verified, key not obtained | data.go.kr dataset 15077315; key application checks institutional affiliation | Likely Hangul only | KOGL Type 1; site robots `Disallow: /` | Low-medium |
| 5 | JST CREST/PRESTO | projectdb.jst.go.jp; bulk CSV/XML needs an approved application | — | No mechanical bulk download | — |
| — | China NSFC | kd.nsfc.cn, robots `Disallow: /`, no open dataset, Chinese-only names | — | — | Low — **do not ingest** |
| — | Singapore NRF / MOE AcRF | No public structured list | — | — | **Skip** |

CS filters: RGC subject "Computing Science & Information Technology"; KAKEN review sections 60xxx/61xxx (inferred);
GRB field 資訊 (inferred).

## Scholarships (official URLs)
- HKPFS — https://cerg1.ugc.edu.hk/hkpfs/index.html (verified): open to all nationalities incl. Pakistan; 2026/27 stipend HK$344,400/yr + HK$14,400 travel.
- SINGA (A*STAR) — https://www.a-star.edu.sg/scholarships/for-graduate-studies/singapore-international-graduate-award-singa
- Taiwan Scholarship — https://taiwanscholarship.moe.gov.tw/ (route for Pakistani applicants unconfirmed)
- ICDF — https://www.icdf.org.tw/ (partner/ally countries; Pakistan unlikely, unconfirmed)
