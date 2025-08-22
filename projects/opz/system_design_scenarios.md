# Distributed Systems & System Design Scenarios

Perfect! Let's expand these **first two sections** with **Failure Triggers / Exercises** and **Interview-Style Follow-Ups** so that each scenario becomes hands-on and discussion-ready. I've added columns for **"Failure / Exercise"** and **"Follow-Up Questions"**:

- [Distributed Systems \& System Design Scenarios](#distributed-systems--system-design-scenarios)
  - [Concurrency \& Coordination](#concurrency--coordination)
  - [Rate Limiting \& Throttling](#rate-limiting--throttling)
  - [Caching \& Storage Systems](#caching--storage-systems)
  - [Distributed Consensus \& Coordination](#distributed-consensus--coordination)
  - [Queueing \& Messaging Systems](#queueing--messaging-systems)
  - [Networking \& API Systems](#networking--api-systems)
  - [Failure Injection \& Observability](#failure-injection--observability)
  - [AI Systems \& Security Playground](#ai-systems--security-playground)
    - [**Tier 1: Low-Level Infrastructure Issues (Network, RBAC, Secrets)**](#tier-1-low-level-infrastructure-issues-network-rbac-secrets)
    - [**Tier 2: Mid-Level AI Pipeline Problems (CI/CD, Model Artifacts, Deployment)**](#tier-2-mid-level-ai-pipeline-problems-cicd-model-artifacts-deployment)
    - [**Tier 3: High-Level Attack / Threat Modeling**](#tier-3-high-level-attack--threat-modeling)
    - [**Tier 4: Observability \& Detection**](#tier-4-observability--detection)
    - [**Tier 5: Strategic Trade-offs**](#tier-5-strategic-trade-offs)
  - [Miscellaneous Systems](#miscellaneous-systems)
  - [Learning Strategy — Distributed Systems Playground](#learning-strategy--distributed-systems-playground)

---

## Concurrency & Coordination

| Scenario                              | Concepts Covered                                                             | Failure / Exercise                                                                                | Interview-Style Follow-Ups                                                                                 |
| ------------------------------------- | ---------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------- |
| Dining Philosophers Problem           | Deadlock prevention, resource ordering, semaphores, starvation handling      | Simulate all philosophers picking the same fork order → deadlock; implement odd/even ordering fix | How does ordering resources prevent deadlock? Can starvation still occur?                                  |
| Producer-Consumer with Bounded Buffer | Semaphores, mutexes, condition variables, buffer overflow/underflow handling | Fill buffer rapidly to test blocking; swap mutex order in producer vs consumer                    | What happens if mutex is unlocked incorrectly? How does semaphore ordering affect throughput?              |
| Reader-Writer Lock Implementation     | Read/write locks, starvation avoidance, fairness guarantees                  | Spawn long readers while writers wait → observe writer starvation; switch to fair lock            | How would you implement a fair reader-writer lock? What trade-offs exist between performance and fairness? |
| Sleeping Barber Simulation            | Thread scheduling, waiting queues, conditional synchronization               | Randomized customer arrival; simulate barber sleeping incorrectly or missing wake signals         | How do condition variables prevent race conditions? What happens if signaling is missed?                   |
| Implement a Semaphore from Scratch    | Atomic operations, busy waiting vs blocking, fairness                        | Build semaphore with only atomic compare-and-swap; simulate high contention                       | Can you guarantee FIFO fairness? How do busy-wait vs blocking approaches differ in performance?            |
| Distributed Locking Service           | Leader election, failure recovery, quorum, deadlock avoidance                | Simulate node failure during lock acquisition; implement leader failover                          | How do quorum and timeouts prevent deadlocks? How would network partitions affect locking?                 |
| Deadlock Detection Simulator          | Resource allocation graphs, cycle detection, deadlock recovery               | Create a cycle of resource requests across threads/nodes                                          | How do you detect cycles dynamically? What recovery strategies exist when deadlocks are detected?          |
| Barrier Synchronization Across Nodes  | Distributed barriers, coordination primitives, fault tolerance               | Delay a subset of nodes → test barrier wait and timeout handling                                  | How would you design a fault-tolerant barrier? What happens if one node fails or is slow?                  |

---

## Rate Limiting & Throttling

| Scenario                              | Concepts Covered                                                                      | Failure / Exercise                                                         | Interview-Style Follow-Ups                                                                     |
| ------------------------------------- | ------------------------------------------------------------------------------------- | -------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------- |
| API Rate Limiter (Single Node)        | Fixed vs sliding window, leaky bucket, token bucket, concurrency control              | Simulate burst traffic to see if limiter blocks correctly                  | Sliding vs fixed window: which scales better? How to handle race conditions?                   |
| Distributed Rate Limiter              | Multi-node coordination, Redis/etcd/consensus-based token bucket, clock skew handling | Introduce network partition → nodes disagree on count                      | How do you maintain consistency? How do you handle clock drift across nodes?                   |
| Priority-Based API Throttling         | Weighted queues, fairness, starvation prevention                                      | Push mixed-priority requests → check if high-priority starvation occurs    | How do you ensure low-priority requests are not starved?                                       |
| Circuit Breaker Implementation        | Failure detection, fallback strategies, exponential backoff, monitoring alerts        | Force downstream failures → breaker trips; test reset and fallback         | How to choose thresholds? How does breaker state affect system availability?                   |
| Retry Queue with Dead-Letter Handling | Retry policies, exponential backoff, idempotency, observability                       | Inject failing tasks repeatedly → verify DLQ captures failed tasks         | How do you prevent infinite retries? How do you ensure idempotency in retries?                 |
| Global Rate Limiter Across Services   | Distributed coordination, eventual vs strong consistency, performance trade-offs      | Simulate node failure or delayed updates → measure consistency of counters | How do you balance latency vs strong consistency? How would you recover from partial failures? |

---

## Caching & Storage Systems

| Scenario                         | Concepts Covered                                                               | Failure / Exercise                                                               | Interview-Style Follow-Ups                                                                         |
| -------------------------------- | ------------------------------------------------------------------------------ | -------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------- |
| Build a Simple KV Store          | Key-value storage, persistence vs in-memory, CRUD APIs                         | Simulate crash during write → test recovery; high concurrency read/write         | How would you ensure durability? Trade-offs between in-memory vs disk-backed storage?              |
| Distributed Cache                | Cache replication, consistency models (strong vs eventual), invalidation       | Simulate network partition → observe stale reads; implement TTL invalidation     | Strong vs eventual consistency: which to pick for what workloads? How to invalidate caches safely? |
| Cache with Expiration & Eviction | LRU/LFU/MRU policies, TTL management, memory limits                            | Overload cache → test eviction correctness; simulate TTL expiry while under load | How do eviction policies affect hit ratio? Can TTL and eviction conflict under load?               |
| Write-Through & Write-Back Cache | Data consistency, performance vs durability trade-offs                         | Inject write failures to backing store → test write-back recovery                | When is write-back preferred? How does write-through impact latency and consistency?               |
| Sharded KV Store                 | Hash-based partitioning, request routing, node addition/removal                | Add/remove nodes → test rebalancing correctness; simulate node failure           | How to handle key redistribution? How to avoid hotspots during rebalancing?                        |
| Persistent Queue Storage         | Disk-backed queues, recovery after crash, replay handling                      | Crash mid-write → verify queue recovery; inject duplicate writes                 | How to ensure exactly-once delivery? What trade-offs exist for durability vs performance?          |
| Mini "Kafka" Implementation      | Partitioned log, offset tracking, leader/follower replication, fault tolerance | Fail leader → test failover; simulate message ordering issues                    | How to guarantee order per partition? How to detect and recover from replica lag?                  |
| Metrics Aggregator               | Time-series aggregation, eventual consistency, fault-tolerant writes           | Drop nodes or delay metric ingestion → check aggregation accuracy                | How to handle out-of-order or missing metrics? Trade-offs between consistency and latency?         |

---

## Distributed Consensus & Coordination

| Scenario                        | Concepts Covered                                                            | Failure / Exercise                                                          | Interview-Style Follow-Ups                                                                            |
| ------------------------------- | --------------------------------------------------------------------------- | --------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| Leader Election in a Cluster    | Heartbeat mechanisms, split-brain avoidance, failover detection             | Kill leader node → verify new leader election; simulate network partition   | How to avoid split-brain? How to choose election timeout values?                                      |
| Implement Raft Consensus        | Log replication, leader election, term and quorum handling                  | Simulate network delay → observe consistency issues; fail followers mid-log | How does Raft maintain safety during partition? How to optimize election frequency?                   |
| Paxos Algorithm Simulation      | Prepare/accept phases, consensus under failures, network partition handling | Simulate delayed or lost messages → verify agreement across nodes           | When would you choose Paxos vs Raft? How does quorum size affect availability?                        |
| Consensus with Byzantine Faults | PBFT basics, malicious node detection, performance trade-offs               | Introduce "malicious" nodes → test correct consensus outcome                | How many faulty nodes can PBFT tolerate? What are the performance costs of Byzantine fault tolerance? |
| Distributed Transaction System  | Two-phase commit vs saga, partial failure handling, ACID vs BASE            | Fail participant during commit → simulate rollback or saga compensation     | How to choose between 2PC and sagas? How to handle cascading failures?                                |
| Quorum-Based Reads/Writes       | Strong vs eventual consistency, trade-offs, conflict resolution             | Delay or fail nodes → observe read/write inconsistencies                    | How does read/write quorum size affect latency and consistency?                                       |

---

## Queueing & Messaging Systems

| Scenario                         | Concepts Covered                                                | Failure / Exercise                                                                                | Interview-Style Follow-Ups                                                            |
| -------------------------------- | --------------------------------------------------------------- | ------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------- |
| Build a Job Queue from Scratch   | Task scheduling, worker pool management, persistent storage     | Simulate worker crash → test job recovery; enqueue bursts of tasks to test scheduling fairness    | How to ensure no job is lost? How to handle slow vs fast workers?                     |
| Queue with Priority              | Priority handling, starvation avoidance, fairness               | Starve low-priority jobs → check fairness; inject burst of high-priority jobs                     | How do you prevent priority inversion? How would you tune priorities under load?      |
| Pub/Sub Messaging System         | Topic partitioning, delivery guarantees, backpressure           | Drop or delay subscribers → test message delivery guarantees; simulate backpressure               | How to guarantee message delivery? How to scale topics and partitions efficiently?    |
| Retry & Dead-Letter Queue        | Retry policies, failure isolation, observability                | Fail tasks repeatedly → verify retries and DLQ routing; simulate partial system outages           | How to choose retry intervals? What workloads benefit from dead-letter queues?        |
| Rate-Limited Messaging Broker    | Throttling messages, global coordination, queue length handling | Flood broker → observe rate limiting enforcement; simulate multiple clients                       | How to implement global vs per-client throttling? How to handle bursts gracefully?    |
| Backpressure Handling in Queues  | Flow control, blocking vs dropping, congestion prevention       | Simulate downstream slowness → observe flow control behavior                                      | When to block vs drop messages? How does backpressure affect system stability?        |
| Exactly-Once Delivery Simulation | Idempotency, deduplication, message ordering                    | Duplicate messages → verify idempotent processing; simulate network partitions affecting ordering | How to implement deduplication efficiently? How to guarantee ordering under failures? |

---

## Networking & API Systems

| Scenario                                   | Concepts Covered                                         | Failure / Exercise                                                                                         | Interview-Style Follow-Ups                                                                                    |
| ------------------------------------------ | -------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| Build a Mini HTTP Server                   | Request parsing, concurrency, thread pools               | Simulate high load → test thread pool exhaustion; malformed requests → verify error handling               | How do you handle concurrency and avoid thread starvation? How to ensure security against malformed requests? |
| Queue-Based Server for Offline Requests    | Persistent request queue, retry logic, worker pools      | Fail worker mid-processing → test retry logic; persist queue → survive crash                               | How to ensure offline requests are not lost? How to prioritize requests under load?                           |
| Sharded API Gateway                        | Request routing, service discovery, load balancing       | Simulate node addition/removal → test routing correctness; fail services → test failover                   | How to route requests efficiently? How to handle partial service failures gracefully?                         |
| Rate-Limited API Gateway                   | Token bucket, sliding window, multi-service coordination | Simulate client flooding → test enforcement; coordinate multiple gateways → verify consistency             | Token bucket vs sliding window: trade-offs? How to scale rate limiting in distributed gateways?               |
| Circuit Breaker at Gateway Level           | Fail-fast strategies, fallback, monitoring integration   | Simulate repeated downstream failures → ensure fallback triggers; remove failing service → verify recovery | How to tune thresholds and timeouts? How to integrate monitoring with circuit breakers?                       |
| Distributed Load Balancer                  | Consistent hashing, health checks, failover              | Simulate node failure → verify failover; add/remove nodes → test key distribution                          | How does consistent hashing help with node churn? How to ensure minimal disruption during rebalancing?        |
| Client-Side Retry with Exponential Backoff | Retry strategies, jitter, network partition handling     | Simulate network failures → verify exponential backoff and jitter; avoid thundering herd                   | Why add jitter? How to balance retry aggressiveness vs latency and system load?                               |

---

## Failure Injection & Observability

| Scenario                          | Concepts Covered                                              | Failure / Exercise                                                                                | Interview-Style Follow-Ups                                                                   |
| --------------------------------- | ------------------------------------------------------------- | ------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------- |
| Simulate Node Crash               | Fault tolerance, recovery strategies, replication             | Kill a node abruptly → observe failover and recovery; test data consistency after restart         | How do you design for minimal downtime? How to handle partial replication states?            |
| Network Partition Simulation      | Partition tolerance, consensus handling, CAP theorem          | Split cluster into isolated partitions → check consistency, availability, and reconciliation      | How does CAP trade-off manifest? How to design partition-tolerant consensus protocols?       |
| Clock Skew in Distributed Systems | Time synchronization, consistency, token bucket coordination  | Offset clocks on nodes → test timestamp-based ordering and token expiration                       | How do clock skews affect distributed consistency? How to mitigate clock drift issues?       |
| Metrics Flood After Restart       | Prometheus-style aggregation, backpressure, alert suppression | Restart multiple services → flood metrics ingestion → test aggregation, suppression, and alerting | How to handle bursty metrics without overwhelming systems? How to prevent alert fatigue?     |
| Logging Blind Spots               | Observability, centralization, PII redaction, alert routing   | Introduce silent failures or unlogged events → detect observability gaps                          | How to centralize logs effectively? How to balance observability with PII/security concerns? |
| Debugging Intermittent Failures   | Tracing, distributed logs, deterministic replay               | Simulate rare intermittent failures → trace requests across multiple services                     | How to reproduce non-deterministic failures? How to design traceable distributed systems?    |
| Canary Rollout Failure Simulation | Deployment strategies, rollback, monitoring triggers          | Introduce failures in canary deployment → test rollback and monitoring responses                  | How to detect canary failures early? How to automate safe rollbacks?                         |
| Resource Starvation               | CPU/memory throttling, QoS, eviction strategies               | Limit node resources → observe throttling, eviction, and QoS prioritization                       | How to design fair resource allocation? How to prevent cascading failures under starvation?  |

---

## AI Systems & Security Playground

| #   | Scenario                                       | Trigger / Exercise                                                                                                                                                                                                                                                                                                                                                                                                                                   | Interview-Style Follow-ups                                                                                                                                       |
| --- | ---------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | **GPU Cluster Hardening**                      | You're given an unsecured Kubernetes GPU cluster running AI training jobs. Nodes have public IPs and weak RBAC.                                                                                                                                                                                                                                                                                                                                      | - What's the first _immediate_ action? <br> - How do you design network boundaries (VPC, private subnets)? <br> - What RBAC model fits AI workloads?             |
| 2   | **AI Data Exfiltration Risk**                  | A researcher accidentally runs a training script that sends model checkpoints to an external S3 bucket.                                                                                                                                                                                                                                                                                                                                              | - How do you detect? <br> - What monitoring stack do you set up? <br> - How do you enforce egress controls?                                                      |
| 3   | **Model Poisoning Defense**                    | You discover commits injecting poisoned datasets into the training pipeline.                                                                                                                                                                                                                                                                                                                                                                         | - How do you detect poisoned data? <br> - What would a secure CI/CD look like for AI pipelines?                                                                  |
| 4   | **Cloud Secrets Management**                   | API keys for Anthropic's internal models are hardcoded in training scripts.                                                                                                                                                                                                                                                                                                                                                                          | - What secrets manager would you integrate (AWS KMS, HashiCorp Vault)? <br> - How do you rotate keys across hundreds of GPUs?                                    |
| 5   | **Distributed Training DoS**                   | A malicious actor submits a huge batch job, exhausting cluster GPUs.                                                                                                                                                                                                                                                                                                                                                                                 | - How do you detect quota abuse? <br> - How do you design fair scheduling with Kubernetes + Slurm?                                                               |
| 6   | **Zero-Trust for AI Research**                 | Researchers want SSH access to debug models on GPU nodes.                                                                                                                                                                                                                                                                                                                                                                                            | - How do you balance research freedom vs. security? <br> - Can SSH be replaced with ephemeral Just-in-Time access?                                               |
| 7   | **Inference Abuse**                            | Someone uses a fine-tuned model endpoint to jailbreak and exfiltrate system prompts.                                                                                                                                                                                                                                                                                                                                                                 | - How do you prevent prompt injection? <br> - What runtime protections exist for inference APIs?                                                                 |
| 8   | **AI Supply Chain Security**                   | HuggingFace models and PyPI dependencies are pulled in automatically.                                                                                                                                                                                                                                                                                                                                                                                | - How do you vet and pin dependencies? <br> - How do you sign model artifacts?                                                                                   |
| 9   | **GPU Telemetry & Side Channels**              | You suspect GPU workloads can leak model weights through timing/side-channel analysis.                                                                                                                                                                                                                                                                                                                                                               | - How would you test this hypothesis? <br> - What mitigations exist (isolation, MIG, noise injection)?                                                           |
| 10  | **Security in Alignment Research**             | A new red-teaming tool is built but runs with escalated privileges.                                                                                                                                                                                                                                                                                                                                                                                  | - How do you containerize/limit blast radius? <br> - What principles of "secure alignment research" apply?                                                       |
| 11  | **Securing Multi-Tenant AI Clusters**          | Anthropic researchers need to run massive LLM training jobs on Kubernetes clusters shared by multiple teams. Someone raises a concern about data leakage across pods. </br> - Design a Kubernetes security architecture that prevents cross-namespace privilege escalation. </br> - Propose PodSecurityPolicies / PodSecurityStandards and RBAC setup. </br> - Discuss whether network policies should be enforced at cluster or service mesh layer. | - What if a researcher's job needs privileged GPU access? </br> - How do you prevent this from breaking isolation?                                               |
| 12  | **Protecting AI Model Artifacts**              | Trained checkpoints are stored in S3 buckets. A leaked model artifact would be catastrophic. </br> - Propose IAM, encryption, and access control setup for sensitive artifacts. </br> - Implement versioning & lifecycle rules that balance security with usability.                                                                                                                                                                                 | - How would you integrate detection of anomalous access? </br> - Would you use Macie, GuardDuty, or build custom anomaly detection?                              |
| 13  | **Supply Chain Security for AI Training**      | PyTorch wheels, CUDA images, and internal packages are pulled into training pipelines. Risk of malicious package insertion. </br> - Set up a hardened artifact registry with signature verification (Sigstore, cosign). </br> - Propose CI/CD pipeline hooks that block unsigned dependencies.                                                                                                                                                       | - How would you handle a zero-day in a CUDA driver during ongoing training? </br> - Rollback or live patching?                                                   |
| 14  | **Threat Modeling AI Research Infrastructure** | A red team reports that lateral movement is possible from internal research notebooks into the production inference cluster. </br> - Build a threat model (STRIDE or attack tree) for Anthropic's AI infra. </br> - Identify high-risk attack paths and propose mitigations.                                                                                                                                                                         | - What mitigations are most urgent if you only had 48 hours? </br> - How would you communicate trade-offs to research teams?                                     |
| 15  | **Securing LLM-Serving APIs**                  | Public APIs allow prompt submissions. Attackers may try prompt injection or resource exhaustion. </br> - Propose API gateway and WAF rules for large-scale inference endpoints. </br> - Design rate limiting, anomaly detection, and abuse prevention.                                                                                                                                                                                               | - How would you detect adversarial prompt sequences that aim to exfiltrate training data? </br> - Would you solve this with infra-level or model-level security? |

### **Tier 1: Low-Level Infrastructure Issues (Network, RBAC, Secrets)**

| #   | Scenario                         | Trigger / Exercise                             | Layered Follow-ups                                     | Principle / Pattern Learned                      |
| --- | -------------------------------- | ---------------------------------------------- | ------------------------------------------------------ | ------------------------------------------------ |
| 1   | Misconfigured Security Groups    | GPU nodes allow 0.0.0.0/0 SSH                  | How do you limit exposure? Bastion hosts?              | Least-privilege networking                       |
| 2   | Weak RBAC Roles                  | Users have admin on shared namespaces          | How to enforce least privilege automatically?          | Role design & enforcement patterns               |
| 3   | Hardcoded Secrets                | API keys in scripts                            | Centralized secrets management? Rotation policies?     | Secrets hygiene & rotation discipline            |
| 4   | Open S3 Buckets                  | Model checkpoints publicly readable            | Encryption & IAM policies                              | Resource exposure awareness                      |
| 5   | Unpatched Nodes                  | GPU drivers outdated                           | Rolling updates? Patch automation?                     | Update discipline & risk mitigation              |
| 6   | Over-Privileged Service Accounts | CI/CD pipeline service account can delete prod | How to audit service accounts & enforce minimal access | Principle of least privilege applied to services |
| 7   | Forgotten Default Credentials    | New VM left with default root password         | Automated detection & remediation                      | Default settings are dangerous                   |
| 8   | Misconfigured Firewall Rules     | Internal database exposed externally           | Segmentation & firewall automation                     | Network segmentation discipline                  |
| 9   | Insecure Network Storage         | Shared storage without ACLs                    | Access logging & automated audits                      | Data access control patterns                     |
| 10  | Weak Password Policies           | Users set simple passwords                     | MFA & password strength enforcement                    | Authentication hygiene                           |
| 11  | Logging Disabled                 | No audit logs on GPU jobs                      | Centralized logging & alerting                         | Observability baseline                           |
| 12  | Excessive Open Ports             | Unneeded ports open on clusters                | Port scanning & automated hardening                    | Minimal attack surface                           |
| 13  | Unmonitored IAM Changes          | Unauthorized IAM policy changes                | Event-driven detection                                 | Configuration drift awareness                    |
| 14  | Unencrypted Disk Volumes         | VM disks storing sensitive checkpoints         | Enforce encryption at rest                             | Data protection principle                        |
| 15  | Public AMI Misuse                | Researchers launch AMIs without vetting        | Hardened AMI templates                                 | Standardization & control of base images         |

### **Tier 2: Mid-Level AI Pipeline Problems (CI/CD, Model Artifacts, Deployment)**

| #   | Scenario                      | Trigger / Exercise                           | Layered Follow-ups                            | Principle / Pattern Learned             |
| --- | ----------------------------- | -------------------------------------------- | --------------------------------------------- | --------------------------------------- |
| 1   | Broken CI Pipeline            | Model training fails to trigger proper tests | How to make pipelines self-healing?           | Resilience in automated workflows       |
| 2   | Unsigned Model Artifacts      | Deployed model not verified                  | How to enforce signing & integrity checks?    | Artifact integrity & trust              |
| 3   | Environment Drift             | Dev vs. prod container mismatch              | Use reproducible builds? Lock dependencies?   | Environment parity discipline           |
| 4   | Insecure Model Deployment     | Model served without auth                    | How to enforce API auth & rate limits?        | Secure model serving practices          |
| 5   | Large Model Version Confusion | Old model deployed accidentally              | How to track versions & rollbacks?            | Version control & reproducibility       |
| 6   | Pipeline Secrets Exposure     | CI logs include database passwords           | Secret injection & vault integration          | Secure CI/CD secret handling            |
| 7   | Data Leakage in Pipelines     | Training pipeline writes to public bucket    | How to enforce data scoping & anonymization?  | Data protection in pipelines            |
| 8   | Resource Starvation           | Multiple jobs over-consume GPU               | How to schedule & isolate workloads?          | Resource management & fairness          |
| 9   | Insufficient Testing          | Model update bypasses integration tests      | How to enforce mandatory tests?               | Quality gates in pipelines              |
| 10  | Overprivileged CI Runners     | Runner can modify prod infra                 | How to isolate runners & enforce permissions? | CI/CD separation of duty                |
| 11  | Improper Rollback             | Failed model rollback corrupts logs          | How to implement safe rollback strategies?    | Safe deployment practices               |
| 12  | Inefficient Artifact Storage  | Models stored redundantly, cost blowup       | How to manage artifacts efficiently?          | Cost-aware infrastructure design        |
| 13  | Model Drift Detection Missed  | Pipeline doesn't check for drift             | Implement monitoring & retraining triggers    | Continuous validation & monitoring      |
| 14  | Pipeline Secrets Hardcoding   | Credentials embedded in scripts              | How to inject secrets dynamically?            | Secret injection & vault best practices |
| 15  | Dependency Vulnerabilities    | Outdated library in training                 | How to scan & enforce secure dependencies?    | Dependency hygiene & patching           |
| 16  | Unauthorized Model Access     | Non-researcher can pull models               | How to enforce ACLs & audit logs?             | Access control in AI pipelines          |
| 17  | Logging Overload              | Pipeline logs too verbose                    | How to balance observability & storage cost?  | Smart logging & observability design    |
| 18  | Insufficient Resource Quotas  | Job failures under high load                 | How to enforce quotas & scaling policies?     | Governance & resource planning          |

### **Tier 3: High-Level Attack / Threat Modeling**

| #   | Scenario                         | Trigger / Exercise                                      | Layered Follow-ups                                | Principle / Pattern Learned               |
| --- | -------------------------------- | ------------------------------------------------------- | ------------------------------------------------- | ----------------------------------------- |
| 1   | Adversarial Input Attack         | Malicious user crafts inputs to manipulate model output | How to detect & sanitize inputs?                  | Input validation & adversarial resilience |
| 2   | Prompt Injection                 | External actor injects malicious instructions           | How to sandbox prompts & validate outputs?        | Defensive prompt design                   |
| 3   | Insider Model Leak               | Employee exports confidential model                     | How to audit access & enforce DLP policies?       | Insider threat mitigation                 |
| 4   | Model Poisoning                  | Training data is subtly poisoned                        | How to detect anomalies & validate training sets? | Secure ML lifecycle & data hygiene        |
| 5   | Unauthorized API Usage           | API abused for unintended predictions                   | Rate limiting, auth & anomaly detection           | API security & usage governance           |
| 6   | Supply Chain Attack              | Dependency used in training contains malware            | How to vet libraries & artifacts?                 | Software supply chain security            |
| 7   | Escalation via Misconfig         | Privilege misconfig exploited                           | How to enforce least privilege & monitoring?      | Access control & privilege management     |
| 8   | Lateral Movement                 | Attacker moves from dev infra to prod                   | Network segmentation & alerting strategies        | Network isolation & monitoring            |
| 9   | Data Exfiltration                | Sensitive data leaves the org via model                 | How to encrypt & audit data flows?                | Data exfiltration prevention & auditing   |
| 10  | Rogue Training Job               | Malicious job requests unauthorized resources           | How to enforce job policy & quotas?               | Job governance & policy enforcement       |
| 11  | Model Theft via API              | External actor reconstructs the model                   | Output rate limits & watermarking                 | Model intellectual property protection    |
| 12  | Adversarial Feedback Loops       | Output of model misused to retrain                      | How to detect & prevent feedback poisoning?       | Closed-loop validation & monitoring       |
| 13  | Misuse of Fine-Tuning            | Unauthorized fine-tuning on proprietary data            | How to enforce fine-tuning policies?              | Fine-tuning governance                    |
| 14  | Compromised Dev Environment      | Malware infects model dev env                           | Container isolation & image scanning              | Dev environment hygiene                   |
| 15  | Privileged Insider Sabotage      | Admin deletes or alters logs                            | Immutable logging & monitoring                    | Tamper-evident audit trails               |
| 16  | AI Alignment Exploit             | Model prompted to bypass safety constraints             | How to implement safety guards & RLHF checks      | Alignment enforcement & monitoring        |
| 17  | Side-Channel Attack              | GPU telemetry used to infer sensitive data              | How to isolate & monitor hardware metrics         | Hardware-level threat awareness           |
| 18  | Social Engineering via Model     | Attacker uses AI to trick internal teams                | Awareness & policy enforcement                    | Human-in-the-loop threat mitigation       |
| 19  | Data Poisoning Detection Evasion | Attacker hides poisoned examples                        | Advanced anomaly detection & retraining           | Continuous vigilance in model lifecycle   |

Perfect — now we move to **Tier 4: Observability & Detection**. This focuses on **monitoring GPU/cluster telemetry, anomaly detection, and proactive alerting** — the kind of work senior engineers do to **see potential threats before they escalate**. We'll create **15–20 layered scenarios**.

### **Tier 4: Observability & Detection**

| #   | Scenario                      | Trigger / Exercise                                 | Layered Follow-ups                                  | Principle / Pattern Learned            |
| --- | ----------------------------- | -------------------------------------------------- | --------------------------------------------------- | -------------------------------------- |
| 1   | GPU Memory Spike              | One node shows sudden GPU memory growth            | Correlate with job logs; check for misbehaving jobs | Detect resource anomalies early        |
| 2   | Unexpected API Latency        | API response time increases sporadically           | Investigate throttling, queueing, network issues    | Performance monitoring & alerting      |
| 3   | Model Drift Detection         | Model outputs gradually diverge                    | Implement drift metrics & retraining triggers       | Continuous model validation            |
| 4   | Unauthorized Access Attempt   | Repeated failed login attempts on cluster          | Implement alerting & temporary lockout              | Security telemetry & response          |
| 5   | High Network Traffic          | Sudden spike between nodes                         | Identify potential exfiltration or misconfig        | Network-level anomaly detection        |
| 6   | Container Crash Loops         | Certain pods restart repeatedly                    | Check image integrity, resource limits              | Cluster health monitoring              |
| 7   | Silent Job Failures           | Jobs complete but outputs are corrupted            | Implement result validation & checksums             | End-to-end observability               |
| 8   | Rogue Resource Usage          | Single user consumes disproportionate GPU          | Enforce quotas & alert infra team                   | Resource governance & anomaly alerts   |
| 9   | Abnormal Log Patterns         | Logs contain unexpected errors                     | Create log pattern analysis & alerts                | Log anomaly detection                  |
| 10  | Suspicious File Changes       | Config files altered unexpectedly                  | Monitor file hashes & integrity                     | File integrity monitoring              |
| 11  | Latent Security Vulnerability | Metrics indicate suspicious activity but no breach | Correlate across logs & telemetry                   | Proactive threat detection             |
| 12  | ML Pipeline Stalls            | Pipeline stages take longer than normal            | Investigate dependency, network, or misconfig       | Pipeline observability & alerting      |
| 13  | Metric Degradation            | Critical metrics degrade gradually                 | Set thresholds, alerting & trending dashboards      | Early warning systems                  |
| 14  | Unauthorized API Key Use      | Key used outside expected regions                  | Implement geo/frequency monitoring                  | Access auditing & anomaly detection    |
| 15  | Cluster Node Outlier          | One node behaves differently                       | Compare metrics against cluster baseline            | Baseline comparison & anomaly spotting |
| 16  | Suspicious Batch Jobs         | Jobs with unusual parameters or frequency          | Monitor for abnormal usage patterns                 | Detect misuse proactively              |
| 17  | Data Pipeline Lag             | Delays in data ingestion or preprocessing          | Identify bottlenecks & alert                        | Observability across data pipeline     |
| 18  | Failed Model Deployments      | Deployment fails silently                          | Set automated health checks                         | Deployment observability & validation  |
| 19  | GPU Telemetry Leak            | Metrics reveal sensitive info                      | Enforce telemetry data access policies              | Hardware-level observability & privacy |
| 20  | Multi-Node Correlated Anomaly | Anomaly across multiple nodes                      | Analyze system-wide metrics & dependencies          | Holistic observability & correlation   |

### **Tier 5: Strategic Trade-offs**

| #   | Scenario                                  | Trigger / Exercise                                     | Layered Follow-ups                                   | Principle / Pattern Learned          |
| --- | ----------------------------------------- | ------------------------------------------------------ | ---------------------------------------------------- | ------------------------------------ |
| 1   | Research vs Security                      | Team wants unrestricted AI model access                | Evaluate risk vs productivity; propose tiered access | Balancing research freedom & safety  |
| 2   | Cost vs GPU Redundancy                    | Cluster duplication increases cost                     | Decide acceptable SLA vs budget                      | Resource trade-offs & prioritization |
| 3   | Model Speed vs Accuracy                   | Faster model training reduces validation               | Determine optimal trade-off for deployment           | Performance vs correctness           |
| 4   | Feature Release vs Stability              | New feature may destabilize platform                   | Plan staged rollout & rollback strategies            | Risk mitigation & release strategy   |
| 5   | Cloud vs On-Premises                      | Debate whether to run models in cloud or local cluster | Evaluate cost, latency, privacy, and compliance      | Infrastructure trade-off decisions   |
| 6   | Automation vs Manual Oversight            | Automated pipeline may skip checks                     | Decide critical manual checks & alert thresholds     | Governance in automated systems      |
| 7   | Open-Source vs Proprietary Tools          | Team wants open-source library                         | Evaluate security, support, and licensing trade-offs | Tool selection & risk assessment     |
| 8   | High Throughput vs Observability          | Monitoring adds latency                                | Decide which metrics are essential to capture        | Observability vs performance         |
| 9   | Multi-Tenancy vs Isolation                | Multiple teams share cluster                           | Evaluate cost vs risk of cross-team interference     | Tenant isolation trade-offs          |
| 10  | Fast Experimentation vs Reproducibility   | Quick experiments may be hard to reproduce             | Decide reproducibility standards                     | Research integrity vs speed          |
| 11  | Security Patching vs Uptime               | Critical patch requires downtime                       | Plan maintenance windows & backup strategy           | Availability vs security             |
| 12  | Data Privacy vs Analytics                 | Anonymizing data reduces insights                      | Decide acceptable privacy vs utility                 | Ethical & practical trade-offs       |
| 13  | Onboarding Speed vs Access Control        | New hires need access quickly                          | Define least-privilege onboarding                    | Access management trade-offs         |
| 14  | AI Autonomy vs Human Oversight            | Autonomous models vs human-in-the-loop                 | Decide thresholds for intervention                   | Safe AI deployment principles        |
| 15  | Experimental vs Production Models         | Team wants to test unvalidated models                  | Decide isolation & risk mitigation                   | Separation of environments           |
| 16  | Resource Allocation vs Fairness           | Heavy users consume disproportionate resources         | Decide quotas & prioritization strategy              | Fair resource distribution           |
| 17  | Debugging vs Privacy                      | Logs contain sensitive data                            | Decide log granularity & retention                   | Privacy-conscious observability      |
| 18  | Long-Term Maintenance vs Rapid Innovation | Rapid iteration adds technical debt                    | Plan refactoring & debt mitigation                   | Strategic technical planning         |
| 19  | Security vs Developer Experience          | Strict security slows devs                             | Decide where friction is acceptable                  | Trade-off between speed and safety   |
| 20  | Scaling vs Cost Efficiency                | Scaling cluster reduces latency but increases cost     | Evaluate scaling triggers & thresholds               | Strategic scaling decisions          |

---

## Miscellaneous Systems

| Scenario                                | Concepts Covered                                                  | Failure / Exercise                                                                     | Interview-Style Follow-Ups                                                                      |
| --------------------------------------- | ----------------------------------------------------------------- | -------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------- |
| Implement a Simple Scheduler            | Priority, time-slicing, concurrency control                       | Overload scheduler → test fairness, starvation, and preemption behavior                | How to implement priority vs round-robin scheduling? How to prevent starvation?                 |
| Transaction Isolation Levels Simulation | READ COMMITTED, REPEATABLE READ, SERIALIZABLE, deadlock scenarios | Simulate concurrent transactions → observe anomalies and deadlocks                     | Explain anomalies under each isolation level. How to prevent deadlocks effectively?             |
| Rate-Limited Database Connection Pool   | Pooling, throttling, backpressure, resource starvation            | Saturate connections → verify throttling, queuing, and client-side backpressure        | How to tune pool size vs throughput? How to prevent resource starvation in high-load scenarios? |
| Distributed Configuration Store         | Consistency, leader election, watch/notify mechanisms             | Simulate network partitions → verify consistency and leader election                   | How to implement watch/notify efficiently? How to maintain consistency during failures?         |
| TTL-Based Token Store                   | Expiration, cleanup, race conditions, distributed consistency     | Expire tokens concurrently → test cleanup and race handling                            | How to avoid stale tokens? How to maintain correctness in a distributed TTL store?              |
| Simple OAuth2 Token Issuer              | JWT validation, replay protection, token expiry handling          | Replay or modify tokens → ensure validation and revocation work correctly              | How to handle token revocation in distributed systems? How to scale token validation?           |
| Distributed Cache Invalidation          | Multi-node invalidation, performance vs correctness trade-offs    | Simulate stale cache reads → test invalidation propagation                             | How to design cache invalidation efficiently? How to handle eventual consistency?               |
| Build a Feature Flag Service            | Rollout percentages, consistency, cache invalidation              | Roll out a feature → simulate partial updates → verify consistency and correct rollout | How to implement gradual rollout safely? How to reconcile cached flag values?                   |
| Simulate Phantom Reads & Deadlocks      | Isolation levels, transaction conflicts, gap locks                | Introduce conflicting transactions → observe phantom reads and deadlocks               | How to detect and prevent phantom reads? How to design deadlock detection or avoidance?         |

---

## Learning Strategy — Distributed Systems Playground

1. **Contextual Framing**
   - Each scenario starts with a _system-level story_: nodes, services, messaging patterns, consistency requirements, and why failure matters at scale. Includes business or user impact and potential downstream effects.
2. **🧱 Minimal Reproducible Topology**
   - Defines a small-scale but realistic cluster: number of nodes, shards/partitions, leader/follower roles, consensus groups, and deployment setup (Docker, Kubernetes, local VMs). Enables hands-on experimentation without needing full prod resources.
3. **🧨 Failure Injection / Trigger Point**
   - Explicitly models _what goes wrong_:
     - Node crash, network partition, message loss, clock skew
     - Misconfigured replication, deadlocks, race conditions
     - Byzantine/malicious behavior (if BFT scenario)
4. **🔬 Observability & Diagnostic Trace**
   - Step-by-step exploration of logs, metrics, and traces across nodes. Emphasizes:
     - Detecting silent failures
     - Debugging inconsistent state
     - Evaluating replication lag and consensus convergence
     - Using distributed tracing, vector clocks, and monitoring dashboards
5. **📉 Root Cause & Architectural Retrospective**
   - Maps failure to underlying system design:
     - CAP tradeoffs violated
     - Fault isolation gaps
     - Weak abstractions in replication, leader election, or transaction handling
     - Improper assumptions in failure models
6. **🛠️ Remediation Strategy**
   - Defines actionable fixes:
     - Consensus algorithm tweaks
     - Retry, backoff, and idempotency handling
     - Partition-tolerant design patterns
     - Instrumentation improvement and alert tuning
     - Testing and simulation strategies
7. **🔐 System Hardening & Preventive Design**
   - Encourages long-term resilience thinking: - Chaos engineering and failure injection pipelines - Monitoring guardrails and SLA/SLO enforcement - Policy-as-code, automated recovery, and circuit breakers - Distributed testing frameworks (multi-node integration, BFT validation)
     >
