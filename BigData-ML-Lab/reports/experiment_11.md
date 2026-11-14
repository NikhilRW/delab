# Experiment 11: Implementing Data Quality Checks

## Aim
To detect, report, and remove invalid student records using PySpark.

## Course outcomes
CO6.

## Requirements and theory
PySpark, Python, Java, and local storage. Data-quality validation checks nulls, duplicates, types, ranges, and labels before a clean dataset is published.

## Procedure
Read the typed CSV, preserve input order, mark issue categories, keep the first ID occurrence, reject invalid rows, write the cleaned Spark CSV directory, rejected records, and JSON report.

## Complete program
The complete executable is [data_quality.py](../experiment_11/data_quality.py).

## Actual execution output
Input records: `525`; rejected: `25`; cleaned: `500`; remaining duplicate IDs: `0`; remaining invalid records: `0`. Issue counts were missing `5`, duplicate records `5`, out-of-range values `10`, invalid labels `5`, and invalid data types `0`. The actual report is `outputs/experiment_11/quality_report.json`.

## Result and conclusion
All deliberately defective records were rejected without replacement values, and the cleaned Spark dataset contains 500 valid unique students.

