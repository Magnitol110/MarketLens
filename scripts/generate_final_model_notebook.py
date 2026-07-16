"""Generate the reproducible CUDA training notebook for MarketLens."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "notebooks" / "03_final_model.ipynb"


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
    markdown('''# 03 — Фінальна нейромережа на GPU

## Що демонструє цей notebook

1. Модель навчається **лише на `train`** і виконує обчислення на NVIDIA GPU через CUDA.
2. Нормалізація ознак обчислюється лише за `train`, тому немає витоку з майбутнього.
3. `validation` використовується для early stopping і вибору найкращої епохи.
4. `test` не відкривається і не використовується — його залишаємо для notebook `04_evaluation.ipynb`.
5. Зберігаються окремі ваги `.pt` та deployment bundle з вагами, порядком ознак, нормалізацією і назвами класів.

Ціль — три класи відносної дохідності MSFT проти SPY на наступні 5 торгових днів: `underperform`, `neutral`, `outperform`.
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
    import torch
except ImportError:
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", str(ROOT / "requirements-gpu.txt")],
        check=True,
    )
    import torch

if not torch.cuda.is_available():
    raise RuntimeError(
        "CUDA GPU is required. In Colab choose Runtime → Change runtime type → T4 GPU."
    )

DEVICE = torch.device("cuda")
GPU_NAME = torch.cuda.get_device_name(0)
print("Repository:", ROOT)
print("Python:", sys.executable)
print("PyTorch:", torch.__version__)
print("CUDA runtime:", torch.version.cuda)
print("Training device:", DEVICE)
print("GPU:", GPU_NAME)'''),
    markdown('''## 1. Дані та захист від витоку

Порядок рядків уже хронологічний. Із моделі виключаємо `date`, `split` та `target_class`. Статистики нормалізації рахуємо тільки на старішому train-періоді.
'''),
    code('''import hashlib
import json
import random

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, balanced_accuracy_score, confusion_matrix, f1_score
from torch import nn
from torch.utils.data import DataLoader, TensorDataset

from backend.model import MarketLensMLP

SEED = 42
random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)
torch.cuda.manual_seed_all(SEED)
torch.backends.cudnn.deterministic = True
torch.backends.cudnn.benchmark = False

DATA_PATH = ROOT / "data" / "processed" / "training_features.csv"
data = pd.read_csv(DATA_PATH, parse_dates=["date"])
feature_columns = [column for column in data.columns if column not in {"date", "split", "target_class"}]

train = data.loc[data["split"].eq("train")].copy()
validation = data.loc[data["split"].eq("validation")].copy()
test_row_count = int(data["split"].eq("test").sum())

labels = ["underperform", "neutral", "outperform"]
label_to_index = {label: index for index, label in enumerate(labels)}
index_to_label = {index: label for label, index in label_to_index.items()}

train_mean = train[feature_columns].mean().to_numpy(dtype=np.float32)
train_scale = train[feature_columns].std(ddof=0).to_numpy(dtype=np.float32)
train_scale = np.where(train_scale < 1e-8, 1.0, train_scale).astype(np.float32)

X_train = ((train[feature_columns].to_numpy(dtype=np.float32) - train_mean) / train_scale).astype(np.float32)
X_validation = ((validation[feature_columns].to_numpy(dtype=np.float32) - train_mean) / train_scale).astype(np.float32)
y_train = train["target_class"].map(label_to_index).to_numpy(dtype=np.int64)
y_validation = validation["target_class"].map(label_to_index).to_numpy(dtype=np.int64)

assert np.isfinite(X_train).all() and np.isfinite(X_validation).all()
assert set(np.unique(y_train)) == {0, 1, 2}

summary = pd.DataFrame(
    {
        "split": ["train", "validation", "test (untouched)"],
        "rows": [len(train), len(validation), test_row_count],
        "start": [train["date"].min().date(), validation["date"].min().date(), "not loaded"],
        "end": [train["date"].max().date(), validation["date"].max().date(), "not loaded"],
    }
)
display(summary)
print("Features:", len(feature_columns))
print("Train-only normalization confirmed.")'''),
    markdown('''## 2. Архітектура й навчання

Компактна MLP має два приховані шари, BatchNorm, ReLU та Dropout. Ваги класів компенсують нерівномірний розподіл цілі. Найкращий стан визначаємо за `validation macro-F1`.
'''),
    code('''HIDDEN_SIZES = (128, 64)
DROPOUT = 0.25
BATCH_SIZE = 128
MAX_EPOCHS = 300
PATIENCE = 40
LEARNING_RATE = 1e-3
WEIGHT_DECAY = 1e-4

train_dataset = TensorDataset(torch.from_numpy(X_train), torch.from_numpy(y_train))
train_loader = DataLoader(
    train_dataset,
    batch_size=BATCH_SIZE,
    shuffle=True,
    num_workers=0,
    pin_memory=True,
    generator=torch.Generator().manual_seed(SEED),
)
validation_features_gpu = torch.as_tensor(X_validation, dtype=torch.float32, device=DEVICE)

class_counts = np.bincount(y_train, minlength=len(labels))
class_weights = len(y_train) / (len(labels) * class_counts)
class_weights_gpu = torch.as_tensor(class_weights, dtype=torch.float32, device=DEVICE)

model = MarketLensMLP(
    input_size=len(feature_columns),
    hidden_sizes=HIDDEN_SIZES,
    dropout=DROPOUT,
    output_size=len(labels),
).to(DEVICE)
loss_function = nn.CrossEntropyLoss(weight=class_weights_gpu)
optimizer = torch.optim.AdamW(model.parameters(), lr=LEARNING_RATE, weight_decay=WEIGHT_DECAY)
scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
    optimizer, mode="max", factor=0.5, patience=10, min_lr=1e-5
)

best_macro_f1 = -1.0
best_epoch = 0
best_state = None
epochs_without_improvement = 0
history = []

for epoch in range(1, MAX_EPOCHS + 1):
    model.train()
    total_loss = 0.0
    for batch_features, batch_targets in train_loader:
        batch_features = batch_features.to(DEVICE, non_blocking=True)
        batch_targets = batch_targets.to(DEVICE, non_blocking=True)
        optimizer.zero_grad(set_to_none=True)
        logits = model(batch_features)
        loss = loss_function(logits, batch_targets)
        loss.backward()
        optimizer.step()
        total_loss += float(loss.item()) * len(batch_targets)

    model.eval()
    with torch.inference_mode():
        validation_logits = model(validation_features_gpu)
        validation_predictions = validation_logits.argmax(dim=1).cpu().numpy()

    macro_f1 = f1_score(y_validation, validation_predictions, average="macro")
    accuracy = accuracy_score(y_validation, validation_predictions)
    scheduler.step(macro_f1)
    history.append(
        {
            "epoch": epoch,
            "train_loss": total_loss / len(train_dataset),
            "validation_macro_f1": macro_f1,
            "validation_accuracy": accuracy,
            "learning_rate": optimizer.param_groups[0]["lr"],
        }
    )

    if macro_f1 > best_macro_f1 + 1e-4:
        best_macro_f1 = float(macro_f1)
        best_epoch = epoch
        best_state = {key: value.detach().cpu().clone() for key, value in model.state_dict().items()}
        epochs_without_improvement = 0
    else:
        epochs_without_improvement += 1

    if epoch == 1 or epoch % 20 == 0:
        print(
            f"epoch={epoch:03d} loss={history[-1]['train_loss']:.4f} "
            f"val_macro_f1={macro_f1:.4f} device={next(model.parameters()).device}"
        )
    if epochs_without_improvement >= PATIENCE:
        print(f"Early stopping at epoch {epoch}.")
        break

assert best_state is not None
model.load_state_dict(best_state)
model.to(DEVICE).eval()
print("Best epoch:", best_epoch)
print("Best validation macro-F1:", round(best_macro_f1, 4))
print("Model device:", next(model.parameters()).device)'''),
    markdown('''## 3. Метрики й артефакти

- `marketlens_mlp_weights.pt` — лише ваги нейромережі.
- `marketlens_mlp_bundle.pt` — готовий пакет для сайту: ваги + архітектура + preprocessing + класи.
- `docs/final-model-metrics.json` — перевірюваний звіт для команди й учителів.

Файли ваг навмисно ігноруються Git, бо бінарні моделі краще зберігати як release artifact або у хмарному сховищі.
'''),
    code('''model.eval()
with torch.inference_mode():
    validation_probabilities = torch.softmax(model(validation_features_gpu), dim=1).cpu().numpy()
validation_predictions = validation_probabilities.argmax(axis=1)

validation_metrics = {
    "macro_f1": float(f1_score(y_validation, validation_predictions, average="macro")),
    "accuracy": float(accuracy_score(y_validation, validation_predictions)),
    "balanced_accuracy": float(balanced_accuracy_score(y_validation, validation_predictions)),
    "confusion_matrix": confusion_matrix(y_validation, validation_predictions, labels=[0, 1, 2]).tolist(),
}

models_dir = ROOT / "models"
models_dir.mkdir(parents=True, exist_ok=True)
weights_path = models_dir / "marketlens_mlp_weights.pt"
bundle_path = models_dir / "marketlens_mlp_bundle.pt"
metrics_path = ROOT / "docs" / "final-model-metrics.json"

torch.save(best_state, weights_path)
bundle = {
    "format_version": 1,
    "model_state_dict": best_state,
    "architecture": {
        "input_size": len(feature_columns),
        "hidden_sizes": list(HIDDEN_SIZES),
        "dropout": DROPOUT,
        "output_size": len(labels),
    },
    "feature_columns": feature_columns,
    "preprocessing": {"mean": train_mean.tolist(), "scale": train_scale.tolist()},
    "label_to_index": label_to_index,
    "index_to_label": index_to_label,
    "target": {
        "horizon_trading_days": 5,
        "benchmark": "SPY",
        "neutral_threshold": 0.01,
    },
    "validation_metrics": validation_metrics,
}
torch.save(bundle, bundle_path)

input_sha256 = hashlib.sha256(DATA_PATH.read_bytes()).hexdigest()
metrics = {
    "experiment_id": "gpu_mlp_001",
    "model": "MarketLensMLP",
    "task": "three-class classification",
    "seed": SEED,
    "device": str(DEVICE),
    "gpu_name": GPU_NAME,
    "torch_version": torch.__version__,
    "cuda_runtime": torch.version.cuda,
    "best_epoch": best_epoch,
    "epochs_trained": len(history),
    "architecture": bundle["architecture"],
    "train_rows": len(train),
    "validation_rows": len(validation),
    "test_rows_untouched": test_row_count,
    "feature_count": len(feature_columns),
    "validation": validation_metrics,
    "input_file": str(DATA_PATH.relative_to(ROOT)),
    "input_sha256": input_sha256,
    "weights_file": str(weights_path.relative_to(ROOT)),
    "bundle_file": str(bundle_path.relative_to(ROOT)),
    "code_files": ["notebooks/03_final_model.ipynb", "backend/model.py"],
}
metrics_path.write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")

display(pd.DataFrame([validation_metrics]).drop(columns=["confusion_matrix"]))
print("Confusion matrix [underperform, neutral, outperform]:")
print(np.asarray(validation_metrics["confusion_matrix"]))
print("Saved weights:", weights_path, f"({weights_path.stat().st_size / 1024:.1f} KiB)")
print("Saved deployment bundle:", bundle_path, f"({bundle_path.stat().st_size / 1024:.1f} KiB)")
print("Saved metrics:", metrics_path)'''),
    markdown('''## 4. Перевірка deployment bundle і завантаження з Colab

Завантажуємо збережений пакет через той самий модуль, який використає backend, і перевіряємо збіг прогнозів. Для inference GPU не обов’язковий — сайт може працювати на CPU.

У Colab фінальні файли упаковуються в невеликий `marketlens_model_artifacts.zip` і завантажуються через браузер. Google Drive не використовується.
'''),
    code('''import zipfile

from backend.model import load_model_bundle, predict_rows

deployment_model, deployment_bundle = load_model_bundle(bundle_path, device="cpu")
deployment_predictions = predict_rows(
    deployment_model,
    deployment_bundle,
    validation.iloc[:3][feature_columns].to_numpy(dtype=np.float32),
    device="cpu",
)
assert len(deployment_predictions) == 3
assert all(abs(sum(item["probabilities"].values()) - 1.0) < 1e-5 for item in deployment_predictions)
display(pd.DataFrame(deployment_predictions))
print("Deployment bundle reload test: OK")
print("The test split remains untouched:", test_row_count, "rows reserved for notebook 04.")'''),
    code('''archive_path = ROOT / "marketlens_model_artifacts.zip"
export_files = [weights_path, bundle_path, metrics_path]
with zipfile.ZipFile(archive_path, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
    for source_path in export_files:
        archive.write(source_path, arcname=source_path.name)

print("Created artifact archive:", archive_path)
print("Archive size:", f"{archive_path.stat().st_size / 1024:.1f} KiB")

if IN_COLAB:
    from google.colab import files

    files.download(str(archive_path))
    print("Browser download requested. Google Drive was not used.")
else:
    print("Local run: archive remains at", archive_path)
'''),
]

notebook = {
    "cells": cells,
    "metadata": {
        "accelerator": "GPU",
        "colab": {"provenance": []},
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3.12"},
    },
    "nbformat": 4,
    "nbformat_minor": 5,
}

OUTPUT.write_text(json.dumps(notebook, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"Generated {OUTPUT}")
