# AI DevSecOps

## Simulating GPU Workloads With CPU-Only Tools

- Tools:
  - vLLM (supports CPU inference)
  - Triton Inference Server (CPU models)
  - TensorRT-LLM (limited CPU ops) just to understand deployment structure
  - Ray Serve (all CPU)
  - MLflow / DVC / Airflow / LakeFS
  - HuggingFace Optimum (CPU optimizations)
- Topics that will need to be learned,
  - Model loading
  - Tokenization
  - Batching
  - Caching
  - Inference pipelines
  - Deploying an endpoint
  - Autoscaling
  - Observability

## Required Distributed Systems Tech

- Kubernetes
- Service mesh (Istio, Linkerd)
- Autoscaling patterns
- Node/pod resource management
- Observability design
- Message queues
- Load balancing origins
- Storage systems
- Networking models for inference

## Model Serving With Small Models

- We can run,
  - DistilGPT-2
  - TinyLlama
  - Mistral 7B (slow but works)
  - Phi-2
  - LLaMA-3 8B (slow but enough for testing serving)
- Even running them slowly teaches:
  - Token streaming
  - Model memory planning
  - CPU quantization (INT8, INT4)
  - Caching behavior
  - vLLM's architecture

## AI Security

- Vulnerabilities,
  - Prompt injection
  - Jailbreaks
  - Model inversion
  - Data leakage
  - RCE through LLM agents
  - Dependency poisoning
  - Supply chain attacks
  - Model tampering
  - API surface attacks
- Tools to learn:
  - OPA Gatekeeper
  - RBAC hardening
  - Security scanning (Trivy, Grype, Syft)
  - Sigstore Cosign
  - SOPS / Sealed Secrets
  - Kubernetes PodSecurityStandards
  - Falco runtime detection
