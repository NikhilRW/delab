"""Spark SQL and DataFrame operations for Experiment 7."""

from __future__ import annotations

import json
from pathlib import Path

from pyspark.sql import SparkSession
from pyspark.sql.functions import avg, col, lit, when
from pyspark.sql.types import DoubleType, IntegerType, StringType, StructField, StructType


ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = str(ROOT / "data" / "students_raw.csv")
OUTPUT_DIR = ROOT / "outputs" / "experiment_7"
SCHEMA = StructType(
    [
        StructField("student_id", StringType(), True),
        StructField("attendance_pct", IntegerType(), True),
        StructField("study_hours_weekly", DoubleType(), True),
        StructField("internal_marks", IntegerType(), True),
        StructField("assignments_completed", IntegerType(), True),
        StructField("passed", IntegerType(), True),
    ]
)


def run(spark: SparkSession | None = None) -> dict[str, object]:
    owns_spark = spark is None
    spark = spark or SparkSession.builder.appName("Experiment7-SparkSQL").master("local[2]").getOrCreate()
    try:
        students = spark.read.option("header", True).schema(SCHEMA).csv(RAW_PATH)
        result = students.withColumn(
            "result", when(col("passed") == 1, lit("Pass")).otherwise(lit("Fail"))
        )
        dataframes = {
            "selected": result.select("student_id", "attendance_pct", "passed").limit(10),
            "filtered": result.filter(col("attendance_pct") > 75).orderBy(col("attendance_pct").desc()).limit(10),
            "grouped": result.groupBy("passed").count().orderBy("passed"),
            "derived": result.select("student_id", (col("internal_marks") / 40 * 100).alias("marks_percentage")).limit(10),
        }
        result.createOrReplaceTempView("students")
        queries = {
            "total_records": "SELECT COUNT(*) AS total_records FROM students",
            "average_attendance": "SELECT AVG(attendance_pct) AS average_attendance FROM students",
            "count_by_result": "SELECT passed, COUNT(*) AS count FROM students GROUP BY passed ORDER BY passed",
            "attendance_above_75": "SELECT student_id, attendance_pct FROM students WHERE attendance_pct > 75 ORDER BY attendance_pct DESC",
            "average_marks_by_result": "SELECT result, AVG(internal_marks) AS average_internal_marks FROM students GROUP BY result ORDER BY result",
        }
        query_results = {}
        for name, query in queries.items():
            frame = spark.sql(query)
            query_results[name] = [row.asDict() for row in frame.collect()]
            frame.show(20, truncate=False)
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        with (OUTPUT_DIR / "query_results.json").open("w", encoding="utf-8") as handle:
            json.dump(query_results, handle, indent=2, default=str)
        for name, frame in dataframes.items():
            frame.write.mode("overwrite").json(str(OUTPUT_DIR / name))
        return query_results
    finally:
        if owns_spark:
            spark.stop()


if __name__ == "__main__":
    run()

