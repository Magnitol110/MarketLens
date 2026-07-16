"""Lightweight NumPy inference for the frozen MarketLens neural network."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Mapping, Sequence

import numpy as np


class PortableMarketLensModel:
    """Run the exported MLP without PyTorch in the deployed API."""

    def __init__(self, artifact_path: str | Path) -> None:
        artifact = np.load(Path(artifact_path), allow_pickle=False)
        self.metadata = json.loads(str(artifact["metadata_json"].item()))
        self.arrays = {name: artifact[name] for name in artifact.files if name != "metadata_json"}
        self.feature_columns: list[str] = self.metadata["feature_columns"]
        self.labels: list[str] = self.metadata["labels"]
        self.mean = np.asarray(self.metadata["mean"], dtype=np.float32)
        self.scale = np.asarray(self.metadata["scale"], dtype=np.float32)
        self.batch_norm_eps = float(self.metadata["batch_norm_eps"])

    def _linear(self, values: np.ndarray, layer: int) -> np.ndarray:
        weight = self.arrays[f"layer_{layer}_weight"]
        bias = self.arrays[f"layer_{layer}_bias"]
        return values @ weight.T + bias

    def _batch_norm(self, values: np.ndarray, layer: int) -> np.ndarray:
        weight = self.arrays[f"layer_{layer}_weight"]
        bias = self.arrays[f"layer_{layer}_bias"]
        running_mean = self.arrays[f"layer_{layer}_running_mean"]
        running_var = self.arrays[f"layer_{layer}_running_var"]
        normalized = (values - running_mean) / np.sqrt(running_var + self.batch_norm_eps)
        return normalized * weight + bias

    def predict_array(self, rows: np.ndarray | Sequence[Sequence[float]]) -> np.ndarray:
        values = np.asarray(rows, dtype=np.float32)
        if values.ndim == 1:
            values = values.reshape(1, -1)
        if values.shape[1] != len(self.feature_columns):
            raise ValueError(f"Expected {len(self.feature_columns)} features, received {values.shape[1]}.")

        values = (values - self.mean) / self.scale
        values = np.maximum(self._batch_norm(self._linear(values, 0), 1), 0)
        values = np.maximum(self._batch_norm(self._linear(values, 4), 5), 0)
        logits = self._linear(values, 8)
        logits -= logits.max(axis=1, keepdims=True)
        exponentials = np.exp(logits)
        return exponentials / exponentials.sum(axis=1, keepdims=True)

    def predict_mapping(self, features: Mapping[str, float]) -> dict[str, object]:
        row = np.asarray([features[column] for column in self.feature_columns], dtype=np.float32)
        probabilities = self.predict_array(row)[0]
        class_index = int(probabilities.argmax())
        return {
            "label": self.labels[class_index],
            "confidence": float(probabilities[class_index]),
            "probabilities": {
                label: float(probabilities[index])
                for index, label in enumerate(self.labels)
            },
        }
