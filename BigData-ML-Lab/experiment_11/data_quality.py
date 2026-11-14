"""Detect and remove the deliberately defective records from the raw dataset."""

from __future__ import annotations

import json
from pathlib import Path

from pyspark.sql import DataFrame, SparkSession, Window
from pyspark.sql.functions import col, count, lit, row_number, when
from pyspark.sql.types import DoubleType, IntegerType, StringType, StructField, StructType


ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = str(ROOT / "data" / "students_raw.csv")
OUTPUT_DIR = ROOT / "outputs" / "experiment_11"
CLEAN_PATH = str(OUTPUT_DIR / "cleaned_students")
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
REQUIRED = ["student_id", "attendance_pct", "study_hours_weekly", "internal_marks", "assignments_completed", "passed"]


def quality_frames(raw: DataFrame) -> tuple[DataFrame, DataFrame]:
    indexed = raw.rdd.zipWithIndex().toDF(["record", "_input_order"]).select("record.*", "_input_order")
    duplicate_ids = indexed.groupBy("student_id").count().where((col("student_id").isNotNull()) & (col("count") > 1)).select("student_id")
    marked = (
        indexed.withColumn("_duplicate", col("student_id").isin([row.student_id for row in duplicate_ids.collect()]))
        .withColumn("_missing", col("student_id").isNull() | col("attendance_pct").isNull() | col("study_hours_weekly").isNull() | col("internal_marks").isNull() | col("assignments_completed").isNull() | col("passed").isNull())
        .withColumn("_range", (col("attendance_pct") < 0) | (col("attendance_pct") > 100) | (col("study_hours_weekly") < 0) | (col("study_hours_weekly") > 30) | (col("internal_marks") < 0) | (col("internal_marks") > 40) | (col("assignments_completed") < 0) | (col("assignments_completed") > 10))
        .withColumn("_label", ~col("passed").isin([0, 1]))
    )
    window = Window.partitionBy("student_id").orderBy("_input_order")
    marked = marked.withColumn("_not_first_duplicate", col("_duplicate") & (row_number().over(window) > 1))
    invalid = marked.filter(col("_missing") | col("_range") | col("_label") | col("_not_first_duplicate"))
    clean = marked.filter(~(col("_missing") | col("_range") | col("_label") | col("_not_first_duplicate"))).select(*REQUIRED)
    return clean, invalid


def run(spark: SparkSession | None = None) -> dict[str, object]:
    owns_spark = spark is None
    spark = spark or SparkSession.builder.appName("Experiment11-DataQuality").master("local[2]").getOrCreate()
    try:
        raw = spark.read.option("header", True).schema(SCHEMA).csv(RAW_PATH)
        clean, invalid = quality_frames(raw)
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        clean.write.mode("overwrite").option("header", True).csv(CLEAN_PATH)
        issue_counts = {
            "missing_values": invalid.filter(col("_missing")).count(),
            "duplicate_student_ids": invalid.filter(col("_not_first_duplicate")).count(),
            "out_of_range_values": invalid.filter(col("_range")).count(),
            "invalid_pass_fail_labels": invalid.filter(col("_label")).count(),
            "invalid_data_types": invalid.filter(lit(False)).count(),
        }
        report = {
            "input_records": raw.count(),
            "rejected_records": invalid.count(),
            "valid_cleaned_records": clean.count(),
            "remaining_duplicate_ids": clean.groupBy("student_id").count().where(col("count") > 1).count(),
            "remaining_invalid_records": clean.filter((col("attendance_pct") < 0) | (col("attendance_pct") > 100) | (col("study_hours_weekly") < 0) | (col("study_hours_weekly") > 30) | (col("internal_marks") < 0) | (col("internal_marks") > 40) | (col("assignments_completed") < 0) | (col("assignments_completed") > 10) | ~col("passed").isin([0, 1])).count(),
            "issue_counts": issue_counts,
        }
        with (OUTPUT_DIR / "quality_report.json").open("w", encoding="utf-8") as handle:
            json.dump(report, handle, indent=2)
        invalid.select("student_id", *REQUIRED, "_missing", "_range", "_label", "_not_first_duplicate").write.mode("overwrite").option("header", True).csv(str(OUTPUT_DIR / "rejected_records"))
        return report
    finally:
        if owns_spark:
            spark.stop()


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))

