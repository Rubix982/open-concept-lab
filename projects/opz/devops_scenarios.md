# Scenarios

| Scenario                                                   | Concepts Covered                                                 |
| ---------------------------------------------------------- | ---------------------------------------------------------------- |
| Pipeline Secrets Exfiltration                              | GitHub Actions, Secret Scanning, Vaults, Threat Modeling         |
| Drift in IaC Deployments                                   | Terraform, State Conflicts, GitOps Sync Failures                 |
| Kubernetes Misconfigured RBAC Attack                       | K8s, RBAC, SecurityContext, NetworkPolicies                      |
| Incident: Outage due to Ingress Controller Misconfig       | NGINX, Helm, Load Balancing, Logs                                |
| Broken Canary Deployment                                   | Argo Rollouts, Prometheus Alerts, Rollback Strategy              |
| S3 Bucket Data Leak Simulation                             | AWS IAM Policies, Misconfigured ACLs, Guardrails                 |
| Container Escape Simulation                                | PodSecurityPolicy, Seccomp, AppArmor, Runtime Hardening          |
| False Positives in DevSecOps Scanners                      | Semgrep, Trivy, Prioritization, Suppression Best Practices       |
| Logging Blind Spot During an Attack                        | Loki, Fluent Bit, Metrics vs Logs, Postmortem Writing            |
| GitOps Desync Leads to Drifted Production                  | ArgoCD, Flux, Terraform, Event-Driven Syncs                      |
| DNS Misconfiguration Leads to Partial Outage               | Route53, ExternalDNS, Health Checks, HAProxy                     |
| Rate Limiting Not Enforced on Public API                   | NGINX, AWS API Gateway, DoS Prevention                           |
| Expired TLS Cert Brings Down Frontend                      | Cert-Manager, Let's Encrypt, Renewal Automation                  |
| Zombie Resources Driving Up Cloud Bill                     | AWS Cost Explorer, Tag Hygiene, IaC Resource Lifecycle           |
| Debugging a CrashLoopBackOff Pod                           | K8s Logs, Probes, Resource Limits, ReadinessGate                 |
| Post-Deployment Failure Due to Missing Migration           | CI/CD Pipelines, DB Migrations, Rollback Plans                   |
| Overprivileged Service Accounts in K8s                     | IAM Roles for Service Accounts, Least Privilege, Audit Logs      |
| Log Injection Attack on Centralized Logging                | Fluent Bit, Log Parsing, Escaping, Secure Output Formats         |
| IAM Role Hijack via EC2 Metadata Misuse                    | IMDSv1 vs v2, Metadata Restrictions, SSRF                        |
| Privilege Escalation via Misused Jenkins Plugins           | Jenkinsfile, Plugin Security, RBAC, Audit Logs                   |
| Credential Rotations Not Propagated                        | Secrets Manager, CI/CD Pipelines, Env Caching                    |
| Open Docker Daemon Exploit                                 | Docker Socket, Root Access, Network Access Controls              |
| Helm Chart with Insecure Default Values                    | Helm Templates, Default Overrides, Config Validation             |
| Silent Data Loss from Wrong Volume Mount                   | K8s VolumeClaims, Init Containers, Data Persistence Strategy     |
| Resource Starvation due to Misconfigured Requests & Limits | K8s QoS Classes, Pod Evictions, Throttling                       |
| CI/CD Pipeline Race Condition                              | Parallel Stages, Job Dependencies, Artifact Caching              |
| Zero-Day in Dependency Not Caught in Build                 | SCA (Software Composition Analysis), Trivy, SBOMs                |
| Replay Attack via Insecure Webhooks                        | GitHub Webhooks, HMAC Signature Validation                       |
| Secret Committed in Public Repo                            | Git Hooks, Gitleaks, GitHub Token Revocation, Notifications      |
| Sensitive Log Data in Monitoring System                    | PII Redaction, Regex Filters, Alert Routing                      |
| Misconfigured Load Balancer Sticky Sessions                | HAProxy, NGINX, ALB, Session Affinity Debugging                  |
| DNS Propagation Delay Causing Rollout Chaos                | TTL, Blue/Green, CNAME Fallbacks, Health Gate Checks             |
| Metrics Flood After Rolling Restart                        | Prometheus Remote Write, Histogram Explosion, Alert Suppression  |
| AWS Lambda Timeout Bottlenecks                             | Cold Start, Memory Scaling, VPC Configuration                    |
| Alert Fatigue from Poor Thresholds                         | AlertManager, SLO-driven Alerts, Noise Reduction                 |
| Duplicate Cron Jobs Triggered by Accident                  | K8s CronJobs, Locking Mechanisms, Idempotent Tasks               |
| Container Registry Compromise                              | Docker Hub Pulls, SBOM Signing, Image Attestation                |
| Sidecar Misbehavior Affects Main Container                 | Istio, Network Policies, Sidecar Injection Debug                 |
| Infrastructure Provisioning in Partial State               | Terraform Locks, Plan Conflicts, Rollbacks                       |
| K8s Node Disk Full and Pods Crash                          | Eviction Policies, Node Exporter, Disk Usage Monitoring          |
| JWT Replay Due to No Expiry Validation                     | JWT Best Practices, OAuth2, Token Rotation                       |
| Azure AD Identity Misuse                                   | Azure Managed Identities, Least Privilege, Logs                  |
| Trivy Not Catching Runtime CVEs                            | Static vs Dynamic Scanning, CVE Feeds, Runtime Detection         |
| Hardcoded Credentials in Dockerfile                        | Multistage Builds, .dockerignore, Secrets Injection              |
| K8s Cluster Open to World via Misconfigured Ingress        | ALB Rules, Ingress Annotations, CIDR Restrictions                |
| Self-hosted GitLab Pipeline Compromise                     | GitLab Runners, Shared Runners Isolation, Artifact Handling      |
| Failure to Detect Build Tampering                          | Build Provenance, Sigstore, Attestation Frameworks               |
| Missing Retention on Logging Infrastructure                | Loki, EFK, Storage Retention, Long-Term Archiving                |
| No Rollback on Terraform Apply Failure                     | Remote Backend, Safe Apply Patterns, Automated Rollback Modules  |
| System Fails Due to Throttled API Limit                    | Rate Limiting, Retry Strategies, Exponential Backoff             |
| Shared Secret Used Across Multiple Services                | Secret Rotation, Identity Federation, Per-Service Policies       |
| Vulnerable Dependency Bypassing CI/CD Scanning             | Dev Dependency Leaks, Scan Paths, Transitive Dependency Mapping  |
| Monitoring Blind Spot in Sidecar Mesh                      | Istio Metrics, Prometheus Scrape Annotations, Sidecar Visibility |
| Alert Not Fired Due to Misconfigured Label                 | PromQL Expressions, Label Cardinality, Alert Previewing          |
| Auto-Scaling Triggers Too Early                            | HPA, Cooldown Periods, Queue Depth Based Metrics                 |
| Debugging Intermittent Network Failures in K8s             | Network Policies, DNS Resolution, CNI Debugging                  |
| Sensitive Backup Snapshots Exposed                         | AWS S3, GCP Buckets, Retention Policies, Encryption              |
| False Alert due to Clock Drift                             | NTP Sync, Distributed Systems Time, Prometheus Timestamps        |
| Escalating Build Times Due to Dependency Bloat             | CI Optimization, Caching Strategies, Docker Layers               |
| Security Group Too Permissive for Jumpbox                  | AWS EC2, Security Groups, VPC Ingress Rules                      |
| Data Exfiltration via Misconfigured SNS Topic              | AWS SNS, IAM Policies, Cross-Account Subscriptions               |
| Kubernetes Secret Mounted in Public Pod                    | K8s Secrets, VolumeMounts, RBAC Enforcement                      |
| Overlapping CronJobs Hammer Shared Resource                | CronJob Limits, Queuing, Isolation Patterns                      |
| Unintended Infra Tear-Down via Destroy Plan in CI          | Terraform Safeguards, Plan Review, Conditional Execution         |
| CI/CD System Breaks After GitHub Rate Limit Exceeded       | GitHub API, Token Scoping, Retry Strategies                      |
| Log Flooding due to Infinite Loop in App                   | Log Retention, Backpressure, Fluent Bit Buffering                |
| CloudWatch Metrics Delay Obscures Critical Alert           | CloudWatch Resolution, Alarming Delay, Metrics Over Sampling     |
| Broken RBAC: Developer Can Modify Prod Terraform           | IAM Separation, Scoped Access, Terraform Backend Restrictions    |
| Unauthorized Docker Image Pushed to Internal Registry      | CI Signing, Image Attestation, RBAC on Registry                  |
| DoS Attack via Large JSON Body                             | WAF, Payload Size Limit, API Gateway Throttling                  |
| ArgoCD Application Deleted Accidentally from UI            | RBAC Scopes, Audit Logs, PR-based Deploy Enforcement             |
| Monitoring System Down Due to Missing StorageClass         | Prometheus PVCs, K8s Storage, StatefulSet Recovery               |
| Postmortem Reveals Deadman's Switch Was Disabled           | AlertManager Deadman’s Switch, Watchdog Checks                   |
| DNS Spoofing Due to Weak Internal DNS Config               | CoreDNS, Split Horizon DNS, DNSSEC                               |
| Instance Metadata Overexposed to Internal App              | AWS IMDSv2, Metadata Token Restriction, SSRF Protections         |
| CI Runner Breakout via Host Mounts                         | GitLab Runners, Docker Socket Access, Namespace Isolation        |
| Preprod Secrets Accidentally Promoted to Prod              | Environment Segregation, Secret Tagging, Promotion Gates         |
| Unsecured Redis Allows Remote Access                       | Redis Bindings, AuthN Config, Network Segmentation               |
| Forgotten CronJob Fills Disk Over Months                   | Logrotate, Monitoring Gaps, Cron Hygiene                         |
| Misconfigured NLB Target Group Causes 503 Storm            | AWS NLB, Target Health, Connection Draining                      |
| Static S3 Website Leaking Logs                             | Bucket Policies, Logging Paths, Audit Buckets                    |
| Replay of GitHub Actions via Malicious Fork                | Action Triggers, `pull_request_target`, Token Scoping            |
| Canary Release Exposes Internal API Versions               | Ingress Rules, Header Filters, Version Routing                   |
| Slack Alert Overload Drowns Critical Signals               | Alert Routing, SLO Labeling, Notification Channels               |
| Shared EBS Volume Mount Causes FS Corruption               | AWS EBS, Mount Conflicts, StatefulSet Configuration              |
| OIDC Token Expiry Leaves Job in Zombie State               | OIDC Rotation, Job Lifespan Control, Token Refresh Hooks         |
| SSRF Leads to RDS Credential Dump                          | Metadata Protection, DB IAM, SSRF Protection Layers              |
| Insecure Helm Chart Pull from Public Repo                  | Chart Signing, Dependency Lockfiles, Private Registries          |
| Pod Crash on Timezone Mismatch                             | Timezone Config, Base Images, App Layer Time Assumptions         |

