# MySQL change data capture with Debezium — manual setup

Run MySQL, Kafka, and Kafka Connect directly inside your GitHub Codespaces
development environment. This lab does not use Docker Compose or containers for
these services. All processes must run in the **same Codespace**.

```text
MySQL :3306 -> Debezium MySQL plugin in Kafka Connect :8083 -> Kafka :9092
```

## Versions and files

Use Ubuntu 22.04/24.04, MySQL **8.0**, Java **17**, Kafka **3.9.0** (Scala 2.13),
and Debezium MySQL **3.0.8.Final**. These commands target the Ubuntu environment
in Codespaces, not a local Windows PowerShell terminal.

| File | Purpose |
| --- | --- |
| `env.sh` | Select Java/Kafka and switch to the lab working directory |
| `config/mysql.cnf` | Enable MySQL row-based binary logging |
| `init.sql` | Create `college.students`, a seed row, and the CDC database user |
| `config/server.properties` | Single-node Kafka KRaft configuration |
| `config/connect-distributed.properties` | Connect worker and plugin configuration |
| `register.json` | Register the `mysql-connector` Debezium source |
| `.runtime/` | Ignored downloads, plugins, cluster ID, and Kafka data |

Connections use `127.0.0.1`; the old container names `mysql` and `kafka` are no
longer needed. Kafka's controller uses port `9093`. Stop any previous lab stack
before starting this setup so ports `3306`, `8083`, `9092`, and `9093` are free.
Old container databases and Kafka volumes are not automatically migrated here.

## 1. Install prerequisites

From the repository in the Codespaces terminal:

```bash
cd "$(git rev-parse --show-toplevel)/lab5/debezium-part"
sudo apt-get update
sudo apt-get install -y openjdk-17-jdk mysql-server curl jq tar
source ./env.sh
java -version
mysql --version
```

Confirm Java 17 and MySQL 8.0. MariaDB is not a substitute for this connector;
these instructions also do not target MySQL 8.4. `sudo mysql` below uses the
Ubuntu package's local administrative socket authentication, not a root password.

**In every additional terminal**, initialize the same environment:

```bash
cd "$(git rev-parse --show-toplevel)/lab5/debezium-part"
source ./env.sh
```

Keep this working directory for all Kafka and Connect commands: the configuration
uses relative paths under `.runtime/`. The environment limits each Java process
to a 512 MiB heap for this small lab.

## 2. Download Kafka and the complete Debezium plugin

```bash
mkdir -p .runtime/downloads .runtime/plugins

curl -fL --retry 3 \
  https://archive.apache.org/dist/kafka/3.9.0/kafka_2.13-3.9.0.tgz \
  -o .runtime/downloads/kafka_2.13-3.9.0.tgz
tar -xzf .runtime/downloads/kafka_2.13-3.9.0.tgz -C .runtime

curl -fL --retry 3 \
  https://repo.maven.apache.org/maven2/io/debezium/debezium-connector-mysql/3.0.8.Final/debezium-connector-mysql-3.0.8.Final-plugin.tar.gz \
  -o .runtime/downloads/debezium-mysql-plugin.tar.gz
tar -xzf .runtime/downloads/debezium-mysql-plugin.tar.gz -C .runtime/plugins
```

Use the **plugin archive**, which includes its dependencies, rather than copying
only the connector JAR. Kafka's own distribution supplies the Connect worker.

## 3. Configure and initialize MySQL

```bash
sudo install -m 644 config/mysql.cnf /etc/mysql/mysql.conf.d/debezium.cnf
sudo service mysql restart
sudo mysql < init.sql

sudo mysql -e "SELECT VERSION(), @@server_id, @@log_bin, @@binlog_format, @@binlog_row_image;"
```

Expected: MySQL `8.0.x`, server ID `1`, binlog `1` (ON), format `ROW`, row image
`FULL`. `service` is used because Codespaces may not run systemd.

Check the account that Connect will use (enter `debezium` at the prompt):

```bash
mysql --protocol=TCP -h 127.0.0.1 -u debezium -p \
  -e "SELECT * FROM college.students;"
```

The example account/password is `debezium` / `debezium`, matching `register.json`.
`init.sql` is repeatable: it keeps existing table rows and resets only these lab
accounts' passwords and grants. If you already have a different `college.students`
schema, adapt the example SQL to it before running initialization.

## 4. Initialize Kafka storage once

```bash
if [ ! -f .runtime/kafka-data/meta.properties ]; then
  if [ ! -s .runtime/cluster-id ]; then
    "$KAFKA_HOME/bin/kafka-storage.sh" random-uuid > .runtime/cluster-id
  fi
  "$KAFKA_HOME/bin/kafka-storage.sh" format \
    --cluster-id "$(cat .runtime/cluster-id)" \
    --config config/server.properties
fi
```

Do this for a fresh installation, not on every restart. Keep the stored cluster
ID and Kafka data together. A storage error must be investigated rather than
fixed by deleting metadata or formatting over existing data.

## 5. Start Kafka — terminal A

After sourcing `env.sh`, run in the foreground:

```bash
"$KAFKA_HOME/bin/kafka-server-start.sh" config/server.properties
```

Leave this terminal open. From another initialized terminal, verify readiness:

```bash
timeout 20s "$KAFKA_HOME/bin/kafka-broker-api-versions.sh" \
  --bootstrap-server 127.0.0.1:9092
```

