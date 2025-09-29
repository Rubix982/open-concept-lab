# AI

- [AI](#ai)
  - [Souces](#souces)
    - [1. Direct Paper Libraries with Code Links](#1-direct-paper-libraries-with-code-links)
    - [2. Workshop-Level Sources (Easier to Implement)](#2-workshop-level-sources-easier-to-implement)
    - [3. Specific Curated Lists](#3-specific-curated-lists)
    - [4. Dataset Sources for Security + AI](#4-dataset-sources-for-security--ai)
    - [5. Target Keywords](#5-target-keywords)
  - [Funding](#funding)
    - [Security (most urgent / high-impact)](#security-most-urgent--high-impact)
    - [AI (most active / publishable / fundable)](#ai-most-active--publishable--fundable)
    - [Software / Engineering (what teams are actually building)](#software--engineering-what-teams-are-actually-building)
    - [Cross-cutting industry/geo/policy signals](#cross-cutting-industrygeopolicy-signals)
    - [Where to read / follow (quick starter list)](#where-to-read--follow-quick-starter-list)
    - [Quick playbook for you (as MS Cybersecurity aiming at AI/Sec research)](#quick-playbook-for-you-as-ms-cybersecurity-aiming-at-aisec-research)
    - [References](#references)
  - [Top AI+SEC Companies](#top-aisec-companies)
    - [1. **Wiz — cloud security / posture + CSPM at scale**](#1-wiz--cloud-security--posture--cspm-at-scale)
      - [1. Misconfiguration detection from IaC (Terraform / CloudFormation)](#1-misconfiguration-detection-from-iac-terraform--cloudformation)
      - [2. Cloud telemetry anomaly detection (logs/metrics) with transformer time-series](#2-cloud-telemetry-anomaly-detection-logsmetrics-with-transformer-time-series)
      - [3. Agentless asset fingerprinting \& discovery via metadata + network flows](#3-agentless-asset-fingerprinting--discovery-via-metadata--network-flows)
      - [4. Risk-prioritization / Learning-to-Rank for alerts](#4-risk-prioritization--learning-to-rank-for-alerts)
      - [5. Automated remediation suggestion using constrained LLMs](#5-automated-remediation-suggestion-using-constrained-llms)
      - [6. Adversarial robustness for CSPM models (attacks \& defenses)](#6-adversarial-robustness-for-cspm-models-attacks--defenses)
      - [7. Model monitoring \& concept-drift detection for cloud-security models](#7-model-monitoring--concept-drift-detection-for-cloud-security-models)
      - [8. Privacy-preserving threat intel sharing (federated learning)](#8-privacy-preserving-threat-intel-sharing-federated-learning)
  - [Interview / Hiring Playbook: how to present these projects to Wiz](#interview--hiring-playbook-how-to-present-these-projects-to-wiz)
    - [2. **SentinelOne — AI-driven endpoint detection \& response (EDR)**](#2-sentinelone--ai-driven-endpoint-detection--response-edr)
    - [3. **CrowdStrike — AI-powered endpoint + cloud security platform**](#3-crowdstrike--ai-powered-endpoint--cloud-security-platform)
    - [4. **Darktrace — network/enterprise anomaly detection using ML**](#4-darktrace--networkenterprise-anomaly-detection-using-ml)
    - [5. **Orca Security — agentless cloud security \& data-centric risk**](#5-orca-security--agentless-cloud-security--data-centric-risk)
    - [6. **Snyk — developer-first application security (SCA/IAST/API security)**](#6-snyk--developer-first-application-security-scaiastapi-security)
    - [7. **Lacework / (and similar cloud security vendors)** — cloud workload protection + ML](#7-lacework--and-similar-cloud-security-vendors--cloud-workload-protection--ml)
    - [8. **Model \& AI-security specialist startups (example: Robust Intelligence — model safety / ML security)**](#8-model--ai-security-specialist-startups-example-robust-intelligence--model-safety--ml-security)
    - [References](#references-1)

## Souces

### 1. Direct Paper Libraries with Code Links

- **[Papers With Code](https://paperswithcode.com/)**

  - Best starting point → search "adversarial machine learning," "LLM jailbreak," "federated learning security."
  - Each paper shows code repos + benchmarks.

- **[NeurIPS Proceedings](https://papers.nips.cc/)**

  - Search terms: _robustness, adversarial, security, privacy, poisoning, red-teaming_.
  - NeurIPS papers are often followed by open-sourced repos on GitHub.

- **[USENIX Security Symposium Proceedings](https://www.usenix.org/conferences/byname/108)**

  - Security-specific. Search _adversarial ML, data poisoning, AI security_.
  - Many USENIX papers have reproducible datasets and attack/defense code.

### 2. Workshop-Level Sources (Easier to Implement)

- **NeurIPS Workshops (AI Safety, Adversarial ML, Security & Privacy)** → papers are shorter, often code-backed.
- **USENIX WOOT (Workshop on Offensive Technologies)** → practical security+AI attack papers.
- **ICLR Workshops (Adversarial Robustness, LLM Safety)** → lots of reproducible implementations.

### 3. Specific Curated Lists

- **[Awesome Adversarial Machine Learning](https://github.com/yenchenlin/awesome-adversarial-machine-learning)** (GitHub list of reproducible papers + repos).
- **[AI Security Papers list by MITRE](https://github.com/mitre/advmlthreatmatrix)** → connects papers to real-world security threats.
- **[Federated Learning Security Repos](https://paperswithcode.com/task/federated-learning)** → many poisoning/backdoor papers here.

### 4. Dataset Sources for Security + AI

- **[CICIDS2017](https://www.unb.ca/cic/datasets/ids-2017.html)** → intrusion detection logs.
- **[EMBER](https://github.com/elastic/ember)** → malware classification dataset.
- **[DARPA OpTC](https://github.com/FiveDirections/OpTC-data)** → cyber traffic dataset.
- **[MIMIC-III (for anomaly detection experiments)](https://physionet.org/content/mimiciii/1.4/)** → can be adapted for anomaly/robustness tasks.

### 5. Target Keywords

- `"adversarial machine learning" site:nips.cc`
- `"data poisoning" site:usenix.org`
- `"LLM jailbreak adversarial" NeurIPS`
- `"federated learning security" NeurIPS USENIX"`
- `"robustness AI safety workshop"`

## Funding

### Security (most urgent / high-impact)

1. **AI-enabled attacks & defenses (agentic AI risk)**

   - Why: Autonomous/multi-agent attackers can scale phishing, credential stuffing, and automated exploitation; defenders are using agentic systems for detection and response. This is reshaping threat models. ([TechRadar][2])
   - Project idea: build and evaluate a "red-team agent" that composes multi-step phishing campaigns against a simulated org, vs a detection agent — measure detection lag and false positives.

2. **Adversarial ML, LLM jailbreaks & model safety**

   - Why: Attacks that manipulate training data, or exploit LLM prompting, remain top research areas and are now mainline security concerns. NeurIPS/USENIX workshops put robustness & agent safety front and center. ([NeurIPS][3])
   - Project idea: reproduce a recent LLM jailbreak paper and extend it to show practical SOC/automation risks; submit to a NeurIPS/USENIX workshop.

3. **Supply-chain attacks & software provenance**

   - Why: Attacks through dependencies and CI/CD pipelines continue to be effective and costly; provenance + SBOMs + attestation are trending controls. ([World Economic Forum][4])
   - Project idea: implement a lightweight attestation + anomaly detector for pip/npm packages and test against simulated supply-chain poisoning.

4. **Zero Trust & identity fraud (AI-augmented)**

   - Why: Identity attacks (deepfakes, synthetic identities) integrated with AI make fraud easier; zero-trust microsegmentation and continuous auth are increasing priorities. ([SentinelOne][5])

### AI (most active / publishable / fundable)

1. **Agentic / multi-agent AI (safety & evaluation)**

   - Why: Agentic systems are exploding in workshops and competitions — evaluation, benchmark design, and containment are hot problems. NeurIPS 2025 had multiple agent/agentic tracks. ([NeurIPS][3])
   - Research angle: build benchmarks that measure emergent unsafe policies in multi-agent LLM systems and propose mitigations.

2. **LLM safety, red-teaming & interpretability**

   - Why: Practical safety (prompt injection, data leakage, hallucinations) is a top industrial and academic priority. Workshops heavily emphasize human-in-loop evaluation. ([NeurIPS][6])
   - Project/paper: a reproducible framework for automated red-teaming + human validation with measurable metrics (precision/recall of unsafe content).

3. **Robustness, certified defenses & adversarial ML**

   - Why: As models are deployed in critical systems, provable robustness and certification methods are getting traction again (e.g., certified defenses, robust training at scale). ([McKinsey & Company][1])

4. **Privacy-preserving ML (federated learning, DP) for sensitive domains**

   - Why: regulated domains (health, defense) demand privacy-preserving pipelines; federated learning attacks/backdoors are an active threat area. ([World Economic Forum][4])

### Software / Engineering (what teams are actually building)

1. **AI-first platform engineering & DevSecOps**

   - Why: Platform teams embed AI (code assistants, automated CI checks, policy as code) and expect developers to rely on intelligent platform primitives. This affects how infra is designed and secured. ([duplocloud.com][7])
   - Practical: add an ML-based PR scanner into CI that flags probable security regressions (and measure developer friction).

2. **Observability + AIOps**

   - Why: With distributed systems, observability + automated fault-repair using AI (AIOps) is trending. OpenTelemetry and ML anomaly detection are becoming defaults. ([CNCF][8])
   - Project: build ML models over traces/metrics to predict incidents and produce explainable alerts.

3. **Edge & privacy-sensitive ML ops**

   - Why: Pushing models to edge devices and maintaining security/privacy in constrained environments is rising (IoT, mobile).
   - Project: secure on-device model update pipeline with signed model attestation.

4. **AI-assisted coding and security linting**

   - Why: LLMs as co-developers are mainstream; integrating them into secure code generation + vetting is now an ops problem. ([Data Centers][9])

### Cross-cutting industry/geo/policy signals

- **Government & critical infrastructure focus** — national security budgets and procurement keep funding cyber/AI work (important for Arlington/DC placements). ([The Washington Post][10])

### Where to read / follow (quick starter list)

- **NeurIPS / ICLR / ICML workshops** (safety, robustness, agents). ([NeurIPS][6])
- **USENIX Security / WOOT / IEEE S&P** (adversarial ML + system security). ([World Economic Forum][4])
- **PapersWithCode** (code links + leaderboards) — great for picking reproducible targets.
- **Industry reports**: McKinsey tech trends, WEF Global Cybersecurity Outlook, vendor blogs (SentinelOne, CrowdStrike) for tactical signals. ([McKinsey & Company][1])

### Quick playbook for you (as MS Cybersecurity aiming at AI/Sec research)

1. **Pick 2 high-impact themes** from above (e.g., _LLM safety_ + _adversarial ML for IDS_).
2. **Reproduce 2-3 papers** (workshops/NeurIPS) — focus on those with repos/datasets.
3. **Produce 1 novel extension** (new threat model, larger scale, cross-domain adaptation) and target a NeurIPS/USENIX workshop submission.
4. **Use co-op data** (if permitted) to ground experiments in real pipelines — that’s huge CV currency.
5. **Ship reproducible code + short blog** — hiring managers and program committees value reproducibility.

### References

[1]: https://www.mckinsey.com/~/media/mckinsey/business%20functions/mckinsey%20digital/our%20insights/the%20top%20trends%20in%20tech%202025/mckinsey-technology-trends-outlook-2025.pdf? "Technology Trends Outlook 2025"
[2]: https://www.techradar.com/pro/agentic-ai-cybersecuritys-friend-or-foe? "Agentic AI: cybersecurity's friend or foe?"
[3]: https://neurips.cc/Downloads/2025? "Downloads 2025"
[4]: https://www.weforum.org/publications/global-cybersecurity-outlook-2025/? "Global Cybersecurity Outlook 2025 | World Economic Forum"
[5]: https://www.sentinelone.com/cybersecurity-101/cybersecurity/cyber-security-trends/? "10 Cyber Security Trends For 2025"
[6]: https://neurips.cc/virtual/2025/events/workshop? "NeurIPS 2025 Workshops"
[7]: https://duplocloud.com/blog/emerging-trends-in-platform-engineering-for-2025/? "Emerging Trends in Platform Engineering for 2025 | Insights"
[8]: https://www.cncf.io/blog/2025/03/05/observability-trends-in-2025-whats-driving-change/? "Observability Trends in 2025 - What's Driving Change?"
[9]: https://www.datacenters.com/news/top-software-development-trends-to-watch-in-2025? "Top Software Development Trends to Watch in 2025"
[10]: https://www.washingtonpost.com/technology/2025/10/02/cisa-shutdown-cybersecurity/? "Shutdown guts U.S. cybersecurity agency at perilous time"

## Top AI+SEC Companies

### 1. **Wiz — cloud security / posture + CSPM at scale**

What they build: cloud risk posture, vulnerability & misconfiguration discovery, agentless scanning and prioritized remediation for cloud infra. Big rounds recently (notably a $1B round, $12B valuation in 2024). Why it matters: cloud security is where AI/analytics meet large telemetry — if you want co-ops that combine ML, infra, and security telemetry, Wiz is a leading target. ([wiz.io][1])

#### 1. Misconfiguration detection from IaC (Terraform / CloudFormation)

**What:** Train models to detect insecure/misconfigured IaC patterns (open S3, over-permissive IAM roles, insecure security groups) and produce human-readable fixes.
**Why Wiz cares:** CSPM needs to scan IaC at scale and reduce false positives while suggesting targeted fixes.
**Data / sources:** scrape public GitHub IaC repos, KICS/tfsec rule sets as weak labels, synthesize misconfigs.
**Tech stack:** Python, Hugging Face (transformer encoder for code), CodeBERT/GraphCodeBERT, scikit-learn, tfsec/KICS for baseline.
**Metrics:** precision@k for true misconfigs, F1, false-positive rate, % auto-fix suggested accepted in user study.
**4-6 week plan:** dataset scrape & weak-labeling (wk1-2); model prototyping (wk3-4); explanation + remediation template generator (wk5); demo & README (wk6).
**Deliverables:** GitHub repo, notebook, dataset snapshot, demo video (2-3 min showing detection → fix).
**Resume bullet:** "Built an IaC misconfiguration detector using CodeBERT + weak-labeling on 10k Terraform files; reduced noisy alerts by 46% vs tfsec baseline and auto-suggested remediation templates."

#### 2. Cloud telemetry anomaly detection (logs/metrics) with transformer time-series

**What:** Train transformer-based time-series/anomaly models on CloudTrail/flow logs and surface anomalous resources and root-cause components.
**Why Wiz cares:** prioritize noisy alerts across many tenants and find systemic misconfigurations vs attacks.
**Data / sources:** public network datasets (MAWILab/CIC), simulated CloudTrail via terraform + synthetic workloads, open-source telemetry exporters.
**Tech stack:** Python, PyTorch, Time-series Transformers (Informer/Transformers), OpenTelemetry, Elastic / Kafka for ingestion.
**Metrics:** ROC-AUC, precision@N for top-10 anomalous resources, mean time-to-detection (MTTD) in simulation.
**4-6 week plan:** create ingestion + synthetic attack scenarios (wk1-2); baseline (LSTM/ARIMA) vs transformer (wk3-4); RCA visualization & dashboard (wk5-6).
**Deliverables:** Dashboard (Grafana/Elastic), Jupyter notebooks, synthetic dataset + attack scripts.
**Resume bullet:** "Implemented transformer-based anomaly detector over simulated CloudTrail; improved top-10 precision by 38% vs traditional baselines and produced automated root-cause summaries."

#### 3. Agentless asset fingerprinting & discovery via metadata + network flows

**What:** Build an ML model that, using only cloud metadata + network flow features, classifies asset type, exposure level, and probable misconfig (no agent required).
**Why Wiz cares:** agentless scanning is a core competitive differentiator — do it with ML to infer missing context and reduce blind spots.
**Data / sources:** generate cloud accounts with varied services using test AWS/GCP accounts or use public datasets; combine with NVD/CVE mappings.
**Tech stack:** Python, XGBoost/LightGBM, feature store (Feast), AWS boto3 / GCP SDK for data generation.
**Metrics:** classification accuracy, recall for high-risk assets, reduction in inventory gaps.
**4-6 week plan:** scripted cloud env generator (wk1); feature engineering + model training (wk2-3); evaluation and partial integration to demo scanner (wk4-6).
**Deliverables:** scanner CLI, model, sample outputs for a tenant.
**Resume bullet:** "Built agentless asset fingerprinting pipeline using cloud metadata + flow features; discovered 92% of high-risk resources without agent deployment."

#### 4. Risk-prioritization / Learning-to-Rank for alerts

**What:** Learn to rank alerts/tickets by business impact using historical remediation outcomes and external CVE/NVD severity.
**Why Wiz cares:** CSPM value is prioritization — which findings to fix first to reduce risk/cost.
**Data / sources:** public CVE/NVD, mock historical triage logs (synthesize), or partner with small org for anonymized logs.
**Tech stack:** Python, LightGBM / CatBoost ranking objective, ElasticSearch for retrieval.
**Metrics:** NDCG, MRR, % of high-risk items appearing in top-k, estimated reduction in expected loss.
**4-6 week plan:** collect signals & labels (wk1-2); ranker training + feature ablation (wk3-4); integrate ranking into alert UI simulation (wk5-6).
**Deliverables:** ranking model, reproducible scripts, demo UI & evaluation report.
**Resume bullet:** "Developed learning-to-rank alert prioritization that improved NDCG@10 by 0.32 and reduced estimated remediation cost in simulation by 28%."

#### 5. Automated remediation suggestion using constrained LLMs

**What:** Build a safe LLM-based assistant that suggests remediation steps (Terraform snippet or CLI commands), but constrained with static checks & policy validators to avoid unsafe edits.
**Why Wiz cares:** remediation suggestions speed up fix cycles but must be safe & explainable.
**Data / sources:** curated remediation corpora (CIS benchmarks, vendor docs), IaC examples.
**Tech stack:** Open-source LLM (Llama2 / Vicuna-style), retrieval-augmented generation (RAG) with vector DB, policy-safety sandbox.
**Metrics:** accuracy of suggested fix, % of suggestions that pass an automated policy verifier, user acceptance in small user study.
**4-6 week plan:** collect remediation snippets (wk1-2); RAG pipeline + safety verifier (wk3-4); user study script + evaluation (wk5-6).
**Deliverables:** demo where LLM suggests Terraform fix and sandbox verifier rejects unsafe ones, plus logs.
**Resume bullet:** "Created retrieval-augmented remediation assistant for IaC that auto-suggests validated fixes; 91% of suggestions passed automated policy checks."

#### 6. Adversarial robustness for CSPM models (attacks & defenses)

**What:** Design poisoning/evasion attacks against your IaC/alert models and propose robust defenses (robust training, data sanitization, certification if possible).
**Why Wiz cares:** attackers may try to evade CSPM; demonstrating robustness is a selling point.
**Data / sources:** your project datasets (from 1-4), and adversarial attack toolkits (TextAttack, Foolbox).
**Tech stack:** PyTorch, adversarial libraries, provenance tracking.
**Metrics:** drop in detection rate under attack, improvement after defense, certified bounds if applicable.
**4-6 week plan:** implement evasion + poisoning attacks (wk1-2); defenses + evaluation (wk3-5); write-up & reproducibility scripts (wk6).
**Deliverables:** attack scripts, defense code, reproducible eval table.
**Resume bullet:** "Evaluated poisoning and evasion attacks on IaC detectors and implemented robust training pipeline reducing attack success rate by 67%."

#### 7. Model monitoring & concept-drift detection for cloud-security models

**What:** Production-ready pipeline to monitor deployed models on telemetry, detect drift, alert on distribution shifts, and trigger retraining/sandbox checks.
**Why Wiz cares:** modeling at scale requires operational safety and low-maintenance models.
**Data / sources:** synthetic streaming logs, OpenTelemetry traces, historic metrics.
**Tech stack:** Kafka, Prometheus, Python, Alibi Detect or River for streaming drift, MLflow for model lifecycle.
**Metrics:** time-to-drift-detection, false alarm rate, successful auto-retrain cycles.
**4-6 week plan:** streaming synthetic data + baseline model (wk1-2); drift detectors + hooks (wk3-4); auto-retrain demo (wk5-6).
**Deliverables:** Dockerized pipeline, monitoring dashboard, playbook.
**Resume bullet:** "Built model-monitoring pipeline for cloud-security models that detected distributional drift within 120 minutes and triggered safe retraining."

#### 8. Privacy-preserving threat intel sharing (federated learning)

**What:** Federated learning framework for multiple tenants to jointly train detection models without sharing raw logs — include secure aggregation + differential privacy controls.
**Why Wiz cares:** customers want collective intelligence without exposing tenant data.
**Data / sources:** simulate multiple tenant datasets; use DP libraries.
**Tech stack:** Flower/FedML, TensorFlow/PyTorch, PySyft or Opacus for DP.
**Metrics:** delta in model utility vs centralized training, privacy budget (ε), communication cost.
**4-6 week plan:** multi-node FL simulation (wk1-2); DP + aggregation (wk3-4); evaluation & write-up (wk5-6).
**Deliverables:** FL simulation scripts, evaluation, privacy/config tuning guide.
**Resume bullet:** "Prototyped a federated anomaly detection system for multi-tenant cloud telemetry achieving 92% utility of centralized training with ε=1.5 DP guarantees."

## Interview / Hiring Playbook: how to present these projects to Wiz

1. **Problem → Data → Model → Production**: Always show the data pipeline (how you’d ingest CloudTrail/IaC), why the model was chosen, and how it would run in-prod (latency, cost, inferencing constraints).
2. **Explainability & low FPR**: demonstrate how you reduce false positives (explainable features, rule+model hybrids).
3. **Proof of production readiness**: Docker container, simple REST API, lightweight benchmark on sample tenant.
4. **Business impact**: quantify "estimated time saved," "remediation cost reduced," or "reduction in noisy alerts."
5. **Open-source & standards**: integrate or compare to tfsec/KICS, CIS benchmarks, OpenTelemetry — shows you’re industry-aware.
6. **Tie to CSPM value prop**: emphasize agentless approaches, multi-tenant scale, and remediation prioritization — core Wiz differentiators.

### 2. **SentinelOne — AI-driven endpoint detection & response (EDR)**

What they build: autonomous endpoint protection, runtime detection/response and threat hunting driven by ML/behavioral models. Funding/exit history: large private rounds and a major IPO (their growth has funded large R&D pushes into model/agentic detection). Why it matters: great for co-ops doing ML for telemetry, anomaly detection, or building detection models working close to production telemetry. ([Clay][2])

### 3. **CrowdStrike — AI-powered endpoint + cloud security platform**

What they build: Falcon platform (endpoint, cloud workload protection) with heavy ML for prevention, detection, threat intel and response automation. Large public company with significant R&D on detection models; frequent hiring for ML+security roles. Why it matters: strong co-op + FTE pipeline in ML security, threat intel, and telemetry engineering. ([Tracxn][3])

### 4. **Darktrace — network/enterprise anomaly detection using ML**

What they build: probabilistic ML and anomaly detection across enterprise networks and cloud. Recent financing and growth pushes to expand ML capabilities and global coverage. Why it matters: if you want to research/implement unsupervised detection algorithms at scale, Darktrace is a relevant place. ([Darktrace][4])

### 5. **Orca Security — agentless cloud security & data-centric risk**

What they build: agentless cloud security (identity, data, workload risks), scanning cloud metadata and using analytics/ML to prioritize critical risks. Strong venture backing and fast growth. Why it matters: cloud telemetry + model/heuristic design, good for cloud-security + ML co-ops. ([Contrary Research][5])

### 6. **Snyk — developer-first application security (SCA/IAST/API security)**

What they build: developer-integrated security tooling (dependency scanning, SAST/SCA) with automation — lately expanding into API and supply-chain security (important for secure AI supply chains). Big fundraising history and likely IPO path. Why it matters: if you want SecDevOps + ML applied to code analysis (code embeddings, vulnerability detection), Snyk is a prime target. ([Tracxn][6])

### 7. **Lacework / (and similar cloud security vendors)** — cloud workload protection + ML

What they build: behavioral analytics for cloud workloads, anomaly detection across IaC and runtime — large funding history and primary players in cloud security. Why it matters: similar to Wiz/Orca; if cloud security telemetry + ML is your focus, these are hot. ([Latka][7])

### 8. **Model & AI-security specialist startups (example: Robust Intelligence — model safety / ML security)**

What they build: tools for model/ML lifecycle security (model validation, data provenance, model robustness, monitoring). Some of these startups have been acquired/partnered with large networking/security vendors (example: Robust Intelligence integration news). Why it matters: target these if you want to work specifically on LLM safety, model poisoning defenses, model monitoring and secure model deployment. ([SiliconANGLE][8])

### References

[1]: https://www.wiz.io/blog/celebrating-our-1-billion-funding-round-and-12-billion-valuation "Celebrating Our $1 Billion Funding Round and $12 ..."
[2]: https://www.clay.com/dossier/sentinelone-funding "How Much Did SentinelOne Raise? Funding & Key Investors"
[3]: https://tracxn.com/d/companies/crowdstrike/__9ZiFQz2xBM2CTXqz7YIXn1l9mm5SQSb2efu2uZCFlVc? "CrowdStrike - 2025 Company Profile & Team"
[4]: https://www.darktrace.com/news/cyber-security-company-darktrace-in-65-million-fundraise-to-accelerate-global-expansion-in-round-led-by-kkr-6 "Darktrace Gains $65M for Cybersecurity Growth"
[5]: https://research.contrary.com/company/orca-security "Orca Security Business Breakdown & Founding Story"
[6]: https://tracxn.com/d/companies/snyk/__R962gE3cLhPYE6YfvOOI_C7Ek9zrtlGPOgVeCjDvLBI/funding-and-investors "Snyk - 2025 Funding Rounds & List of Investors"
[7]: https://getlatka.com/companies/lacework "How Lacework hit $350M revenue with a 762 person team in ..."
[8]: https://siliconangle.com/2024/08/27/cisco-snaps-ai-model-data-security-startup-robust-intelligence/ "Cisco's Robust Intelligence acquisition boosts AI security"