---

## ☁️ AWS-Specific Incident Scenarios

| Scenario                                               | Concepts Covered                                                               |
| ------------------------------------------------------ | ------------------------------------------------------------------------------ |
| S3 Bucket Public Exposure Detected                     | S3 Permissions, ACLs, IAM Policies, AWS Config Rules                           |
| IAM Role Misuse by EC2 Instance                        | EC2 Metadata Service (IMDSv1 vs v2), IAM Role Scoping, Credential Exfiltration |
| Security Group Allows World Access to RDS              | VPC Security Groups, Network ACLs, Principle of Least Access                   |
| Lambda Function Times Out Due to VPC Misconfig         | Lambda VPC Config, Subnet Routing, ENI Setup                                   |
| EKS Node IAM Role Escalation via Pod                   | IAM Roles for Service Accounts (IRSA), RBAC, Pod Security Policies             |
| CloudTrail Stops Logging Unexpectedly                  | CloudTrail Config, S3 Bucket Logging Failures, Monitoring with EventBridge     |
| SNS Topic Sends Secrets to External Sub                | SNS Policy, Encryption, Audit Logs, Subscription Filters                       |
| Forgotten EBS Snapshots Bloat Monthly Bill             | AWS Cost Explorer, Snapshot Lifecycle Policies, Tag Enforcement                |
| Auto Scaling Loop Consumes Budget Rapidly              | ASG Policies, Health Checks, Scaling Triggers                                  |
| CodePipeline Skipped Approval and Deployed to Prod     | CodePipeline Stages, Manual Approvals, Change Control                          |
| CloudWatch Alarms Fail Due to Missing Metric           | CloudWatch Namespace Config, Alarm Validation, Metric Retention                |
| Secrets Manager Rotation Fails Silently                | Lambda Rotation Functions, Secrets Lifecycle, Failure Notification             |
| SES Compromised and Used for Spam Campaign             | SES Identity Management, Sending Limits, DKIM/SPF                              |
| Route53 Propagation Delay Breaks Frontend              | DNS TTL, Health Checks, Multi-Region Records                                   |
| CloudFront Cache Leaks User Sessions                   | Cache Key Config, Cookie Whitelisting, Origin Header Mismatches                |
| AWS Batch Fails Due to Misconfigured Compute Env       | EC2 Spot Policies, IAM Permissions, Batch Queue Priorities                     |
| VPC Peering Route Table Missing                        | VPC Peering, Route Table Associations, NACL Conflicts                          |
| SQS Message Flood Unprocessed, Causes Latency          | SQS Visibility Timeout, Dead Letter Queues, Lambda Triggers                    |
| EBS Burst Credits Exhausted                            | gp2 Volume Metrics, IO Throughput Bottlenecks, Alarming                        |
| CloudWatch Logs Expose Internal Tokens                 | Log Sanitization, Centralized Logging, PII Scrubbing                           |
| Open RDP Port on Bastion Host                          | Security Group Review, GuardDuty Alerts, AWS Inspector                         |
| KMS Key Not Enabled for RDS Encryption                 | RDS Snapshots, Encryption in Transit & At Rest, Automated Audits               |
| Overlapping ALB Rules Cause Route Collisions           | ALB Listener Rules, Priority Conflicts, Path vs Host Matching                  |
| CloudFormation Stack Deletion Leaves Orphan Resources  | Stack Dependencies, Retain Policies, Drift Detection                           |
| ECR Image Not Scanned for CVEs                         | ECR Image Scanning, Lifecycle Rules, SBOM Best Practices                       |
| API Gateway Key Rotation Breaks Clients                | API Key Lifecycle, Caching Issues, Versioned APIs                              |
| Parameter Store Used Insecurely in Plain Text          | SSM Parameter Policies, Encryption with KMS, Access Control                    |
| GuardDuty Flags EC2 Behavior from Malicious Domain     | Threat Intelligence Feeds, Flow Logs, Security Hub                             |
| IoT Rule Sends Sensitive Payload to Untrusted Endpoint | AWS IoT Core, Rule Actions, TLS Validation                                     |

