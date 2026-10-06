# Rank NSF Linker

This system helps prospective students, collaborators, or researchers **identify active faculty** in specific research areas, along with **their affiliations, recent funding from NSF, and latest publications** — all in a searchable and mappable format.

- [Rank NSF Linker](#rank-nsf-linker)
  - [🧭 Use Cases](#-use-cases)
  - [🔁 Step-by-Step Pipeline](#-step-by-step-pipeline)
  - [Expected Outcome](#expected-outcome)
  - [🔗 Algorithm: Mapping CS Faculty to NSF Awards \& Google Scholar Publications](#-algorithm-mapping-cs-faculty-to-nsf-awards--google-scholar-publications)
    - [🧠 Step-by-Step Algorithm](#-step-by-step-algorithm)
  - [🛠️ Expand Features to Support Further Use Cases](#️-expand-features-to-support-further-use-cases)
- [Running the population pipeline](#running-the-population-pipeline)
- [Debugging](#debugging)
  - [http: server gave HTTP response to HTTPS client](#http-server-gave-http-response-to-https-client)

## Guided tour

The app (http://localhost:3000) has a guided tour: **Tour** in the header, or open
http://localhost:3000/?tour=1 to start it straight away (handy for recording a walkthrough). It runs a
real search ("robot learning") and walks through results, filters, a profile, the Funding tab and a
university, ten steps; Esc leaves it.

## 🧭 Use Cases

| Use-Case                                      | Description                                                                                                                                          |
| --------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| 🧑‍🎓 **Prospective MS/PhD Students**            | See what’s being funded, who’s doing the research, and what topics are hot — across US/EU universities. Perfect for tailoring applications.          |
| 🧠 **Independent Researchers**                | Track research momentum across institutions. Identify trends, labs, grants. Plan their own research or apply for funding.                            |
| 🧑‍🏫 **Professors / Advisors**                  | Compare institutions, find potential collaborators or co-PIs. Spot underfunded areas. Use NSF history to write better proposals.                     |
| 🧑‍💼 **Policymakers / Think Tanks**             | Visualize how much money is flowing into AI, Security, etc. across universities. See regional biases or funding trends.                              |
| 🧑‍💻 **Open-Source Contributors**               | Use it to find professors or teams doing real research in fields they care about (like formal methods, distributed systems) and offer collaboration. |
| 📚 **Academic Bloggers / Journalists**        | Great for pulling stories: “Top 5 institutions funded in AI last 3 years”, “Security vs. Privacy funding over time” etc.                             |
| 🧑‍🔬 **Industry Researchers / Hiring Managers** | Spot rising academic talent by tracking who's publishing _and_ getting funded — helps recruitment or scouting for partnerships.                      |

## 🔁 Step-by-Step Pipeline

1. **Filter Faculty by Area & Region**

   - Parse CSRankings dataset (`generated-author-info.csv`)
   - Use `AREA_GROUPS` to match subareas to top-level domains (e.g., AI, Systems, etc.)
   - Allow selection of countries/regions (e.g., US, Germany, Australia)
   - Deduplicate faculty records by name and department

2. **Map Faculty to University Geolocation**

   - Use institutional CSVs to locate each university's latitude and longitude
   - Visualize all matches on an interactive map using `folium`, color-coded by area group
   - Popups show individual faculty, their departments, and matched research venues

3. **Integrate NSF Funding Data**

   - Download annual NSF Award Search ZIP files (2019-2025)
   - Extract and normalize project data (e.g., PI, university, title, abstract)
   - Join awards to faculty using cleaned names and affiliations
   - Optionally allow filtering by keyword or award amount

4. **Enhance with Recent Research Activity**

   - Match faculty to their **Google Scholar** profiles (planned via scraping or Semantic Scholar/ORCID APIs)
   - Fetch latest 3-5 publications per professor
   - Display titles, publication year, and direct links in popups or reports

5. **Output Modes**

   - 📦 Export to CSV with all metadata: name, affiliation, area, homepage, NSF awards, recent papers
   - 🗺️ Generate map (`university_map.html`) to visually explore global research hotspots
   - 📊 Optionally extend with charts: top-funded areas, award counts by year, etc.

## Expected Outcome

To use this parser and scraper as a source to generate ideas about research projects for implementation.

## 🔗 Algorithm: Mapping CS Faculty to NSF Awards & Google Scholar Publications

This algorithm enhances the core faculty selection tool by connecting researchers with publicly available NSF funding data and recent research output via Google Scholar.

---

### 🧠 Step-by-Step Algorithm

```text
1. [Faculty Selection]
   └── Use CSRankings dataset to filter faculty by:
       ├── Research Area (e.g. AI, Systems)
       └── Country / University / Affiliation

2. [Download NSF Data]
   └── For each year (2025 → 2019):
       ├── Download NSF Award zip from official URL
       └── Unzip into a structured directory: ./data/nsf/awards/<year>/

3. [Parse NSF Awards]
   └── For each CSV file:
       ├── Read rows with fields:
       │     → PI Name, University, Title, Amount, Abstract, Year, Award URL
       └── Normalize PI name + University for matching (lowercase, remove extra tags)

4. [Match Faculty ↔ NSF Awards]
   └── For each faculty member:
       ├── Match name + affiliation to PI Name + Organization
       └── Store all matched NSF awards as a list under that faculty

5. [Fetch Google Scholar Publications]
   └── If `scholarid` is available for a faculty:
       ├── Use 'scholarly' to fetch latest publications (title, year, venue)
       └── Store top 3-5 papers under that faculty

6. [Augment Final Output]
   └── For each faculty (filtered result):
       ├── Display:
       │     → Affiliation, Department, Research Areas
       │     → NSF Awards (Title, Year, Amount, Link)
       │     → Recent Publications (Title, Year, Venue)
       └── Output to:
           → Pretty CSV
           → Interactive Map (folium popup)
           → Optional terminal preview

7. [Visualization]
   └── On the generated map:
       ├── Group markers by research area color
       ├── Each marker popup includes:
       │     → Faculty info
       │     → NSF awards (with links)
       │     → Recent publications (Google Scholar)
```

## 🛠️ Expand Features to Support Further Use Cases

| Feature                                                  | Why Add It                                                           |
| -------------------------------------------------------- | -------------------------------------------------------------------- |
| 🧭 **Smart Filters** (Year, Funding Size, Research Area) | Helps zoom in on the “AI 2023 under \$1M” type of question           |
| 🧑‍🔬 **Faculty Profile Pages**                             | Like mini pages showing name, institution, NSF grants, papers        |
| 📄 **Paper ↔ Grant Linkage**                             | If a paper links to a grant (via award ID or PI), show it            |
| 💰 **Funding Trend Timelines**                           | Show bar graphs / line charts for AI, Systems, Security across years |
| 📍 **Regional Funding Breakdown**                        | Show how funding is distributed within US or Europe                  |
| 📤 **Export Options** (CSV, JSON)                        | Helps bloggers, journalists, students do deeper dives                |
| 🔄 **Daily/Weekly Sync with NSF API**                    | Keep data fresh                                                      |
| 💡 **“Suggested Researchers” Engine**                    | “If you liked this grant/lab, here are similar ones”                 |

# Running the population pipeline

The Go server (`go-server` container) loads Postgres on startup in 29 steps
(`pipelineSteps` in `server/db.go`). Each step records its status in `pipeline_status`. The pipeline
fetches its own data: CSRankings, NSF and IPEDS in Go; every other source (11 grant funders, DAAD,
DBLP, OpenAlex) through the `fetcher` container (`fetcher/app.py`, state in `data/fetch_state/`).
API keys come from `server/.env` only. A source that stops at a daily allowance (OpenAlex: 10,000
calls) keeps its previous data, and the server reruns the pipeline about once a day until it is
complete, and every 7 days after that (`PIPELINE_REFRESH_DAYS`).

| Command | What it does |
| --- | --- |
| `make up` | Start everything; the pipeline runs if it has never completed |
| `make pipeline` | Restart `go-server`; resumes at the first step that has not completed |
| `make pipeline-from STEP=N [TO=M]` | Rerun step N (to M) and everything after it (e.g. `STEP=27` to fetch OpenAlex and embed) |
| `make golden` | Save the finished state (Postgres dump + both Qdrant indexes + manifest) to `golden/<date>/` |
| `make golden-verify DIR=golden/<date>` | Restore it into scratch copies, compare counts, delete them |
| `make golden-restore DIR=golden/<date>` | Load it into the live app: a new server is ready in minutes |

From nothing, the fetches take days (OpenAlex's allowance) and embedding about 6 hours; restoring a
golden dataset (about 3.5 GB, not in git) takes a few minutes.

**Starting from nothing.** A new server with an empty `data/` fetches everything itself. It needs:

- `server/.env` with `OPENALEX_API_KEY` (free, openalex.org) and `CINII_APP_ID` (free, KAKEN), read by the
  fetcher only. FWF's read key is public and fetched at run time.
- The curated files committed in `backup/` (coordinates, aliases, Pakistani universities, scholarships,
  Marsden spreadsheets, ERC result-list URLs, `openalex_institutions.csv`, `zh_institutions.csv`,
  `carnegie.csv`). When a download is missing they stand in: CSRankings no longer publishes
  `geolocation.csv`, and when nces.ed.gov can't be reached (`SKIP_IPEDS=1`) R1/R2 status comes from
  `carnegie.csv` (tuition and other IPEDS fields stay empty).
- About 25 GB of disk and a few days: the OpenAlex fetches (~22k calls) span several daily allowances;
  everything else finishes on the first run. A golden dataset (`make golden-restore`) skips all of it.

**Data the pipeline reads**

- `data/` — CSRankings CSVs, NSF award JSONs (`data/nsfdata/<year>/`), IPEDS CSVs (`data/ipeds_data/<year>/`)
- `backup/institution_aliases.csv` — hand-curated institution spellings (`alias,canonical,note`) for cases the
  matching rule can't solve. `backup/` is mounted, so after editing it run `make pipeline-from STEP=16`; no rebuild.

**IPEDS.** nces.ed.gov is often unreachable, so `SKIP_IPEDS=1` (dev compose) skips the download and the
pipeline ingests whatever is in `data/ipeds_data/`. To fill that from the parquet cache in `data/ipeds_cache/`:

```bash
cd server/scripts/ipeds
python3.12 -m venv .venv && .venv/bin/pip install -r requirements.txt   # once
cd ../../.. && server/scripts/ipeds/.venv/bin/python server/scripts/ipeds/parquet_to_csv.py 2023
```

**How records are linked**

- Institutions: one matching rule, `institution_key()` (`server/migrations/8_institution_aliases.sql`);
  every merged spelling is kept in `institution_aliases`. Rows carry `institution_type`
  (`university`, `university_affiliate`, `business`, `organization`) and, for US universities, `ipeds_unitid`.
- People: NSF investigators live in `nsf_investigators`; `professor` is their CSRankings match, set only when a
  shared name is backed by evidence (an award at the professor's university, or a matching email domain).
  See `server/link.go`.

Open work is tracked in `TODO.md`.

# Debugging

## http: server gave HTTP response to HTTPS client

If "HTTP/HTTPS" error occurs while pushing the docker images, add the following to the Docker Engine configuration,

```json
  "insecure-registries": [
    "host.docker.internal:5128"
  ]
```