Continue when this returns broker/API information. `listeners` and
`advertised.listeners` both use reachable loopback addresses; no Docker DNS,
host-gateway mapping, or bridge firewall changes are needed.

## 6. Start Kafka Connect — terminal B

After sourcing `env.sh` in a second terminal:

```bash
"$KAFKA_HOME/bin/connect-distributed.sh" config/connect-distributed.properties
```

Leave it running. In a third initialized terminal, check readiness and plugin
discovery (retry after startup if the endpoint is not ready yet):

```bash
curl --fail --max-time 10 http://127.0.0.1:8083/ | jq .
curl --fail --max-time 10 http://127.0.0.1:8083/connector-plugins \
  | jq -e '.[] | select(.class == "io.debezium.connector.mysql.MySqlConnector")'
```

The first response should include a Kafka cluster ID. The second must show the
MySQL connector. If absent, check the plugin extraction under `.runtime/plugins`
and restart Connect after correcting it.

## 7. Register the connector — terminal C

```bash
curl --fail-with-body -X POST http://127.0.0.1:8083/connectors \
  -H 'Content-Type: application/json' \
  --data-binary @register.json

curl --fail http://127.0.0.1:8083/connectors/mysql-connector/status | jq .
```

Wait until both the connector and its task have state `RUNNING`. A successful
HTTP response alone does not mean the task is healthy; a `FAILED` task includes
a `trace` explaining the problem.

If registration returns HTTP `409` because the connector already exists, it is
persisted in Kafka. To apply an edited configuration without deleting it:

```bash
jq '.config' register.json | curl --fail-with-body -X PUT \
  http://127.0.0.1:8083/connectors/mysql-connector/config \
  -H 'Content-Type: application/json' --data-binary @-
```

The connector captures the `college` database. The existing topic prefix is
also `college`, so the students topic is **`college.college.students`**:
`<topic.prefix>.<database>.<table>`. Its internal schema history topic is
`schema-history.college`, separate from the public schema-change topic `college`.
The broker defaults to one partition so the schema history remains ordered.

## 8. Verify real change events

In an initialized terminal, consume the table topic after registration:

```bash
"$KAFKA_HOME/bin/kafka-console-consumer.sh" \
  --bootstrap-server 127.0.0.1:9092 \
  --topic college.college.students --from-beginning \
  --property print.key=true
```

In another terminal, make changes using a currently unused ID:

```bash
sudo mysql college <<'SQL'
INSERT INTO students (id, name, department) VALUES (1001, 'Nikhil', 'Computer Engineering');
UPDATE students SET department = 'Data Engineering' WHERE id = 1001;
DELETE FROM students WHERE id = 1001;
SQL
```

The consumer should show JSON events with `op` values `c` (insert), `u` (update),
and `d` (delete), plus a null-valued tombstone after deletion. Initial snapshot
rows use `op: "r"`. JSON schemas are disabled in the worker, so the event fields
are directly in the value rather than under a `payload` wrapper.

List topics if needed:

```bash
"$KAFKA_HOME/bin/kafka-topics.sh" --bootstrap-server 127.0.0.1:9092 --list
```

## Stop and restart

1. Stop consumers with **Ctrl+C**.
2. Stop **Connect** with **Ctrl+C** in terminal B; wait for shutdown.
3. Stop **Kafka** with **Ctrl+C** in terminal A; wait for shutdown.
4. Optionally stop MySQL with `sudo service mysql stop`.

On the next session, source `env.sh`, start MySQL with `sudo service mysql start`,
then start Kafka and Connect in that order. Do not reformat Kafka storage.
Connector configuration and offsets persist in Kafka; registration is not needed
again unless you change the configuration. Keep `.runtime/kafka-data` and the
MySQL data directory to retain state. Deleting just schema history or Kafka data
can make existing connector offsets unusable.

## Troubleshooting

- **Address already in use:** inspect `sudo ss -lntp` for ports 3306, 8083, 9092,
  and 9093; stop the old process before starting another instance.
- **Node assignment/metadata timeout:** first run the Kafka readiness command
  above. Confirm Kafka is running and all bootstrap/advertised endpoints use
  `127.0.0.1:9092`, then check terminal A's logs.
- **MySQL access denied:** run the TCP account check in step 3. The connector uses
  the dedicated account, not Ubuntu's socket-authenticated root account.
- **Binlog or snapshot failure:** inspect connector task `trace`, verify MySQL's
  global binlog settings and the account grants, and confirm MySQL is 8.0.
- **Plugin/class not found:** use Java 17, extract the full plugin archive, source
  `env.sh`, and restart Connect from the lab directory.
- **Working after stop/start:** allow time for the worker to recover its stored
  configuration and for the connector task to resume before testing writes.

There is no need to expose Kafka through the Codespaces browser Ports panel.
All lab commands run inside the Codespace. If viewing Connect's REST API from
your browser, forward only port `8083` with private visibility.

## References

- [Apache Kafka 3.9 quickstart](https://kafka.apache.org/39/getting-started/quickstart/)
- [Debezium 3.0 MySQL connector setup and privileges](https://debezium.io/documentation/reference/3.0/connectors/mysql.html)
- [Debezium 3.0.8.Final MySQL plugin distribution](https://repo.maven.apache.org/maven2/io/debezium/debezium-connector-mysql/3.0.8.Final/)