## Learning Strategy

1. **📌 Contextual Framing**
   A real-world failure or misconfiguration modeled after production incidents. Includes business impact, system topology, and why it _matters beyond the error_.

2. **🧱 Stack Composition**
   Recreates the system minimally but realistically: IaC definitions (Terraform/CloudFormation), app services, CI/CD flows, and surrounding tooling. Enables reproducible environments for hands-on introspection.

3. **🧨 Failure Injection / Trigger Point**
   Defines _how_ the system broke (or could be broken). Surfaces behavior under specific load, misconfig, race condition, or exploit vector.

4. **🔬 Diagnostic Trace**
   Deep dive into logs, metrics, traces, and configs — **how a senior engineer would actually discover the issue**. Attention to silent failures, noisy alerts, observability gaps, and traceability across layers.

5. **📉 Design Retrospective**
   Maps the root cause to upstream architectural flaws: misuse of primitives, poor abstraction boundaries, overly permissive defaults, brittle pipelines, or unclear ownership. Encourages thinking in _causal graphs_ and _failure surfaces_.

6. **🛠️ Remediation Strategy**
   Pinpoints code-level fixes, IaC corrections, access policy changes, or SLO realignment. Includes **before/after diffs**, rollback paths, alert tuning, and downstream communication steps (e.g., Slack/StatusPage postmortems).

7. **🔐 Hardening & Prevention**
   What systemic guardrails _should’ve already existed_? Introduces fuzz tests, regression pipelines, mutating webhooks, escalation paths, policy-as-code, and long-term resilience levers. Treats incident not as a patch, but as a leverage point for reliability culture.
