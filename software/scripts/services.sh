#!/usr/bin/env bash
set -eo pipefail; [[ $TRACE ]] && set -x

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

ARG="${1:-}"

case "$ARG" in
    start|stop|restart)
        ;;
    *)
        echo "usage: $(basename "$0") {start|stop|restart}" >&2
        exit 1
        ;;
esac

(
    cd "$SCRIPT_DIR/software/battery"
    sudo service stratopi-battery "$ARG"
)

(
    cd "$SCRIPT_DIR/software/communication"
    sudo service stratopi-communication "$ARG"
)

(
    cd "$SCRIPT_DIR/software/environmental"
    sudo service stratopi-environmental "$ARG"
)

(
    cd "$SCRIPT_DIR/software/location"
    sudo service stratopi-location "$ARG"
)
