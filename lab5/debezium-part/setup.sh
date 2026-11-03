#!/usr/bin/env bash
set -Eeuo pipefail
source "$(dirname -- "${BASH_SOURCE[0]}")/lib.sh"

source /etc/os-release
[[ "$ID" == ubuntu && ( "$VERSION_ID" == 22.04 || "$VERSION_ID" == 24.04 ) ]] \
    || die 'Supported setup: Ubuntu 22.04 or 24.04 with MySQL 8.0.'
require_commands sudo flock ss curl tar
lock_lab

for port in 8083 9092 9093; do
    require_free_port "$port"
done

printf 'Installing Java 17, MySQL 8.0, and command-line tools...\n'
sudo -v
sudo apt-get update
sudo env DEBIAN_FRONTEND=noninteractive apt-get install -y \
    openjdk-17-jdk mysql-server curl jq tar iproute2 util-linux ca-certificates
[[ -x "$JAVA_HOME/bin/java" ]] || die "Java 17 was not installed at $JAVA_HOME."
mysql --version | grep -Eq 'Ver 8\.0\.' || die 'MySQL 8.0 is required; MariaDB/MySQL 8.4 are not supported by this setup.'

mkdir -p .runtime/downloads .runtime/plugins

download() {
    local url="$1" archive="$2"
    # Only promote a complete, readable archive to the download cache.
    if [[ -f "$archive" ]] && tar -tzf "$archive" >/dev/null 2>&1; then
        return
    fi
    curl --fail --location --retry 3 --connect-timeout 15 \
        "$url" -o "$archive.part"
    tar -tzf "$archive.part" >/dev/null
    mv -- "$archive.part" "$archive"
}

printf 'Preparing Kafka 3.9.0...\n'
if [[ ! -x "$KAFKA_HOME/bin/kafka-server-start.sh" ]]; then
    download 'https://archive.apache.org/dist/kafka/3.9.0/kafka_2.13-3.9.0.tgz' \
        .runtime/downloads/kafka_2.13-3.9.0.tgz
    tar -xzf .runtime/downloads/kafka_2.13-3.9.0.tgz -C .runtime
fi

printf 'Preparing Debezium MySQL 3.0.8.Final...\n'
PLUGIN_JAR='.runtime/plugins/debezium-connector-mysql/debezium-connector-mysql-3.0.8.Final.jar'
if [[ ! -f "$PLUGIN_JAR" || ! -f .runtime/mysql-plugin-installed ]]; then
    download 'https://repo.maven.apache.org/maven2/io/debezium/debezium-connector-mysql/3.0.8.Final/debezium-connector-mysql-3.0.8.Final-plugin.tar.gz' \
        .runtime/downloads/debezium-mysql-plugin.tar.gz
    tar -xzf .runtime/downloads/debezium-mysql-plugin.tar.gz -C .runtime/plugins
    [[ -f "$PLUGIN_JAR" ]] || die 'The MySQL plugin archive did not contain the expected connector JAR.'
    touch .runtime/mysql-plugin-installed
fi

printf 'Configuring the native MySQL server (this restarts MySQL)...\n'
sudo install -m 644 config/mysql.cnf /etc/mysql/mysql.conf.d/debezium.cnf
sudo service mysql restart
wait_for MySQL 60 mysql_ready
sudo mysql < init.sql
settings="$(sudo mysql -Nse "SELECT VERSION() LIKE '8.0.%' AND @@global.server_id=1 AND @@global.log_bin=1 AND @@global.binlog_format='ROW' AND @@global.binlog_row_image='FULL';")"
[[ "$settings" == 1 ]] || die 'MySQL version/binlog settings do not match config/mysql.cnf.'

printf 'Initializing Kafka storage if this is a fresh installation...\n'
if [[ ! -f .runtime/kafka-data/meta.properties ]]; then
    if [[ ! -s .runtime/cluster-id ]]; then
        "$KAFKA_HOME/bin/kafka-storage.sh" random-uuid > .runtime/cluster-id
    fi
    "$KAFKA_HOME/bin/kafka-storage.sh" format \
        --cluster-id "$(cat .runtime/cluster-id)" \
        --config "$LAB_DIR/config/server.properties"
fi

printf '\nSetup complete. Start the lab with:\n  bash "%s/start.sh"\n' "$LAB_DIR"
printf 'MySQL is running. Kafka and Connect will be started by start.sh.\n'
