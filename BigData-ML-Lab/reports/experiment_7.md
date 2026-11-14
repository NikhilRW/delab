# Experiment 7: Data Manipulation and Querying with Spark SQL and DataFrames

## Aim
To load student records with a defined Spark schema and query them with DataFrame and Spark SQL APIs.

## Course outcomes
CO2, CO4.

## Requirements and theory
PySpark 4.2.0, Python, Java, and a local machine with 4 GB RAM are sufficient. Spark DataFrames provide typed distributed tabular operations; temporary views expose the same data to SQL.

## Procedure
Create a local SparkSession, read the CSV with `SCHEMA`, derive a result column, perform select/filter/sort/group operations, register `students`, execute five SQL statements, and save JSON results.

## Complete program
The complete executable is [spark_sql.py](../experiment_7/spark_sql.py).

## Actual execution output
`total_records=525`; `average_attendance=72.72115384615384`; pass/fail counts were `0:96`, `1:424`, `2:5`. Average internal marks were `Fail=19.99009900990099`, `Pass=26.433962264150942`. Full query output is in `outputs/experiment_7/query_results.json`.

## Result and conclusion
All DataFrame operations and five Spark SQL queries executed successfully. The experiment demonstrates consistent SQL and DataFrame access to the same Spark dataset.

