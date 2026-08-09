#!/usr/bin/env bash
set -eo pipefail; [[ $TRACE ]] && set -x

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

read -r -p "Delete all battery, environmental, and location database data? Continue? [y/N] " response

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


read -r -p "Delete all systemd journal entries as well? Continue? [y/N] " response

if [[ ! "$response" =~ ^[Yy]$ ]]; then
    exit 0
fi

sudo journalctl --rotate
sudo journalctl --vacuum-time=1s
