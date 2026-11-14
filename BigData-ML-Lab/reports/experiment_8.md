# Experiment 8: Machine Learning with Spark MLlib

## Aim
To predict student pass/fail status with logistic regression without target leakage.

## Course outcomes
CO1, CO4.

## Requirements and theory
PySpark MLlib, NumPy, Python, and Java. Logistic regression estimates class probability from a linear combination of features. Accuracy, precision, recall, F1, and ROC-AUC measure complementary classification behavior.

## Procedure
Read the cleaned Spark dataset, assemble attendance, study hours, internal marks, and completed assignments, split with seed 42, train logistic regression, predict, evaluate, and save the model and predictions.

## Complete program
The complete executable is [spark_mllib.py](../experiment_8/spark_mllib.py). `passed` is not in `FEATURE_COLUMNS`.

## Actual execution output
The run used 426 training and 74 test records. Metrics were accuracy `0.7432432432432432`, precision `0.6911196911196911`, recall `0.7432432432432432`, F1 `0.6749236192714454`, and ROC-AUC `0.7291866028708135`. Full metrics and confusion matrix are in `outputs/experiment_8/metrics.json`.

## Result and conclusion
The model trained and predicted both classes with finite metrics in the valid range. The saved model and predictions can be reused for examination.

