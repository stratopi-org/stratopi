#!/usr/bin/env bash
set -eo pipefail; [[ $TRACE ]] && set -x

journalctl -u stratopi-environmental -o cat
