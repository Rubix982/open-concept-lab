# Funder terms, Korea NRF data, NCN call calendar (research, 2026-10-06)

## Summary table (Part A)

| Source | What the publisher says | Verdict | Credit line to show |
|---|---|---|---|
| NHMRC (AU) | CC BY 4.0 on NHMRC material | **OK** | "Source: National Health and Medical Research Council" |
| FWO / FRIS (BE) | Flemish Free Open Data Licence (Modellicentie Gratis Hergebruik) | **OK** | "Source: FRIS / Flemish Government" |
| NCN (PL) | Public-sector reuse under the 2016 Act. Conditions: name the source and the date | **OK** | "Source: Narodowe Centrum Nauki (NCN), retrieved <date>" |
| AMED (JP) | Reuse allowed with source and URL; mark edits; commercial use needs a form | **OK** (we are non-commercial) | "出典：国立研究開発法人日本医療研究開発機構 (AMED) <URL>" |
| ICMR (IN) | "may be reproduced free of charge"; acknowledge source prominently | **OK** | "Source: ICMR" |
| FAPESP BV (BR) | SP open-data catalogue lists BV FAPESP as CC-BY open data. I could not open that page | **OK (medium confidence)** | "Source: Biblioteca Virtual da FAPESP" |
| NSFC kd.nsfc.cn (CN) | Only "Copyright © NSFC"; no reuse terms found | **OK-FACTS** | link back |
| FCT (PT) | No site terms page; footer "©2022 FCT" | **OK-FACTS** | link back |
| TÜBİTAK / TR Dizin (TR) | The "Terms" page only covers personal data (KVKK). Project full texts depend on coordinator permission and embargo | **OK-FACTS** (show abstracts only if OpenAlex has them) | link back |
| ISF (IL) | Not verified: isf.org.il refused connections from here | **OK-FACTS (unverified)** | link back |
| ZonMw (NL) | Only "© 2026 ZonMw"; no disclaimer clauses | **OK-FACTS** | link back |
| DFF / forskningsportal.dk (DK) | "Open… whenever possible", but no licence stated for grant data | **OK-FACTS** | "Source: Research Portal Denmark" |
| NAFOSTED (VN) | Footer "Coryright © Quỹ Phát triển KH&CN Quốc gia" only | **OK-FACTS** | link back |
| HEC NRPU (PK) | Footer has "Terms & Condition" and "Copyrights HEC 2019", but the links go nowhere (`href="#"`) | **OK-FACTS** | link back |
| ISCIII Portal FIS (ES) | "queda prohibida su reproducción… sin la autorización expresa del ISCIII" | **ASK** before showing abstracts. Facts plus link are low risk | link back |
| NSF Sri Lanka (LK) | Terms forbid copying, displaying or distributing "any part of the Content" | **ASK** before showing abstracts. Facts plus link are low risk | link back |

No source reached DROP. A general point applies everywhere: the grant facts we show (title, PI, institution, amount, dates) are facts and are weakly protected. Abstracts are the copyrightable part. EU sources (ES, PT, NL, DK, PL, BE) also have the database right, which covers taking a substantial part of the database. We take the data from OpenAlex's CC0 copy, show it for non-commercial use, and link back, so the risk is low. Where a row is ASK, hiding abstracts removes most of the risk.

## Part A — key quotes and URLs

