"""Read-only FastAPI service for MarketLens history and model signals."""

from __future__ import annotations

import csv
import os
from datetime import date, timedelta
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from backend.inference import PortableMarketLensModel


ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = Path(os.getenv("MARKETLENS_MODEL_PATH", ROOT / "backend" / "marketlens_model.npz"))
LATEST_FEATURES_PATH = ROOT / "data" / "processed" / "latest_features.csv"
HISTORY_PATH = ROOT / "data" / "processed" / "msft_daily.csv"
MODEL_VERSION = "gpu_mlp_001"
SUPPORTED_SYMBOLS = {"MSFT"}


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


model = PortableMarketLensModel(MODEL_PATH)
app = FastAPI(
    title="MarketLens API",
    version="1.0.0",
    description="Educational, read-only market signal API.",
)

allowed_origins = [
    origin.strip()
    for origin in os.getenv(
        "MARKETLENS_CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    ).split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)


def require_supported_symbol(symbol: str) -> str:
    normalized = symbol.upper()
    if normalized not in SUPPORTED_SYMBOLS:
        raise HTTPException(
            status_code=404,
            detail=f"No trained model is available for {normalized}. Current coverage: MSFT.",
        )
    return normalized


def latest_signal(symbol: str) -> dict[str, object]:
    normalized = require_supported_symbol(symbol)
    feature_rows = read_csv_rows(LATEST_FEATURES_PATH)
    if not feature_rows:
        raise HTTPException(status_code=503, detail="Latest feature snapshot is unavailable.")
    latest = feature_rows[-1]
    features = {column: float(latest[column]) for column in model.feature_columns}
    prediction = model.predict_mapping(features)

    history = read_csv_rows(HISTORY_PATH)
    current = history[-1]
    previous = history[-2]
    current_price = float(current["close"])
    previous_price = float(previous["close"])
    daily_change = (current_price / previous_price - 1) * 100

    return {
        "symbol": normalized,
        "as_of_date": latest["date"],
        "current_price": current_price,
        "daily_change_percent": daily_change,
        "prediction": prediction["label"],
        "confidence": prediction["confidence"],
        "probabilities": prediction["probabilities"],
        "horizon_trading_days": int(model.metadata["target"]["horizon_trading_days"]),
        "benchmark": model.metadata["target"]["benchmark"],
        "model_version": MODEL_VERSION,
        "disclaimer": "Experimental educational signal; not investment advice.",
    }


@app.get("/api/health")
def health() -> dict[str, object]:
    return {
        "status": "ok",
        "model_loaded": True,
        "model_version": MODEL_VERSION,
        "coverage": sorted(SUPPORTED_SYMBOLS),
    }


@app.get("/api/assets")
def assets() -> dict[str, object]:
    return {"assets": [latest_signal(symbol) for symbol in sorted(SUPPORTED_SYMBOLS)]}


@app.get("/api/predict/{symbol}")
def predict(symbol: str) -> dict[str, object]:
    return latest_signal(symbol)


@app.get("/api/history/{symbol}")
def history(
    symbol: str,
    period: str = Query(default="5y", pattern="^(1y|5y|max)$"),
) -> dict[str, object]:
    normalized = require_supported_symbol(symbol)
    rows = read_csv_rows(HISTORY_PATH)
    latest_date = date.fromisoformat(rows[-1]["date"])
    if period == "1y":
        start_date = latest_date - timedelta(days=365)
    elif period == "5y":
        start_date = latest_date - timedelta(days=365 * 5)
    else:
        start_date = date.min

    candles = [
        {
            "time": row["date"],
            "open": float(row["open"]),
            "high": float(row["high"]),
            "low": float(row["low"]),
            "close": float(row["close"]),
            "volume": int(float(row["volume"])),
        }
        for row in rows
        if date.fromisoformat(row["date"]) >= start_date
    ]
    return {
        "symbol": normalized,
        "period": period,
        "as_of_date": rows[-1]["date"],
        "candles": candles,
    }
