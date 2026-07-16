"""MarketLens neural-network architecture and inference helpers.

The training notebook saves a deployment bundle containing the model state,
feature order, train-only normalization statistics, and class mapping.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import numpy as np
import torch
from torch import nn


class MarketLensMLP(nn.Module):
    """Compact multilayer perceptron for the three MSFT-vs-SPY classes."""

    def __init__(
        self,
        input_size: int,
        hidden_sizes: tuple[int, ...] = (128, 64),
        dropout: float = 0.25,
        output_size: int = 3,
    ) -> None:
        super().__init__()
        layers: list[nn.Module] = []
        previous_size = input_size
        for hidden_size in hidden_sizes:
            layers.extend(
                [
                    nn.Linear(previous_size, hidden_size),
                    nn.BatchNorm1d(hidden_size),
                    nn.ReLU(),
                    nn.Dropout(dropout),
                ]
            )
            previous_size = hidden_size
        layers.append(nn.Linear(previous_size, output_size))
        self.network = nn.Sequential(*layers)

    def forward(self, features: torch.Tensor) -> torch.Tensor:
        return self.network(features)


def load_model_bundle(
    bundle_path: str | Path,
    device: str | torch.device = "cpu",
) -> tuple[MarketLensMLP, dict]:
    """Load a trained model plus its preprocessing metadata."""

    bundle = torch.load(Path(bundle_path), map_location=device, weights_only=False)
    architecture = bundle["architecture"]
    model = MarketLensMLP(
        input_size=architecture["input_size"],
        hidden_sizes=tuple(architecture["hidden_sizes"]),
        dropout=architecture["dropout"],
        output_size=architecture["output_size"],
    )
    model.load_state_dict(bundle["model_state_dict"])
    model.to(device)
    model.eval()
    return model, bundle


def predict_rows(
    model: MarketLensMLP,
    bundle: dict,
    rows: np.ndarray | Iterable[Iterable[float]],
    device: str | torch.device = "cpu",
) -> list[dict[str, object]]:
    """Predict labels and probabilities for rows in the saved feature order."""

    values = np.asarray(rows, dtype=np.float32)
    if values.ndim == 1:
        values = values.reshape(1, -1)

    mean = np.asarray(bundle["preprocessing"]["mean"], dtype=np.float32)
    scale = np.asarray(bundle["preprocessing"]["scale"], dtype=np.float32)
    normalized = (values - mean) / scale
    tensor = torch.as_tensor(normalized, dtype=torch.float32, device=device)

    with torch.inference_mode():
        probabilities = torch.softmax(model(tensor), dim=1).cpu().numpy()

    index_to_label = {int(key): value for key, value in bundle["index_to_label"].items()}
    predictions: list[dict[str, object]] = []
    for row_probabilities in probabilities:
        class_index = int(row_probabilities.argmax())
        predictions.append(
            {
                "label": index_to_label[class_index],
                "probabilities": {
                    index_to_label[index]: float(probability)
                    for index, probability in enumerate(row_probabilities)
                },
            }
        )
    return predictions
