#!/usr/bin/env bash
set -eo pipefail; [[ $TRACE ]] && set -x

journal_command="journalctl -u stratopi-location -o cat"

if [ "$1" = "--follow" ]; then
    $journal_command --follow
else
    $journal_command
fi
