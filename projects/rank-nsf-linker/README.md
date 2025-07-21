# Rank NSF Linker

This system helps prospective students, collaborators, or researchers **identify active faculty** in specific research areas, along with **their affiliations, recent funding from NSF, and latest publications** — all in a searchable and mappable format.

- [Rank NSF Linker](#rank-nsf-linker)
  - [🧭 Use Cases](#-use-cases)
  - [🔁 Step-by-Step Pipeline](#-step-by-step-pipeline)
  - [Expected Outcome](#expected-outcome)
  - [🔗 Algorithm: Mapping CS Faculty to NSF Awards \& Google Scholar Publications](#-algorithm-mapping-cs-faculty-to-nsf-awards--google-scholar-publications)
    - [🧠 Step-by-Step Algorithm](#-step-by-step-algorithm)
  - [🛠️ Expand Features to Support Further Use Cases](#️-expand-features-to-support-further-use-cases)

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
