"""Generate the frozen-model held-out evaluation notebook."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "notebooks" / "04_evaluation.ipynb"


def markdown(source: str) -> dict:
    return {"cell_type": "markdown", "metadata": {}, "source": source}


def code(source: str) -> dict:
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": source,
    }


cells = [
    markdown('''# 04 — Frozen-model evaluation on the held-out test period

## tl;dr

This notebook evaluates the already frozen GPU-trained MLP exactly once on the newest chronological test period. It does not tune features, thresholds, architecture or epochs using test results.

The notebook compares the neural network with a most-frequent dummy and the selected histogram gradient boosting baseline, calculates uncertainty with paired bootstrap resampling, and exports charts plus a portable NumPy inference artifact for deployment.
'''),
    markdown('''## Context & Methods

### Key assumptions

- Target: MSFT return relative to SPY over the next five trading days.
- Classes: `underperform` below −1%, `neutral` within ±1%, `outperform` above +1%.
- Primary metric: macro-F1, because all three classes matter equally.
- The test period is newer than both train and validation periods.
- Test results are reporting evidence, not a new tuning signal.
'''),
    code('''from pathlib import Path
import hashlib
import json
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
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

matplotlib_cache = ROOT / "worklog" / ".matplotlib"
matplotlib_cache.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(matplotlib_cache))
os.environ.setdefault("MPLBACKEND", "Agg")

try:
    import torch
    import matplotlib
except ImportError:
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "torch", "matplotlib"], check=True)

print("Repository:", ROOT)
print("Python:", sys.executable)
print("PyTorch:", torch.__version__)'''),
    markdown('''## Data

The bundle contains the exact feature order and train-only normalization statistics. A normalized line-ending hash confirms that the Colab training file and the Windows checkout contain identical CSV content despite CRLF/LF differences.
'''),
    code('''import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
)

from backend.model import MarketLensMLP

DATA_PATH = ROOT / "data" / "processed" / "training_features.csv"
BUNDLE_PATH = ROOT / "models" / "marketlens_mlp_bundle.pt"
TRAINING_METRICS_PATH = ROOT / "docs" / "final-model-metrics.json"

data = pd.read_csv(DATA_PATH, parse_dates=["date"])
bundle = torch.load(BUNDLE_PATH, map_location="cpu", weights_only=False)
training_metrics = json.loads(TRAINING_METRICS_PATH.read_text(encoding="utf-8"))

normalized_bytes = DATA_PATH.read_bytes().replace(b"\\r\\n", b"\\n")
normalized_sha256 = hashlib.sha256(normalized_bytes).hexdigest()
assert normalized_sha256 == training_metrics["input_sha256"], "Training file content does not match the frozen model."

feature_columns = bundle["feature_columns"]
labels = ["underperform", "neutral", "outperform"]
label_to_index = {label: index for index, label in enumerate(labels)}

train = data.loc[data["split"].eq("train")].copy()
validation = data.loc[data["split"].eq("validation")].copy()
test = data.loc[data["split"].eq("test")].copy()

assert train["date"].max() < validation["date"].min() < test["date"].min()
assert len(test) == training_metrics["test_rows_untouched"]

display(pd.DataFrame({
    "split": ["train", "validation", "test"],
    "rows": [len(train), len(validation), len(test)],
    "start": [train["date"].min().date(), validation["date"].min().date(), test["date"].min().date()],
    "end": [train["date"].max().date(), validation["date"].max().date(), test["date"].max().date()],
}))
print("Normalized training-data SHA-256:", normalized_sha256)'''),
    markdown('''## Results

The neural network is evaluated with the preprocessing stored in its bundle. Both baselines are fit only on the original train split, preserving the same validation-based model-selection protocol.
'''),
    code('''mean = np.asarray(bundle["preprocessing"]["mean"], dtype=np.float32)
scale = np.asarray(bundle["preprocessing"]["scale"], dtype=np.float32)

X_train = train[feature_columns].to_numpy(dtype=np.float32)
X_test_raw = test[feature_columns].to_numpy(dtype=np.float32)
X_test_scaled = ((X_test_raw - mean) / scale).astype(np.float32)
y_train = train["target_class"].map(label_to_index).to_numpy(dtype=np.int64)
y_test = test["target_class"].map(label_to_index).to_numpy(dtype=np.int64)

architecture = bundle["architecture"]
model = MarketLensMLP(
    input_size=architecture["input_size"],
    hidden_sizes=tuple(architecture["hidden_sizes"]),
    dropout=architecture["dropout"],
    output_size=architecture["output_size"],
)
model.load_state_dict(bundle["model_state_dict"])
model.eval()

with torch.inference_mode():
    logits = model(torch.as_tensor(X_test_scaled, dtype=torch.float32))
    probabilities = torch.softmax(logits, dim=1).numpy()
mlp_predictions = probabilities.argmax(axis=1)

baseline = HistGradientBoostingClassifier(
    max_iter=200,
    learning_rate=0.05,
    max_leaf_nodes=15,
    min_samples_leaf=20,
    l2_regularization=1.0,
    class_weight="balanced",
    random_state=42,
)
baseline.fit(X_train, y_train)
baseline_predictions = baseline.predict(X_test_raw)

dummy = DummyClassifier(strategy="most_frequent")
dummy.fit(X_train, y_train)
dummy_predictions = dummy.predict(X_test_raw)

def metric_row(name, predictions):
    return {
        "model": name,
        "accuracy": float(accuracy_score(y_test, predictions)),
        "balanced_accuracy": float(balanced_accuracy_score(y_test, predictions)),
        "macro_f1": float(f1_score(y_test, predictions, average="macro")),
        "weighted_f1": float(f1_score(y_test, predictions, average="weighted")),
    }

comparison = pd.DataFrame([
    metric_row("GPU MLP", mlp_predictions),
    metric_row("Histogram gradient boosting", baseline_predictions),
    metric_row("Most-frequent dummy", dummy_predictions),
]).sort_values("macro_f1", ascending=False)
display(comparison)'''),
    markdown('''### Uncertainty and class-level behavior

Bootstrap intervals show how much the headline metric could vary within this finite test period. The confusion matrix makes failure modes visible instead of hiding them behind one score.
'''),
    code('''rng = np.random.default_rng(42)
bootstrap_rows = []
for _ in range(2000):
    indices = rng.integers(0, len(y_test), size=len(y_test))
    bootstrap_rows.append({
        "mlp": f1_score(y_test[indices], mlp_predictions[indices], average="macro", zero_division=0),
        "baseline": f1_score(y_test[indices], baseline_predictions[indices], average="macro", zero_division=0),
    })
bootstrap = pd.DataFrame(bootstrap_rows)
mlp_ci = np.quantile(bootstrap["mlp"], [0.025, 0.975])
difference = bootstrap["mlp"] - bootstrap["baseline"]
difference_ci = np.quantile(difference, [0.025, 0.975])

report = classification_report(
    y_test,
    mlp_predictions,
    target_names=labels,
    output_dict=True,
    zero_division=0,
)
confusion = confusion_matrix(y_test, mlp_predictions, labels=[0, 1, 2])

print(f"MLP macro-F1 95% bootstrap CI: [{mlp_ci[0]:.3f}, {mlp_ci[1]:.3f}]")
print(f"MLP minus baseline macro-F1 95% CI: [{difference_ci[0]:.3f}, {difference_ci[1]:.3f}]")
display(pd.DataFrame(report).T.loc[labels, ["precision", "recall", "f1-score", "support"]])

figures_dir = ROOT / "docs" / "figures"
figures_dir.mkdir(parents=True, exist_ok=True)

fig, ax = plt.subplots(figsize=(7.5, 4.5))
bars = ax.bar(comparison["model"], comparison["macro_f1"], color=["#2563eb", "#7c3aed", "#64748b"])
ax.set_ylim(0, max(0.5, comparison["macro_f1"].max() + 0.08))
ax.set_ylabel("Macro-F1")
ax.set_title("Held-out test performance (2025-01-06 to 2026-07-07)")
ax.tick_params(axis="x", rotation=12)
for bar, value in zip(bars, comparison["macro_f1"]):
    ax.text(bar.get_x() + bar.get_width() / 2, value + 0.01, f"{value:.3f}", ha="center")
fig.tight_layout()
comparison_figure = figures_dir / "test-model-comparison.png"
fig.savefig(comparison_figure, dpi=180, bbox_inches="tight")
plt.show()

fig, ax = plt.subplots(figsize=(5.5, 5))
image = ax.imshow(confusion, cmap="Blues")
for row in range(3):
    for column in range(3):
        ax.text(column, row, confusion[row, column], ha="center", va="center", color="black")
ax.set_xticks(range(3), labels, rotation=20)
ax.set_yticks(range(3), labels)
ax.set_xlabel("Predicted")
ax.set_ylabel("Actual")
ax.set_title("GPU MLP confusion matrix — held-out test")
fig.colorbar(image, ax=ax, fraction=0.046)
fig.tight_layout()
confusion_figure = figures_dir / "test-confusion-matrix.png"
fig.savefig(confusion_figure, dpi=180, bbox_inches="tight")
plt.show()'''),
    markdown('''## Deployment export

For production inference, PyTorch is unnecessary. The frozen linear and batch-normalization parameters are exported to a compressed NumPy artifact, reducing deployment size and cold-start cost.
'''),
    code('''portable_path = ROOT / "backend" / "marketlens_model.npz"
state = bundle["model_state_dict"]
portable_metadata = {
    "format_version": 1,
    "feature_columns": feature_columns,
    "mean": mean.tolist(),
    "scale": scale.tolist(),
    "labels": labels,
    "target": bundle["target"],
    "batch_norm_eps": 1e-5,
}

arrays = {
    key.replace("network.", "layer_").replace(".", "_"): value.detach().cpu().numpy()
    for key, value in state.items()
    if "num_batches_tracked" not in key
}
arrays["metadata_json"] = np.asarray(json.dumps(portable_metadata, ensure_ascii=False))
np.savez_compressed(portable_path, **arrays)

test_predictions_path = ROOT / "docs" / "test-predictions.csv"
pd.DataFrame({
    "date": test["date"].dt.strftime("%Y-%m-%d"),
    "actual": [labels[index] for index in y_test],
    "predicted": [labels[index] for index in mlp_predictions],
    "confidence": probabilities.max(axis=1),
}).to_csv(test_predictions_path, index=False)

metrics_path = ROOT / "docs" / "final-test-metrics.json"
test_metrics = {
    "evaluation_id": "held_out_test_001",
    "frozen_model_experiment_id": training_metrics["experiment_id"],
    "test_period": {
        "first_date": test["date"].min().strftime("%Y-%m-%d"),
        "last_date": test["date"].max().strftime("%Y-%m-%d"),
        "rows": len(test),
    },
    "primary_metric": "macro_f1",
    "comparison": comparison.to_dict(orient="records"),
    "mlp_macro_f1_bootstrap_95_ci": mlp_ci.tolist(),
    "mlp_minus_baseline_macro_f1_bootstrap_95_ci": difference_ci.tolist(),
    "mlp_confusion_matrix": confusion.tolist(),
    "labels": labels,
    "classification_report": report,
    "portable_model": str(portable_path.relative_to(ROOT)),
    "figures": [str(comparison_figure.relative_to(ROOT)), str(confusion_figure.relative_to(ROOT))],
}
metrics_path.write_text(json.dumps(test_metrics, ensure_ascii=False, indent=2), encoding="utf-8")

print("Saved:", metrics_path)
print("Saved:", test_predictions_path)
print("Saved portable model:", portable_path, f"({portable_path.stat().st_size / 1024:.1f} KiB)")'''),
    markdown('''## Takeaways

- Treat the test score as the final measured generalization result for this frozen model.
- A score close to the baseline means the demo proves a complete reproducible ML product pipeline, not a reliable trading edge.
- The website must display probabilities as experimental research signals and retain the investment disclaimer.
'''),
]

notebook = {
    "cells": cells,
    "metadata": {
        "colab": {"provenance": []},
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3.12"},
    },
    "nbformat": 4,
    "nbformat_minor": 5,
}

OUTPUT.write_text(json.dumps(notebook, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"Generated {OUTPUT}")
