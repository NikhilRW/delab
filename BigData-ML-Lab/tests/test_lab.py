import csv
import importlib.util
import json
import sqlite3
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_dataset_shape_and_defects():
    with (ROOT / "data" / "students_raw.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 525
    assert set(rows[0]) == {
        "student_id", "attendance_pct", "study_hours_weekly",
        "internal_marks", "assignments_completed", "passed",
    }
    assert len(rows) - len({row["student_id"] for row in rows}) == 5
    assert sum(row["attendance_pct"] == "" for row in rows) == 5
    assert sum(row["attendance_pct"] != "" and int(row["attendance_pct"]) > 100 for row in rows) == 5
    assert sum(float(row["study_hours_weekly"] or 0) < 0 for row in rows) == 5
    assert sum(row["passed"] not in {"0", "1"} for row in rows) == 5


def test_quality_report_and_clean_dataset():
    report = json.loads((ROOT / "outputs/experiment_11/quality_report.json").read_text())
    assert report["input_records"] == 525
    assert report["rejected_records"] == 25
    assert report["valid_cleaned_records"] == 500
    assert report["remaining_duplicate_ids"] == 0
    assert report["remaining_invalid_records"] == 0
    assert report["issue_counts"]["duplicate_student_ids"] == 5
    assert report["issue_counts"]["missing_values"] == 5
    assert report["issue_counts"]["out_of_range_values"] == 10
    assert report["issue_counts"]["invalid_pass_fail_labels"] == 5


def test_sql_aggregation_results():
    results = json.loads((ROOT / "outputs/experiment_7/query_results.json").read_text())
    assert results["total_records"][0]["total_records"] == 525
    assert sum(row["count"] for row in results["count_by_result"]) == 525
    assert len(results["average_marks_by_result"]) == 2


def test_mllib_metrics_and_feature_exclusion():
    metrics = json.loads((ROOT / "outputs/experiment_8/metrics.json").read_text())
    assert 0 < metrics["train_records"] < 500
    assert 0 < metrics["test_records"] < 500
    assert all(0 <= value <= 1 for value in metrics["metrics"].values())
    ml = load_module("spark_mllib", ROOT / "experiment_8/spark_mllib.py")
    assert "passed" not in ml.FEATURE_COLUMNS
    assert len(metrics["confusion_matrix"]) >= 2


def test_airflow_transformation_and_idempotent_load(tmp_path):
    etl = load_module("student_etl", ROOT / "experiment_9/dags/student_etl.py")
    etl.OUTPUT_DIR = tmp_path
    etl.CSV_OUTPUT = tmp_path / "cleaned_students.csv"
    etl.SQLITE_OUTPUT = tmp_path / "students.sqlite"
    metadata = etl.extract()
    validated = etl.validate(metadata)
    transformed = etl.transform(validated)
    first = etl.load(transformed)
    second = etl.load(transformed)
    assert validated["records"] == 525
    assert transformed["cleaned_records"] == 500
    assert first["loaded_records"] == second["loaded_records"] == 500
    with sqlite3.connect(etl.SQLITE_OUTPUT) as connection:
        assert connection.execute("SELECT COUNT(*) FROM students").fetchone()[0] == 500


def test_airflow_dag_structure_when_installed():
    etl = load_module("student_etl_dag", ROOT / "experiment_9/dags/student_etl.py")
    if etl.dag is None:
        pytest.skip("Airflow is not installed; DAG is validated by docker-compose execution")
    dag_object = etl.student_performance_etl()
    assert dag_object.task_dict["extract_task"] >> dag_object.task_dict["validate_task"]
    assert dag_object.task_dict["validate_task"] >> dag_object.task_dict["transform_task"]
    assert dag_object.task_dict["transform_task"] >> dag_object.task_dict["load_task"]

