# API Endpoints for NSF Rank Explorer

- [API Endpoints for NSF Rank Explorer](#api-endpoints-for-nsf-rank-explorer)
  - [University-Level Endpoints](#university-level-endpoints)
  - [Professor-Level Endpoints](#professor-level-endpoints)
  - [Award-Level Endpoints](#award-level-endpoints)
  - [Time \& Trend Endpoints](#time--trend-endpoints)
  - [Geo \& Country Insights](#geo--country-insights)
  - [Exploratory Insights](#exploratory-insights)
  - [Stats \& Aggregates](#stats--aggregates)
  - [Experimental / ML-based](#experimental--ml-based)
  - [Debug / Development](#debug--development)
  - [Filters / Metadata Helpers](#filters--metadata-helpers)
  - [Exploratory / Graph-Based](#exploratory--graph-based)
  - [Dataset Catalog / Info](#dataset-catalog--info)
  - [Utility Endpoints](#utility-endpoints)
  - [Policy \& Funding Transparency](#policy--funding-transparency)
  - [Inter-University Comparison Analytics](#inter-university-comparison-analytics)
  - [Mentorship \& Academic Lineage](#mentorship--academic-lineage)
  - [Real-time \& Streamed Stats (future extension)](#real-time--streamed-stats-future-extension)
  - [Career Insights / Researcher Profiling](#career-insights--researcher-profiling)
  - [Global \& Cross-National View](#global--cross-national-view)
  - [Foresight \& Disruption Detection](#foresight--disruption-detection)

## University-Level Endpoints

- `GET /universities/top-funded?limit=10`
- `GET /universities/most-awards?limit=10`
- `GET /universities/by-country?country=USA`
- `GET /universities/active-years?university=MIT`
- `GET /universities/top-by-area?area=Artificial Intelligence`
- `GET /universities/area-diversity-score?university=Stanford`
- `GET /universities/funding-trend?university=Berkeley`
- `GET /universities/yearly-funding?from=2010&to=2025`
- `GET /universities/near?lat=40.7&lon=-74.0&radius=200km`
- `GET /universities/by-region?region=Europe`
- `GET /universities/details?name=MIT`
- `GET /universities/compare?u1=MIT&u2=Stanford`
- `GET /universities/award-history?name=UC+Berkeley&area=AI`
- `GET /universities/awards-overlap?u1=Berkeley&u2=CMU`
- `GET /universities/funding-breakdown?name=ETH+Zurich`
- `GET /universities/award-count-by-department?university=MIT`
- `GET /universities/multidisciplinary-index?university=Caltech`
- `GET /universities/emerging-departments?limit=10`

## Professor-Level Endpoints

- `GET /professors/most-awards?limit=20`
- `GET /professors/by-university?university=CMU`
- `GET /professors/top-by-area?area=Systems`
- `GET /professors/career-span?name=John+Doe`
- `GET /professors/funding-history?name=Alice+Smith`
- `GET /professors/search?name=Jane+Doe`
- `GET /professors/by-country?country=Germany`
- `GET /professors/with-keywords?keywords=LLM,neural`
- `GET /professors/topic-shift?name=John+Doe`
- `GET /professors/publication-trend?name=Jane+Doe`
- `GET /professors/funding-trajectory?name=Alice+Smith`

## Award-Level Endpoints

- `GET /awards/by-year?year=2022`
- `GET /awards/by-topic?topic=Quantum+Computing`
- `GET /awards/by-agency?agency=NSF`
- `GET /awards/with-keywords?keywords=cloud,distributed`
- `GET /awards/top-funded?limit=50`
- `GET /awards/grouped-by/area`
- `GET /awards/grouped-by/university`
- `GET /awards/grouped-by/funding-bracket?range=100000-1000000`
- `GET /awards/search?q=multi-agent+systems`
- `GET /awards/related?award_id=1234567`
- `GET /awards/with-abstract-keywords?keywords=privacy,security`

## Time & Trend Endpoints

- `GET /trends/area-growth?area=Cybersecurity`
- `GET /trends/yearly-award-count`
- `GET /trends/overall-funding-growth`
- `GET /trends/award-clustering?by=geography&granularity=state`
- `GET /trends/funding-diffusion?area=ML&granularity=continent`
- `GET /trends/university-influence-score?university=Oxford`
- `GET /trends/funding-shocks?window=5`

## Geo & Country Insights

- `GET /geostats/area-distribution`
- `GET /geostats/top-countries-by-funding`
- `GET /geostats/funding-per-capita?country=USA`
- `GET /geostats/funding-by-latlon-grid?grid_size=1deg`
- `GET /geostats/awards-distribution-map?area=Robotics`
- `GET /geostats/university-density?region=Asia`

## Exploratory Insights

- `GET /insights/collaboration-networks?university=Stanford`
- `GET /insights/hidden-gems?min-funding=100000`
- `GET /insights/top-growing-fields`
- `GET /insights/sudden-spikes?window=3`
- `GET /insights/top-interdisciplinary-universities`
- `GET /insights/area-shift-leaders?area=Quantum+Security`
- `GET /insights/late-blooming-professors`
- `GET /insights/unexpected-awardees?threshold=0.3`

## Stats & Aggregates

- `GET /stats/university-count`
- `GET /stats/professor-count`
- `GET /stats/award-count`
- `GET /stats/funding-total`
- `GET /stats/avg-funding-per-award`
- `GET /stats/median-funding-by-area`
- `GET /stats/funding-stddev?area=AI`
- `GET /stats/year-with-most-awards`
- `GET /stats/professors-with-multiple-affiliations`

## Experimental / ML-based

- `GET /ml/clustering/universities/by-area`
- `GET /ml/clustering/funding/by-geo`
- `GET /ml/predict/funding?university=Harvard&area=AI`
- `GET /ml/recommend/awards?area=AI&university=Berkeley`
- `GET /ml/similar-professors?name=Grace+Hopper`
- `GET /ml/trend-prediction/area-growth?area=Systems`
- `GET /ml/detect/emerging-areas`

## Debug / Development

- `GET /debug/award-schema`
- `GET /debug/sample-awards?limit=5`
- `GET /debug/metadata-report`

## Filters / Metadata Helpers

- `GET /filters/available-areas`
- `GET /filters/available-universities`
- `GET /filters/available-years`
- `GET /filters/available-agencies`

## Exploratory / Graph-Based

- `GET /graph/collaboration/universities?name=Stanford`
- `GET /graph/collaboration/professors?name=David+Silver`
- `GET /graph/topic-cooccurrence`
- `GET /graph/geographic-funding-paths?source=NSF&area=HCI`

## Dataset Catalog / Info

- `GET /datasets/list`
- `GET /datasets/stats?dataset=nsf_awards`
- `GET /datasets/coverage-report`
- `GET /datasets/schema-overview`

## Utility Endpoints

- `GET /utils/normalize-name?input=UC+Berkeley`
- `GET /utils/check-university-exists?name=Princeton`
- `GET /utils/ping`
- `GET /utils/build-info`

## Policy & Funding Transparency

- `GET /policy/agency-funding-trends?agency=NSF`
- `GET /policy/impact-of-funding-cutoffs?threshold=100000`
- `GET /policy/university-dependence-score?university=Yale`

## Inter-University Comparison Analytics

- `GET /compare/universities?u1=MIT&u2=Stanford&metric=total_funding`
- `GET /compare/universities/by-area?area=AI&metric=award_count`

## Mentorship & Academic Lineage

- `GET /lineage/mentorship-tree?professor=Geoff+Hinton`
- `GET /lineage/academic-descendants?professor=Yann+LeCun`
- `GET /lineage/shared-projects?professors=Smith,Jones`

## Real-time & Streamed Stats (future extension)

- `GET /stream/funding-delta?since=2024-01-01`
- `GET /stream/live-award-events` _(event-based backend mock)_

## Career Insights / Researcher Profiling

- `GET /career/archetype?professor=Ian+Goodfellow`
- `GET /career/trajectory-map?professor=Fei+Fei+Li`
- `GET /career/role-switches?name=Alice+Johnson` _(e.g. academia → industry → return)_

## Global & Cross-National View

- `GET /international/collaboration-pairs`
- `GET /international/top-partner-countries`
- `GET /international/agency-participation-map`

## Foresight & Disruption Detection

- `GET /insights/disruptive-topics?threshold=yearly_growth>500%`
- `GET /insights/university-breakouts?window=5`
- `GET /insights/first-awards-in-topic?area=Neurosymbolic+AI`
