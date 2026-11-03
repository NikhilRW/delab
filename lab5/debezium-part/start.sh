#!/usr/bin/env bash
set -Eeuo pipefail
source "$(dirname -- "${BASH_SOURCE[0]}")/lib.sh"
require_commands sudo flock ss curl jq timeout nohup
lock_lab

[[ -x "$JAVA_HOME/bin/java" && -x "$KAFKA_HOME/bin/kafka-server-start.sh" ]] \
    || die 'Java/Kafka is missing. Run bash setup.sh first.'
[[ -f .runtime/kafka-data/meta.properties ]] || die 'Kafka storage is not initialized. Run bash setup.sh first.'
[[ -f .runtime/plugins/debezium-connector-mysql/debezium-connector-mysql-3.0.8.Final.jar ]] \
    || die 'The Debezium MySQL plugin is missing. Run bash setup.sh first.'

# Check conflicts before starting anything; never adopt an unrelated/manual process.
if ! managed_pid kafka >/dev/null; then
    require_free_port 9092
    require_free_port 9093
fi
if ! managed_pid connect >/dev/null; then
    require_free_port 8083
fi

STARTED_KAFKA=0
STARTED_CONNECT=0
cleanup_on_failure() {
    local result=$?
    if ((result != 0)); then
        printf '\nStartup failed. Last service log lines:\n' >&2
        for name in kafka connect; do
            if [[ -f ".runtime/logs/$name.log" ]]; then
                printf '\n--- %s ---\n' "$name" >&2
                tail -n 25 ".runtime/logs/$name.log" >&2
            fi
        done
        # Only stop processes created by this invocation; keep previously running ones.
        if ((STARTED_CONNECT)); then stop_process connect || true; fi
        if ((STARTED_KAFKA)); then stop_process kafka || true; fi
    fi
}
trap cleanup_on_failure EXIT

sudo -v
sudo service mysql start
wait_for MySQL 60 mysql_ready
sudo mysql -e 'SELECT id, name, department FROM college.students LIMIT 1' >/dev/null \
    || die 'The lab database is missing or has a different schema. Run setup.sh or check init.sql.'

launch() {
    local name="$1" command_path="$2" config="$3"
    if managed_pid "$name" >/dev/null; then
        printf '%s is already running.\n' "$name"
        return
    fi
    printf 'Starting %s...\n' "$name"
    # Close the operation lock in children so it is not held for their lifetime.
    nohup "$command_path" "$config" >> ".runtime/logs/$name.log" 2>&1 < /dev/null 9>&- &
    printf '%s\n' "$!" > ".runtime/pids/$name.pid"
    case "$name" in
        kafka) STARTED_KAFKA=1 ;;
        connect) STARTED_CONNECT=1 ;;
    esac
}

kafka_ready() {
    timeout 10s "$KAFKA_HOME/bin/kafka-broker-api-versions.sh" \
        --bootstrap-server 127.0.0.1:9092 >/dev/null 2>&1
}

connect_ready() {
    curl --fail --silent --max-time 5 http://127.0.0.1:8083/ >/dev/null
}

wait_service() {
    local name="$1" seconds="$2" probe="$3" deadline
    deadline=$((SECONDS + seconds))
    while true; do
        managed_pid "$name" >/dev/null || die "$name exited. See .runtime/logs/$name.log."
        if "$probe"; then return; fi
        ((SECONDS < deadline)) || die "Timed out waiting for $name. See .runtime/logs/$name.log."
        sleep 2
    done
}

launch kafka "$KAFKA_HOME/bin/kafka-server-start.sh" "$LAB_DIR/config/server.properties"
wait_service kafka 180 kafka_ready
launch connect "$KAFKA_HOME/bin/connect-distributed.sh" "$LAB_DIR/config/connect-distributed.properties"
wait_service connect 180 connect_ready

curl --fail --silent --show-error --max-time 30 http://127.0.0.1:8083/connector-plugins \
    | jq -e '.[] | select(.class == "io.debezium.connector.mysql.MySqlConnector")' >/dev/null \
    || die 'Connect did not discover the MySQL plugin. See .runtime/logs/connect.log.'

printf 'Creating/updating mysql-connector using register.json...\n'
jq '.config' register.json | curl --fail-with-body --silent --show-error --max-time 30 \
    -X PUT http://127.0.0.1:8083/connectors/mysql-connector/config \
    -H 'Content-Type: application/json' --data-binary @- >/dev/null

deadline=$((SECONDS + 120))
while true; do
    managed_pid connect >/dev/null || die 'Connect exited during connector startup.'
    status="$(curl --fail --silent --show-error --max-time 5 \
        http://127.0.0.1:8083/connectors/mysql-connector/status)" || status='{}'
    if jq -e '.connector.state == "FAILED" or any(.tasks[]?; .state == "FAILED")' <<< "$status" >/dev/null; then
        jq . <<< "$status" >&2
        die 'The connector/task failed; its trace is shown above.'
    fi
    if jq -e '.connector.state == "RUNNING" and (.tasks | length > 0) and all(.tasks[]; .state == "RUNNING")' <<< "$status" >/dev/null; then
        break
    fi
    ((SECONDS < deadline)) || die 'Timed out waiting for the connector task to become RUNNING.'
    sleep 2
done

printf '\nReady: MySQL :3306, Kafka :9092, Connect :8083, mysql-connector RUNNING.\n'
printf 'Logs: %s/.runtime/logs/{kafka,connect}.log\n' "$LAB_DIR"
printf 'Check status: curl -s http://127.0.0.1:8083/connectors/mysql-connector/status | jq .\n'
printf 'Stop Kafka/Connect: bash "%s/stop.sh"\n' "$LAB_DIR"
printf 'Also stop MySQL:    bash "%s/stop.sh" --mysql\n' "$LAB_DIR"
