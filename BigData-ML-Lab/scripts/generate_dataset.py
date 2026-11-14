"""Generate the deterministic raw dataset used by all laboratory experiments."""

from __future__ import annotations

import csv
import random
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "students_raw.csv"
FIELDNAMES = [
    "student_id",
    "attendance_pct",
    "study_hours_weekly",
    "internal_marks",
    "assignments_completed",
    "passed",
]


def generate_records() -> list[dict[str, object]]:
    rng = random.Random(42)
    records: list[dict[str, object]] = []
    for number in range(1, 501):
        attendance = rng.randint(45, 100)
        study_hours = round(rng.uniform(2, 30), 1)
        marks = rng.randint(10, 40)
        assignments = rng.randint(2, 10)
        score = (
            0.035 * attendance
            + 0.08 * study_hours
            + 0.11 * marks
            + 0.12 * assignments
            + rng.gauss(0, 1.8)
        )
        passed = int(score >= 5.2)
        records.append(
            {
                "student_id": f"S{number:04d}",
                "attendance_pct": attendance,
                "study_hours_weekly": study_hours,
                "internal_marks": marks,
                "assignments_completed": assignments,
                "passed": passed,
            }
        )

    defects: list[dict[str, object]] = []
    defects.extend({**records[index]} for index in range(5))
    for offset, index in enumerate(range(5, 25), start=501):
        defect = {**records[index], "student_id": f"S{offset:04d}"}
        if offset <= 505:
            defect["attendance_pct"] = ""
        elif offset <= 510:
            defect["attendance_pct"] = 101 + offset - 506
        elif offset <= 515:
            defect["study_hours_weekly"] = -(offset - 510)
        else:
            defect["passed"] = 2
        defects.append(defect)
    return records + defects


def main() -> None:
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    records = generate_records()
    with DATA_PATH.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(records)
    print(f"Wrote {len(records)} records to {DATA_PATH}")


if __name__ == "__main__":
    main()

