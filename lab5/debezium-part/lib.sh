#!/usr/bin/env bash
# Shared helpers for setup.sh, start.sh, and stop.sh. Source, do not execute.

die() {
    printf 'ERROR: %s\n' "$*" >&2
    exit 1
}

[[ "$(uname -s)" == Linux ]] || die 'Run these scripts in the Ubuntu Codespaces terminal.'
command -v dpkg >/dev/null || die 'This setup requires Ubuntu and its dpkg package manager.'
source "$(dirname -- "${BASH_SOURCE[0]}")/env.sh"

lock_lab() {
    mkdir -p .runtime/logs .runtime/pids
    exec 9>.runtime/control.lock
    flock -n 9 || die 'Another setup/start/stop operation is running. Try again after it finishes.'
}

require_commands() {
    local command_name
    for command_name in "$@"; do
        command -v "$command_name" >/dev/null || die "Missing $command_name; run bash setup.sh first."
    done
}

port_is_open() {
    [[ -n "$(ss -H -lnt "sport = :$1")" ]]
}

require_free_port() {
    if port_is_open "$1"; then
        die "Port $1 is already listening. Stop the old service; this script will not replace it."
    fi
}

process_config() {
    case "$1" in
        kafka) printf '%s/config/server.properties' "$LAB_DIR" ;;
        connect) printf '%s/config/connect-distributed.properties' "$LAB_DIR" ;;
        *) return 1 ;;
    esac
}

managed_pid() {
    local name="$1" pid config
    [[ -f ".runtime/pids/$name.pid" ]] || return 1
    read -r pid < ".runtime/pids/$name.pid" || return 1
    [[ "$pid" =~ ^[1-9][0-9]*$ ]] || return 1
    kill -0 "$pid" 2>/dev/null || return 1
    config="$(process_config "$name")"
    # Do not mistake a stale/reused PID for one of our Java services.
    grep -Fqa -- "$config" "/proc/$pid/cmdline" 2>/dev/null || return 1
    printf '%s' "$pid"
}

stop_process() {
    local name="$1" pid deadline
    if ! pid="$(managed_pid "$name")"; then
        rm -f ".runtime/pids/$name.pid"
        printf '%s is not running under these scripts.\n' "$name"
        return 0
    fi
    printf 'Stopping %s (PID %s)...\n' "$name" "$pid"
    kill -TERM "$pid" || return 1
    deadline=$((SECONDS + 45))
    while managed_pid "$name" >/dev/null; do
        if ((SECONDS >= deadline)); then
            printf '%s has not stopped; inspect .runtime/logs/%s.log before retrying.\n' "$name" "$name" >&2
            return 1
        fi
        sleep 1
    done
    rm -f ".runtime/pids/$name.pid"
}

mysql_ready() {
    sudo mysql --connect-timeout=3 -Nse 'SELECT 1' >/dev/null 2>&1
}

wait_for() {
    local description="$1" seconds="$2" deadline
    shift 2
    deadline=$((SECONDS + seconds))
    until "$@"; do
        ((SECONDS < deadline)) || die "Timed out waiting for $description."
        sleep 2
    done
}
