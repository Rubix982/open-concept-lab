#!/usr/bin/env bash
# Creates a local kind cluster, builds and loads the image, deploys the notes
# service. Re-run to reset (this deletes the deployment, and any PVCs you made).
set -euo pipefail
cd "$(dirname "$0")"
CLUSTER=opz-lab18
kind get clusters | grep -qx "$CLUSTER" || kind create cluster --name "$CLUSTER"
kubectl config use-context "kind-$CLUSTER" >/dev/null
docker build -q -t opz-lab18-notes:1.0 app >/dev/null
kind load docker-image opz-lab18-notes:1.0 --name "$CLUSTER"
kubectl delete deployment,statefulset -l app=notes --ignore-not-found >/dev/null
kubectl delete deployment notes --ignore-not-found >/dev/null
kubectl delete pvc --all >/dev/null
kubectl apply -f k8s/
kubectl rollout status deployment/notes --timeout=90s 2>/dev/null || true
echo "Deployed. In another terminal: kubectl port-forward svc/notes 8018:8080"
