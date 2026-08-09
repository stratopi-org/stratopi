#!/usr/bin/env bash
set -eo pipefail; [[ $TRACE ]] && set -x

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

read -r -p "This will truncate all battery, environmental, and location data. Continue? [y/N] " response

if [[ ! "$response" =~ ^[Yy]$ ]]; then
    exit 2
fi

(
    cd "$SCRIPT_DIR/software/battery"
    python -m util.truncate
)

(
    cd "$SCRIPT_DIR/software/environmental"
    python -m util.truncate
)

(
    cd "$SCRIPT_DIR/software/location"
    python -m util.truncate
)
