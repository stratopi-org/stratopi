#!/usr/bin/env bash
set -eo pipefail; [[ $TRACE ]] && set -x

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

read -r -p "Delete all database data for battery, environmental, and location? Continue? [y/N] " response

if [[ ! "$response" =~ ^[Yy]$ ]]; then
    exit 0
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


read -r -p "Delete all systemd journal entries for battery, environmental, and location? Continue? [y/N] " response

if [[ ! "$response" =~ ^[Yy]$ ]]; then
    exit 0
fi

sudo journalctl --namespace=stratopi --rotate
sudo journalctl --namespace=stratopi --vacuum-time=1s