- **NHMRC:** NHMRC publications say "provided under a Creative Commons Attribution 4.0 International licence". I saw this in NHMRC PDFs; the /copyright page timed out. https://www.nhmrc.gov.au/funding/data-research/outcomes
- **FRIS:** data is released under "onze gratis opendata-licentie" (our free open-data licence), which allows reuse "with only one condition: attribution". https://www.ewi-vlaanderen.be/onze-opdracht/innoverende-samenleving/fris-flanders-research-information-space , https://overheid.vlaanderen.be/modellicentie-gratis-hergebruik
- **NCN:** "Podmiot ponownie wykorzystujący… powinien wskazać źródło oraz czas wytworzenia i pozyskania" (whoever reuses must state the source and when the information was created and obtained). https://www.ncn.gov.pl/bip/dzialalnosc/ponowne-wykorzystanie
- **AMED:** "出所を明示することにより、引用・転載・複製を行うことが出来ます" (may be quoted, reprinted or copied if the source is shown). Edits must be marked. "商業目的で使用する場合は…申請書をご提出ください" (commercial use needs an application form). The policy does not name AMEDfind. https://www.amed.go.jp/site_policy.html
- **ICMR:** "Material featured on this Website may be reproduced free of charge… the source must be prominently acknowledged." https://www.icmr.gov.in/copyright-policy
- **FAPESP:** a search snippet for http://catalogo.governoaberto.sp.gov.br/dataset/biblioteca-virtual-da-fapesp says "Creative Commons Attribution Open Data license". The page refused connections, so I could not read it myself.
- **ISCIII:** "queda prohibida su reproducción, distribución, comunicación pública y transformación, total o parcial, sin la autorización expresa del ISCIII" (reproducing or distributing the content, in whole or in part, needs ISCIII's express permission). https://www.isciii.es/aviso-legal
- **NSF Sri Lanka:** "You may not copy, display, distribute, modify, publish… any part of the Content." https://www.nsf.gov.lk/index.php/component/sppagebuilder/?view=page&id=731
- **TR Dizin:** https://trdizin.gov.tr/en/terms/ covers personal data only.
- **forskningsportal.dk:** no licence is named on https://forskningsportal.dk/about-data-documentation/download-data/download-grant-metadata/ . Asking norainfo@dst.dk would settle it.
- **NSFC** (https://kd.nsfc.cn/), **ZonMw**, **FCT**, **NAFOSTED**, **HEC:** each has only a © footer or dead links.

## Part B — Korea NRF

**Dataset:** 한국연구재단_이알앤디_과제정보 (NRF R&D project information). https://www.data.go.kr/data/3049029/fileData.do
- **Direct download, no login needed** (the portal says "파일데이터는 로그인 없이 다운로드를 통해 이용하실 수 있습니다", i.e. file data can be downloaded without logging in). I tested it: `https://www.data.go.kr/cmm/cmm/fileDownload.do?atchFileId=FILE_000000003238770&fileDetailSn=1&insertDataPrcus=N` returned the file. The `atchFileId` changes with every annual refresh, so the code should read it from the dataset page.
- **Format:** CSV, about 2.2 MB, **CP949/EUC-KR encoding** (not UTF-8), 11,788 rows.
- **Columns:** 사업년도 (funding year), 선정년도 (selection year), 대사업명, 중사업명, 소사업명, 세부사업명 (four programme levels), 과제명 (title), 연구책임자명 (PI name), 연구자번호 (researcher number), 주관기관명 (host institution), 보안과제여부 (classified project Y/N). There are **no amounts, no end dates and no abstracts.**
- **Coverage is thin.** The page says it covers only "일부" (some) projects. Years are 2023–2025 only. About 88% of rows (10,370) are humanities and social sciences (학술·인문사회사업). Only 964 rows are science and engineering basic research (이공분야기초연구사업).
- **Licence (이용허락범위):** "제한 없음" (no restrictions). **Updates:** yearly; the next refresh is listed as 2026-10-05, last modified 2026-08-28.
- **Other routes:**
  - NRF KRS Open API (https://www.data.go.kr/data/15073646/openapi.do) includes 과제신청및선정현황 (applications and selections) and 과제정보 (project info). Licence 제한 없음 (no restrictions), updated in real time. It needs a free data.go.kr account and service key; the development quota is 5,000 calls.
  - KISTI NTIS national R&D project search API (https://www.data.go.kr/data/15077315/openapi.do). Licence 공공저작물 제1유형 (Korean public-works licence, type 1: attribution only). Also needs a key.
- **NTIS bulk download:** none without login. Real-time export is capped at 10,000 records. Batch download goes to registered members by email. The full "R&D 데이터 신청" (R&D data request) needs a login and an application form (https://www.ntis.go.kr/rndgate/eg/oneMain/OneIndex.do).

## Part C — NCN Poland call calendar

**Key finding:** the leading number in "10_HARMONIA_6808" is most likely NCN's **edition number** (numer edycji), not the HARMONIA call number. NCN grant numbers look like `YYYY/EE/X/PP/NNNNN`, where EE is the edition. Edition 10 contains HARMONIA 5. Each edition has one fixed announcement and closing date. Source: NCN's full edition table, 2011–2026, at https://www.ncn.gov.pl/finansowanie-nauki/faq/edycje (I read it directly).

**Edition number to opening date (true for all 62 editions):** edition E opens in year **2011 + floor((E−1)/4)**. The opening month is **March, June, September or December** for E mod 4 = 1, 2, 3, 0. Each call closes about 3 months after it opens.

**Call number to edition** (worked out from NCN's table):

| Programme | Rule (n = call number) | Exceptions / notes |
|---|---|---|
| OPUS | E = 2n−1 (OPUS 1 … OPUS 31 = ed. 61) | — |
| PRELUDIUM | E = 2n−1 for n ≤ 19 | from n = 20: E = 4n−39 (PREL 25 = ed. 61) |
| SONATA | E = 2n−1 for n ≤ 12 | SONATA 13 = ed. 26; 14 = ed. 31; from n = 15: E = 4n−25 (SONATA 21 = ed. 59) |
| SONATA BIS | E = 4n−2 for n ≥ 3 | SONATA BIS 1 = ed. 5; 2 = ed. 7 |
| MAESTRO | E = 4n−10 for n ≥ 5 | MAESTRO 1–4 = ed. 2, 4, 6, 8 |
| HARMONIA | E = 4n−10 for n ≥ 5 | HARMONIA 1–4 = ed. 1, 4, 6, 8; the last call is HARMONIA 10 = ed. 30 (2018) |
| ETIUDA | E = 4n+4 | runs 1–8 (ed. 8–36) |
| SONATINA | E = 4n+20 | runs 1–10 (ed. 24–60) |
| SYMFONIA | E = 4n+4 | runs 1–4 (ed. 8–20) |
| FUGA | 1–3 = ed. 4, 8, 12; FUGA 5 = ed. 20 | FUGA 4 is not in NCN's table |
| PRELUDIUM BIS | 1–5 = ed. 35, 39, 43, 47, 50 | — |
| POLONEZ / POLONEZ BIS | POLONEZ 1–3 = ed. 19, 21, 23; POLONEZ BIS 1–3 = ed. 43, 45, 47 | — |

MINIATURA is not in the table. From memory (not verified), it runs as one rolling call per year from about 2017.

Worked example: if "10_HARMONIA" means edition 10, it is HARMONIA 5, opened June 2013. If 10 is the call number, it is HARMONIA 10 = edition 30, opened June 2018.

**Results timing:** results usually come about 5–6 months after the call closes:
- **March round:** results Nov–Dec of the same year. Example: OPUS 25/PRELUDIUM 22 results on 2023-11-23 (https://www.ncn.gov.pl/en/aktualnosci/2023-11-23-wyniki-opus22-preludium25).
- **September round:** results May–June of the next year. Example: the autumn round with OPUS 28/SONATA 20 had results on 2025-05-27 (https://www.ncn.gov.pl/aktualnosci/2025-05-27-wyniki-jesiennej-rundy-konkursow).
- **June round** (MAESTRO, SONATA BIS) and **December round** (SONATINA): about 5–6 months after closing. I did not check these against a specific announcement.

Projects usually start 1–6 months after results. A safe estimate is **start year = results year** (or the year after for March rounds), **end = start + the programme's longest duration**.

**Durations** (from NCN call pages, e.g. https://www.ncn.gov.pl/en/ogloszenia/konkursy/opus29 , /sonata-bis15 , /maestro17 , /sonatina10 ):

| Programme | Duration (months) |
|---|---|
| OPUS | 12–48 |
| PRELUDIUM | 12–36 |
| SONATA | 12–36 (recent calls) |
| SONATA BIS | 36–60 |
| MAESTRO | 36–60 |
| HARMONIA | 12–36 |
| SONATINA | 24–36 |

From memory, not checked against NCN pages:

| Programme | Duration (months) |
|---|---|
| PRELUDIUM BIS | 36–48 |
| ETIUDA (doctoral stipend) | 6–12 |
| FUGA | 24–36 |
| SYMFONIA | 36–60 |
| MINIATURA | up to 12 |
| POLONEZ / POLONEZ BIS | 12–24 / 24 |

## What I could not verify
- I could not reach the ISF, NSFC and FAPESP catalogue pages, or the NHMRC copyright page.
- I found no licence at all for forskningsportal.dk grant data.
- FUGA 4's edition is missing from NCN's table.
- I assume the leading number in OpenAlex NCN ids is the edition. I did not test this on real ids; checking a few against NCN grant numbers would settle it.
