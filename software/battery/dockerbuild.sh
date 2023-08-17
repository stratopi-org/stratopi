#!/usr/bin/env bash
set -e; [[ $TRACE ]] && set -x

readonly NAME="ghcr.io/stratopi-org/battery"
read -r VERSION < .version
readonly TAG="v$VERSION-$(git rev-parse --short HEAD)"
readonly IMG="$NAME:$TAG"
printf "\nDocker image: %s\n\n\n" "$IMG"

docker buildx create --use
docker buildx build --platform linux/arm64 -t "$IMG" --push .
