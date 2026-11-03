#!/usr/bin/env bash
set -Eeuo pipefail
source "$(dirname -- "${BASH_SOURCE[0]}")/lib.sh"
[[ $# == 0 || ( $# == 1 && "$1" == --mysql ) ]] || die 'Usage: bash stop.sh [--mysql]'
require_commands flock
lock_lab

# Stop the worker before its broker; retain PID files if graceful shutdown fails.
stop_process connect
stop_process kafka
if [[ "${1:-}" == --mysql ]]; then
    sudo service mysql stop
else
    printf 'MySQL is still running. Use bash stop.sh --mysql to stop it too.\n'
fi
printf 'Lab data and connector offsets have been preserved.\n'
