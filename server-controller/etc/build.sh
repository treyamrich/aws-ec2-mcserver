#!/bin/bash
set -euo pipefail

REGISTRY="localhost:5000"

usage() {
    echo "Usage: ./etc/build.sh <deploy-strategy> <starter> <version>"
    echo "  deploy-strategy: local, ec2, k8s"
    echo "  starter:         discord, http"
    echo "  version:         semver tag (e.g. 1.0.0)"
    exit 1
}

[[ $# -ne 3 ]] && usage

STRATEGY_INPUT="$1"
STARTER="$2"
VERSION="$3"

# Map user-friendly names to code values
case "$STRATEGY_INPUT" in
    local)   DEPLOY_STRATEGY="local" ;;
    ec2)     DEPLOY_STRATEGY="aws_ec2" ;;
    k8s)     DEPLOY_STRATEGY="kubernetes" ;;
    *)       echo "Error: unknown deploy-strategy '$STRATEGY_INPUT'"; usage ;;
esac

case "$STARTER" in
    discord|http) ;;
    *) echo "Error: unknown starter '$STARTER'"; usage ;;
esac

PLATFORM_FLAG=""
if [ "$DEPLOY_STRATEGY" = "local" ]; then
    PLATFORM_FLAG="--platform linux/amd64"
fi

IMAGE="${REGISTRY}/mc-server-controller-${STRATEGY_INPUT}-${STARTER}"

docker build $PLATFORM_FLAG \
    -f etc/Dockerfile \
    --build-arg DEPLOY_STRATEGY="$DEPLOY_STRATEGY" \
    --build-arg STARTER="$STARTER" \
    -t "${IMAGE}:v${VERSION}" \
    .

echo "Pushing ${IMAGE}:v${VERSION}..."
docker push "${IMAGE}:v${VERSION}"

echo "Done: ${IMAGE}:v${VERSION}"
