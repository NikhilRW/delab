"""Airflow TaskFlow ETL for the student performance dataset."""

from __future__ import annotations

import csv
import json
import logging
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from airflow.sdk import dag, task
except ImportError:  # Allows helper functions to be tested without Airflow installed.
    dag = task = None


ROOT = Path(__file__).resolve().parents[2]
RAW_PATH = Path(__import__("os").environ.get("STUDENT_RAW_PATH", ROOT / "data" / "students_raw.csv"))
OUTPUT_DIR = Path(__import__("os").environ.get("STUDENT_ETL_OUTPUT", ROOT / "outputs" / "experiment_9"))
CSV_OUTPUT = OUTPUT_DIR / "cleaned_students.csv"
SQLITE_OUTPUT = OUTPUT_DIR / "students.sqlite"
FIELDS = ["student_id", "attendance_pct", "study_hours_weekly", "internal_marks", "assignments_completed", "passed"]


def extract() -> dict[str, Any]:
    if not RAW_PATH.exists():
        raise FileNotFoundError(f"Raw dataset does not exist: {RAW_PATH}")
    with RAW_PATH.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    logging.info("Extracted %d records from %s", len(rows), RAW_PATH)
    return {"path": str(RAW_PATH), "records": len(rows)}


def validate(metadata: dict[str, Any]) -> dict[str, Any]:
    with Path(metadata["path"]).open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    seen: set[str] = set()
    invalid = 0
    duplicate = 0
    for row in rows:
        if row["student_id"] in seen:
            duplicate += 1
        seen.add(row["student_id"])
        try:
            valid = (
                row["student_id"]
                and 0 <= int(row["attendance_pct"]) <= 100
                and 0 <= float(row["study_hours_weekly"]) <= 30
                and 0 <= int(row["internal_marks"]) <= 40
                and 0 <= int(row["assignments_completed"]) <= 10
                and int(row["passed"]) in (0, 1)
            )
        except (TypeError, ValueError):
            valid = False
        invalid += not valid
    return {**metadata, "invalid_records": invalid, "duplicate_records": duplicate}


def transform(metadata: dict[str, Any]) -> dict[str, Any]:
    with Path(metadata["path"]).open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    cleaned: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in rows:
        if row["student_id"] in seen:
            continue
        try:
            candidate = {
                "student_id": row["student_id"],
                "attendance_pct": int(row["attendance_pct"]),
                "study_hours_weekly": float(row["study_hours_weekly"]),
                "internal_marks": int(row["internal_marks"]),
                "assignments_completed": int(row["assignments_completed"]),
                "passed": int(row["passed"]),
            }
        except (TypeError, ValueError):
            continue
        if (
            not candidate["student_id"]
            or not 0 <= candidate["attendance_pct"] <= 100
            or not 0 <= candidate["study_hours_weekly"] <= 30
            or not 0 <= candidate["internal_marks"] <= 40
            or not 0 <= candidate["assignments_completed"] <= 10
            or candidate["passed"] not in (0, 1)
        ):
            continue
        seen.add(candidate["student_id"])
        cleaned.append(candidate)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with CSV_OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(cleaned)
    return {**metadata, "cleaned_path": str(CSV_OUTPUT), "cleaned_records": len(cleaned)}


def load(metadata: dict[str, Any]) -> dict[str, Any]:
    with CSV_OUTPUT.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    with sqlite3.connect(SQLITE_OUTPUT) as connection:
        connection.execute("CREATE TABLE IF NOT EXISTS students (student_id TEXT PRIMARY KEY, attendance_pct INTEGER, study_hours_weekly REAL, internal_marks INTEGER, assignments_completed INTEGER, passed INTEGER)")
        connection.executemany(
            "INSERT OR REPLACE INTO students VALUES (?, ?, ?, ?, ?, ?)",
            [tuple(row[field] for field in FIELDS) for row in rows],
        )
        count = connection.execute("SELECT COUNT(*) FROM students").fetchone()[0]
    logging.info("Loaded %d unique records into %s", count, SQLITE_OUTPUT)
    return {**metadata, "sqlite_path": str(SQLITE_OUTPUT), "loaded_records": count}


if dag is not None:
    @dag(
        dag_id="student_performance_etl",
        schedule=None,
        start_date=datetime(2024, 1, 1, tzinfo=timezone.utc),
        catchup=False,
        tags=["student", "experiment-9"],
    )
    def student_performance_etl():
        @task
        def extract_task():
            return extract()

        @task
        def validate_task(metadata):
            return validate(metadata)

        @task
        def transform_task(metadata):
            return transform(metadata)

        @task
        def load_task(metadata):
            return load(metadata)

        load_task(transform_task(validate_task(extract_task())))

    student_performance_etl()

