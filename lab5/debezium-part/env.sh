#!/usr/bin/env bash
# Source this file in each terminal before running the lab commands.
LAB_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
export LAB_DIR
export JAVA_HOME="/usr/lib/jvm/java-17-openjdk-$(dpkg --print-architecture)"
export KAFKA_HOME="$LAB_DIR/.runtime/kafka_2.13-3.9.0"
export KAFKA_HEAP_OPTS="-Xms256m -Xmx512m"
export PATH="$JAVA_HOME/bin:$KAFKA_HOME/bin:$PATH"

# Config paths for Kafka data and Connect plugins are relative to this directory.
cd -- "$LAB_DIR" || return 1
