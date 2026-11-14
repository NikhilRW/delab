# Big Data and ML Lab: Experiments 7, 8, 9 and 11

This project uses one deterministic student dataset for Spark SQL, data quality,
Spark MLlib, and an Airflow ETL pipeline. Experiment 10 is intentionally excluded.

## Requirements

- Python 3.11+ (the validation environment used Python 3.14.2)
- Java (the validation environment used Java 25; PySpark 4.2.0 worked)
- PySpark 4.2.x and NumPy
- Docker Compose for Experiment 9

Install dependencies with `python -m pip install -r requirements.txt`.

## Run locally

From this directory:

```bash
python scripts/generate_dataset.py
python experiment_7/spark_sql.py
python experiment_11/data_quality.py
python experiment_8/spark_mllib.py
python -m pytest -q
```

On Windows PowerShell, `.\run_all.ps1` runs the local experiments and tests and
checks Docker availability without changing unrelated Docker resources.

## Airflow

The Compose file is based on the Apache Airflow 3.4.0 quickstart services.
From `experiment_9/`, run `docker compose up airflow-init`, then
`docker compose up -d`. Open `http://localhost:8080`, enable
`student_performance_etl`, and trigger it manually. The DAG reads the project
data through the mounted `/opt/airflow/project` volume and writes
`outputs/experiment_9/cleaned_students.csv` and `students.sqlite`.

If Docker is not running, the pure-Python ETL helpers are covered by pytest; the
container-only DAG execution remains blocked until Docker Desktop/Engine is available.

## Outputs

- `outputs/experiment_7/`: Spark SQL JSON results and DataFrame directories
- `outputs/experiment_11/`: quality report, rejected records, and cleaned Spark CSV directory
- `outputs/experiment_8/`: model, predictions, metrics, and confusion matrix
- `outputs/experiment_9/`: Airflow CSV and SQLite outputs
- `reports/`: practical write-ups with actual validation outputs

