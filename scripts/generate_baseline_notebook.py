"""Generate the reproducible MarketLens classification baseline notebook."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "notebooks" / "02_baseline.ipynb"


def markdown(source: str) -> dict:
    return {"cell_type": "markdown", "metadata": {}, "source": source}


def code(source: str) -> dict:
    return {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": source}


cells = [
    markdown('''# 02 — Базова модель класифікації

## Мета

Передбачити один із трьох класів для наступних 5 торгових днів:

- `outperform`: дохідність MSFT перевищить SPY більш ніж на 1%;
- `neutral`: різниця буде в межах ±1%;
- `underperform`: MSFT відстане від SPY більш ніж на 1%.

Це **класифікація**, а не регресія, тому що готова ціль `target_class` є категоріальною. Регресію майбутньої надлишкової дохідності можна перевірити пізніше як окремий експеримент.

Test-період у цьому notebook не використовується для вибору моделі.
'''),
    code('''from pathlib import Path
import os
import subprocess
import sys

REPO_URL = "https://github.com/Magnitol110/MarketLens.git"
IN_COLAB = "google.colab" in sys.modules

if IN_COLAB:
    repo_path = Path("/content/MarketLens")
    if not repo_path.exists():
        subprocess.run(["git", "clone", REPO_URL, str(repo_path)], check=True)
    os.chdir(repo_path)

ROOT = Path.cwd()
if ROOT.name == "notebooks":
    ROOT = ROOT.parent
assert (ROOT / "README.md").exists(), f"Repository root not found: {ROOT}"

try:
    import sklearn
except ImportError:
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-r", str(ROOT / "requirements-ml.txt")], check=True)

print("Repository:", ROOT)
print("Python:", sys.executable)'''),
    markdown('''## 1. Завантаження готових ознак

Використовуємо тільки `train` для навчання і `validation` для порівняння моделей. `test` лише рахуємо, але не відкриваємо його ціль і не робимо на ньому прогнозів.
'''),
    code('''import hashlib
import json

import joblib
import numpy as np
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, balanced_accuracy_score, confusion_matrix, f1_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

DATA_PATH = ROOT / "data" / "processed" / "training_features.csv"
data = pd.read_csv(DATA_PATH, parse_dates=["date"])
feature_columns = [column for column in data.columns if column not in {"date", "split", "target_class"}]

train = data.loc[data["split"] == "train"].copy()
validation = data.loc[data["split"] == "validation"].copy()
test_row_count = int((data["split"] == "test").sum())

X_train = train[feature_columns]
y_train = train["target_class"]
X_validation = validation[feature_columns]
y_validation = validation["target_class"]

assert train["date"].max() < validation["date"].min()
assert not any("future" in column.lower() or "target" in column.lower() for column in feature_columns)
assert X_train.isna().sum().sum() == 0 and X_validation.isna().sum().sum() == 0

print("Train:", train["date"].min().date(), "—", train["date"].max().date(), len(train))
print("Validation:", validation["date"].min().date(), "—", validation["date"].max().date(), len(validation))
print("Untouched test rows:", test_row_count)
print("Features:", len(feature_columns))'''),
    markdown('''## 2. Фіксовані baseline-моделі

Без підбору параметрів перевіряємо:

1. `Dummy most frequent` — мінімальна контрольна точка.
2. `Logistic regression` — проста лінійна модель зі стандартизацією.
3. `Random forest` — обмежена нелінійна модель.
4. `Histogram gradient boosting` — сильніший табличний baseline.

Основна метрика — `macro_f1`, яка однаково враховує всі три класи.
'''),
    code('''RANDOM_STATE = 42

models = {
    "dummy_most_frequent": DummyClassifier(strategy="most_frequent"),
    "logistic_regression": Pipeline([
        ("scale", StandardScaler()),
        ("model", LogisticRegression(
            max_iter=3000,
            class_weight="balanced",
            random_state=RANDOM_STATE,
        )),
    ]),
    "random_forest": RandomForestClassifier(
        n_estimators=400,
        max_depth=6,
        min_samples_leaf=8,
        class_weight="balanced_subsample",
        random_state=RANDOM_STATE,
        n_jobs=-1,
    ),
    "hist_gradient_boosting": HistGradientBoostingClassifier(
        max_iter=200,
        learning_rate=0.05,
        max_leaf_nodes=15,
        min_samples_leaf=20,
        l2_regularization=1.0,
        class_weight="balanced",
        random_state=RANDOM_STATE,
    ),
}'''),
    code('''LABELS = ["underperform", "neutral", "outperform"]
results = []
predictions = {}

for name, model in models.items():
    model.fit(X_train, y_train)
    prediction = model.predict(X_validation)
    predictions[name] = prediction
    results.append({
        "model": name,
        "accuracy": accuracy_score(y_validation, prediction),
        "balanced_accuracy": balanced_accuracy_score(y_validation, prediction),
        "macro_f1": f1_score(y_validation, prediction, average="macro"),
        "weighted_f1": f1_score(y_validation, prediction, average="weighted"),
    })

results_frame = pd.DataFrame(results).sort_values("macro_f1", ascending=False).reset_index(drop=True)
display(results_frame.round(4))

best_name = results_frame.loc[0, "model"]
best_model = models[best_name]
best_prediction = predictions[best_name]
print("Selected baseline:", best_name)'''),
    markdown('''## 3. Confusion matrix найкращого baseline

Рядки — справжній клас, стовпці — прогнозований.
'''),
    code('''matrix = confusion_matrix(y_validation, best_prediction, labels=LABELS)
matrix_frame = pd.DataFrame(matrix, index=[f"true_{label}" for label in LABELS], columns=[f"pred_{label}" for label in LABELS])
display(matrix_frame)

per_class_f1 = f1_score(y_validation, best_prediction, labels=LABELS, average=None)
display(pd.DataFrame({"class": LABELS, "f1": per_class_f1}).round(4))'''),
    markdown('''## 4. Збереження доказів

Зберігаємо локальний baseline pipeline і JSON із validation-метриками. Test залишається недоторканим для `04_evaluation.ipynb`.
'''),
    code('''def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

MODEL_PATH = ROOT / "models" / "baseline_model.joblib"
METRICS_PATH = ROOT / "docs" / "baseline-metrics.json"
MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)

joblib.dump({
    "model": best_model,
    "feature_columns": feature_columns,
    "labels": LABELS,
    "prediction_horizon_trading_days": 5,
}, MODEL_PATH)

metrics = {
    "selected_model": best_name,
    "selection_metric": "validation_macro_f1",
    "validation_period": {
        "first_date": validation["date"].min().date().isoformat(),
        "last_date": validation["date"].max().date().isoformat(),
        "rows": len(validation),
    },
    "test_rows_untouched": test_row_count,
    "training_data_sha256": sha256(DATA_PATH),
    "feature_count": len(feature_columns),
    "results": results_frame.to_dict(orient="records"),
    "confusion_matrix_labels": LABELS,
    "confusion_matrix": matrix.tolist(),
}
METRICS_PATH.write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")

print("Saved model:", MODEL_PATH)
print("Saved metrics:", METRICS_PATH)
print("Test predictions made: 0")'''),
    markdown('''## Висновок

Baseline завершено, коли обрана модель перевищує Dummy за macro F1, метрики зафіксовані, а test не використовувався. Далі команда переглядає ознаки й можливий витік перед створенням фінального pipeline.
'''),
]

notebook = {
    "cells": cells,
    "metadata": {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3"},
        "colab": {"provenance": []},
    },
    "nbformat": 4,
    "nbformat_minor": 5,
}
OUTPUT.write_text(json.dumps(notebook, ensure_ascii=False, indent=1), encoding="utf-8")
print(OUTPUT)
