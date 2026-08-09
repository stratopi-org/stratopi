#!/usr/bin/env bash
set -eo pipefail; [[ $TRACE ]] && set -x

SELF="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
SOFTWARE_DIR="$(cd -- "$SELF/.." && pwd)"

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
    cd "$SOFTWARE_DIR/battery"
    sudo service stratopi-battery "$ARG"
)

(
    cd "$SOFTWARE_DIR/communication"
    sudo service stratopi-communication "$ARG"
)

(
    cd "$SOFTWARE_DIR/environmental"
    sudo service stratopi-environmental "$ARG"
)

(
    cd "$SOFTWARE_DIR/location"
    sudo service stratopi-location "$ARG"
)
