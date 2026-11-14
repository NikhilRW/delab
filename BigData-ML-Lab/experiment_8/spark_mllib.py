"""Logistic-regression classification with Spark MLlib."""

from __future__ import annotations

import json
import math
import shutil
from pathlib import Path

from pyspark.ml import Pipeline
from pyspark.ml.classification import LogisticRegression
from pyspark.ml.evaluation import MulticlassClassificationEvaluator, BinaryClassificationEvaluator
from pyspark.ml.feature import VectorAssembler
from pyspark.sql import SparkSession


ROOT = Path(__file__).resolve().parents[1]
CLEAN_PATH = str(ROOT / "outputs" / "experiment_11" / "cleaned_students")
OUTPUT_DIR = ROOT / "outputs" / "experiment_8"
FEATURE_COLUMNS = ["attendance_pct", "study_hours_weekly", "internal_marks", "assignments_completed"]


def run(spark: SparkSession | None = None) -> dict[str, object]:
    owns_spark = spark is None
    spark = spark or SparkSession.builder.appName("Experiment8-SparkMLlib").master("local[2]").getOrCreate()
    try:
        data = spark.read.option("header", True).option("inferSchema", True).csv(CLEAN_PATH)
        assembler = VectorAssembler(inputCols=FEATURE_COLUMNS, outputCol="features")
        classifier = LogisticRegression(featuresCol="features", labelCol="passed", predictionCol="prediction")
        pipeline = Pipeline(stages=[assembler, classifier])
        train, test = data.randomSplit([0.8, 0.2], seed=42)
        model = pipeline.fit(train)
        predictions = model.transform(test).cache()
        evaluator = MulticlassClassificationEvaluator(labelCol="passed", predictionCol="prediction")
        metrics = {
            "accuracy": evaluator.evaluate(predictions, {evaluator.metricName: "accuracy"}),
            "precision": evaluator.evaluate(predictions, {evaluator.metricName: "weightedPrecision"}),
            "recall": evaluator.evaluate(predictions, {evaluator.metricName: "weightedRecall"}),
            "f1": evaluator.evaluate(predictions, {evaluator.metricName: "f1"}),
            "roc_auc": BinaryClassificationEvaluator(labelCol="passed", rawPredictionCol="rawPrediction", metricName="areaUnderROC").evaluate(predictions),
        }
        if not all(math.isfinite(value) and 0 <= value <= 1 for value in metrics.values()):
            raise RuntimeError(f"Non-finite or out-of-range evaluation metrics: {metrics}")
        confusion_matrix = [
            row.asDict() for row in predictions.groupBy("passed", "prediction").count().orderBy("passed", "prediction").collect()
        ]
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        predictions.select("student_id", "passed", "prediction", "probability").write.mode("overwrite").json(str(OUTPUT_DIR / "predictions"))
        with (OUTPUT_DIR / "metrics.json").open("w", encoding="utf-8") as handle:
            json.dump({"train_records": train.count(), "test_records": test.count(), "metrics": metrics, "confusion_matrix": confusion_matrix}, handle, indent=2)
        model.write().overwrite().save(str(OUTPUT_DIR / "model"))
        predictions.show(20, truncate=False)
        return {"train_records": train.count(), "test_records": test.count(), "metrics": metrics, "confusion_matrix": confusion_matrix}
    finally:
        if owns_spark:
            spark.stop()


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))

