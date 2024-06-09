#!/usr/bin/env bash
set -eo pipefail; [[ $TRACE ]] && set -x

journal_command="journalctl -b -u stratopi-battery -o cat"

if [ "$1" = "--follow" ]; then
    $journal_command --follow
else
    $journal_command
fi
