#!/usr/bin/env bash
# Build Weaviate from the local source checkout and run it under a headless
# Delve debugger, on the same ports as the Docker container (8080 / gRPC 50051).
#
# Attach from another terminal with:  dlv connect 127.0.0.1:2345
# (or attach VS Code / GoLand to 127.0.0.1:2345)
#
# Stop the Docker container first (docker compose stop) so the ports are free.
set -euo pipefail

WEAVIATE_SRC="${WEAVIATE_SRC:-$HOME/workspace/weaviate}"
DATA_DIR="$(cd "$(dirname "$0")" && pwd)/.weaviate-debug-data"
DLV="$(command -v dlv || echo "$(go env GOPATH)/bin/dlv")"

cd "$WEAVIATE_SRC"

AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED=true \
PERSISTENCE_DATA_PATH="$DATA_DIR" \
ENABLE_MODULES="text2vec-cohere,generative-cohere" \
CLUSTER_HOSTNAME=node1 \
CLUSTER_IN_LOCALHOST=true \
CLUSTER_GOSSIP_BIND_PORT=7100 \
CLUSTER_DATA_BIND_PORT=7101 \
RAFT_BOOTSTRAP_EXPECT=1 \
"$DLV" debug ./cmd/weaviate-server \
  --headless --listen=127.0.0.1:2345 --api-version=2 --accept-multiclient --continue \
  -- \
  --scheme http --host 127.0.0.1 --port 8080 \
  --read-timeout=600s --write-timeout=600s
