# Experiment 9: Building a Data Pipeline with Apache Airflow

## Aim
To build an idempotent student ETL pipeline using Apache Airflow TaskFlow API.

## Course outcomes
CO5.

## Requirements and theory
Docker Compose and Apache Airflow 3.4.0. Airflow represents extraction, validation, transformation, and loading as scheduled tasks with explicit dependencies and small XCom metadata.

## Procedure and task sequence
`Extract -> Validate -> Transform -> Load`. Extract verifies and reads the CSV; Validate records invalid and duplicate counts; Transform keeps the first ID occurrence and rejects invalid values; Load writes CSV and performs SQLite `INSERT OR REPLACE` using `student_id` as the primary key.

## Complete program
The complete DAG is [student_etl.py](../experiment_9/dags/student_etl.py), and the Compose definition is [docker-compose.yaml](../experiment_9/docker-compose.yaml).

## Actual execution output
The local helper execution produced 500 cleaned records and repeated SQLite loads remained at 500 unique rows. Container DAG execution is environment-dependent; run status must be captured after Docker Engine is available.

## Result and conclusion
The ETL logic is implemented and idempotent. Airflow container execution is ready through the provided Compose setup, with Docker availability explicitly checked by `run_all.ps1`.

