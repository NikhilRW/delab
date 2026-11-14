# Progress

## Completed

- Environment inspected: Python 3.14.2, Java 25, PySpark 4.2.0, Docker 29.8.0, Compose v5.5.1, about 5.8 GiB available memory and 8.1 GiB free disk.
- Deterministic dataset generated with 525 rows: 500 valid records and 25 single-defect records.
- Experiment 7 executed with Spark SQL and DataFrame APIs; JSON and DataFrame outputs saved.
- Experiment 11 executed: 25 rejected and 500 clean records; quality report saved.
- Experiment 8 executed with Spark MLlib logistic regression; model, predictions, metrics, and confusion matrix saved.
- Airflow Compose file validated and Airflow 3.4.0/PostgreSQL images pulled.
- Local automated tests pass: 5 passed, 1 skipped.
- Four practical reports, README, and PowerShell automation were created.

## Airflow status

The Docker daemon and Compose configuration are available. PostgreSQL is healthy,
but the `airflow-init` container remained in the metadata migration command without
completing, so DAG discovery and container-triggered execution were not claimed as
successful. Re-run `docker compose up airflow-init` from `experiment_9/` and inspect
`docker compose logs airflow-init`; no unrelated Docker resources were changed.

## Commands and fixes

- Initial ML run failed because NumPy was not installed; NumPy was added to
  `requirements.txt` and installed.
- Initial tests exposed that injected invalid rows reused original IDs. The generator
  was corrected so only the five duplicate defects reuse IDs; the other 20 defects
  have unique IDs.
- Final local command: `python -m pytest -q` -> `5 passed, 1 skipped`.

