#!/usr/bin/env bash
# Creates a local kind cluster, builds and loads the image, deploys the report
# service. Re-run to reset. Run the load test with:
#   kubectl delete job load --ignore-not-found; kubectl apply -f load/job.yaml
set -euo pipefail
cd "$(dirname "$0")"
CLUSTER=opz-lab05
kind get clusters | grep -qx "$CLUSTER" || kind create cluster --name "$CLUSTER"
kubectl config use-context "kind-$CLUSTER" >/dev/null
docker build -q -t opz-lab05-report:1.0 app >/dev/null
kind load docker-image opz-lab05-report:1.0 --name "$CLUSTER"
kubectl delete job load --ignore-not-found >/dev/null
kubectl apply -f k8s/
kubectl rollout status deployment/report --timeout=90s
echo "Deployed. Now run the load test and watch: kubectl get pods -w"
