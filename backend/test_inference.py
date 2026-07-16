from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import torch

from backend.inference import PortableMarketLensModel
from backend.model import load_model_bundle


ROOT = Path(__file__).resolve().parents[1]


def test_portable_probabilities_match_pytorch() -> None:
    data = pd.read_csv(ROOT / "data" / "processed" / "training_features.csv")
    bundle_model, bundle = load_model_bundle(ROOT / "models" / "marketlens_mlp_bundle.pt")
    portable = PortableMarketLensModel(ROOT / "backend" / "marketlens_model.npz")
    rows = data.loc[data["split"].eq("test"), bundle["feature_columns"]].to_numpy(dtype=np.float32)

    mean = np.asarray(bundle["preprocessing"]["mean"], dtype=np.float32)
    scale = np.asarray(bundle["preprocessing"]["scale"], dtype=np.float32)
    with torch.inference_mode():
        pytorch_probabilities = torch.softmax(
            bundle_model(torch.as_tensor((rows - mean) / scale, dtype=torch.float32)),
            dim=1,
        ).numpy()

    portable_probabilities = portable.predict_array(rows)
    np.testing.assert_allclose(portable_probabilities, pytorch_probabilities, rtol=1e-5, atol=1e-6)


def test_portable_metadata_is_complete() -> None:
    portable = PortableMarketLensModel(ROOT / "backend" / "marketlens_model.npz")
    assert len(portable.feature_columns) == 36
    assert portable.labels == ["underperform", "neutral", "outperform"]
    assert portable.metadata["target"]["horizon_trading_days"] == 5
