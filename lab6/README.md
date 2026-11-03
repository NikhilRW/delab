# Lab 6: Scalable Data Processing with Spark RDDs

## Aim

Implement `map`, `filter`, `reduce`, and `aggregate` using Spark RDDs on a large
synthetic dataset.

The script generates **1,000,000 transactions**, with amounts repeating from 1 to
1000. Data is generated across four partitions instead of building a large list
in Python. Spark runs locally with two worker threads, suitable for Codespaces.

## Install — Codespaces terminal

Requires Python 3.10+ and Java 17.

```bash
cd "$(git rev-parse --show-toplevel)/lab6"
sudo apt-get update
sudo apt-get install -y openjdk-17-jdk python3-venv
export JAVA_HOME="/usr/lib/jvm/java-17-openjdk-$(dpkg --print-architecture)"
export PATH="$JAVA_HOME/bin:$PATH"

python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## Run

```bash
python rdd_operations.py
```

To change the dataset size:

```bash
python rdd_operations.py --rows 5000000
```

In a new terminal, return to `lab6`, activate `.venv`, and export `JAVA_HOME` and
`PATH` as above before running the script.

## Operations

| Operation | Demonstration |
| --- | --- |
| `map` | Extract the amount from each transaction |
| `filter` | Keep amounts greater than 500 |
| `reduce` | Add all amounts to calculate the total |
| `aggregate` | Calculate count and sum together, then derive the average |

`map` and `filter` are lazy transformations. `take`, `count`, `reduce`, and
`aggregate` are actions that trigger computation. `cache()` allows the amounts
RDD to be reused by these actions. Only five sample values and summary results
are returned to the driver; the full dataset is not collected.

## Expected output — default 1,000,000 rows

Spark also prints startup messages; the lab results are:

```text
Records: 1000000
Partitions: 4
MAP - first 5 amounts: [1, 2, 3, 4, 5]
FILTER - amounts > 500: 500000
REDUCE - total amount: 500500000
AGGREGATE - count: 1000000, sum: 500500000
Average amount: 500.50
```

The script stops Spark automatically when it finishes. This is a local-mode
demonstration of partitioned RDD processing, not a multi-machine cluster.
