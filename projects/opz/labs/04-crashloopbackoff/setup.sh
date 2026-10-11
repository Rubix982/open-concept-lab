#!/usr/bin/env bash
# Creates a local kind cluster, builds the image, loads it, and deploys the
# (broken) greeter. Re-run any time to reset the manifests' effect.
set -euo pipefail
cd "$(dirname "$0")"
CLUSTER=opz-lab04

if ! kind get clusters | grep -qx "$CLUSTER"; then
  kind create cluster --name "$CLUSTER"
fi
kubectl config use-context "kind-$CLUSTER" >/dev/null

docker build -q -t opz-lab04-greeter:1.0 app >/dev/null
kind load docker-image opz-lab04-greeter:1.0 --name "$CLUSTER"

kubectl delete deployment greeter --ignore-not-found >/dev/null
kubectl apply -f k8s/
echo "Deployed. Watch it: kubectl get pods -w"
