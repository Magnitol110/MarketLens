"""Create leakage-safe chronological features and labels for MarketLens."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data" / "processed" / "msft_spy_daily.csv"
OUTPUT = ROOT / "data" / "processed" / "training_features.csv"
LATEST_OUTPUT = ROOT / "data" / "processed" / "latest_features.csv"
MANIFEST = ROOT / "docs" / "training-dataset-manifest.json"

HORIZON = 5
THRESHOLD = 0.01
WINDOWS = (5, 10, 20)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_features(prices: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, list[str]]:
    frame = prices.copy()
    frame["date"] = pd.to_datetime(frame["date"], errors="raise")
    frame = frame.sort_values("date").drop_duplicates("date", keep="last").reset_index(drop=True)

    feature_columns: list[str] = []
    for ticker in ("msft", "spy"):
        close = frame[f"{ticker}_close"]
        daily_return = close.pct_change(fill_method=None)

        frame[f"{ticker}_return_1d"] = daily_return
        frame[f"{ticker}_gap_return"] = frame[f"{ticker}_open"] / close.shift(1) - 1
        frame[f"{ticker}_intraday_return"] = close / frame[f"{ticker}_open"] - 1
        frame[f"{ticker}_range_pct"] = (frame[f"{ticker}_high"] - frame[f"{ticker}_low"]) / close
        feature_columns.extend([
            f"{ticker}_return_1d",
            f"{ticker}_gap_return",
            f"{ticker}_intraday_return",
            f"{ticker}_range_pct",
        ])

        for window in WINDOWS:
            frame[f"{ticker}_return_{window}d"] = close.pct_change(window, fill_method=None)
            frame[f"{ticker}_ma_ratio_{window}d"] = close / close.rolling(window, min_periods=window).mean() - 1
            frame[f"{ticker}_volatility_{window}d"] = daily_return.rolling(window, min_periods=window).std()
            feature_columns.extend([
                f"{ticker}_return_{window}d",
                f"{ticker}_ma_ratio_{window}d",
                f"{ticker}_volatility_{window}d",
            ])

        frame[f"{ticker}_volume_ratio_20d"] = (
            frame[f"{ticker}_volume"] / frame[f"{ticker}_volume"].rolling(20, min_periods=20).mean() - 1
        )
        feature_columns.append(f"{ticker}_volume_ratio_20d")

    for window in (1, *WINDOWS):
        frame[f"excess_return_{window}d"] = frame[f"msft_return_{window}d"] - frame[f"spy_return_{window}d"]
        feature_columns.append(f"excess_return_{window}d")

    day_of_week = frame["date"].dt.dayofweek
    month = frame["date"].dt.month
    frame["day_of_week_sin"] = np.sin(2 * np.pi * day_of_week / 5)
    frame["day_of_week_cos"] = np.cos(2 * np.pi * day_of_week / 5)
    frame["month_sin"] = np.sin(2 * np.pi * (month - 1) / 12)
    frame["month_cos"] = np.cos(2 * np.pi * (month - 1) / 12)
    feature_columns.extend(["day_of_week_sin", "day_of_week_cos", "month_sin", "month_cos"])

    future_msft = frame["msft_close"].shift(-HORIZON) / frame["msft_close"] - 1
    future_spy = frame["spy_close"].shift(-HORIZON) / frame["spy_close"] - 1
    future_excess = future_msft - future_spy

    target = pd.Series(pd.NA, index=frame.index, dtype="string")
    valid_target = future_excess.notna()
    target.loc[valid_target & (future_excess > THRESHOLD)] = "outperform"
    target.loc[valid_target & (future_excess < -THRESHOLD)] = "underperform"
    target.loc[valid_target & future_excess.between(-THRESHOLD, THRESHOLD, inclusive="both")] = "neutral"
    frame["target_class"] = target

    inference = frame[["date", *feature_columns]].dropna().reset_index(drop=True)
    training = frame[["date", *feature_columns, "target_class"]].dropna().reset_index(drop=True)
    return training, inference, feature_columns


def add_purged_split(training: pd.DataFrame) -> pd.DataFrame:
    frame = training.copy()
    row_count = len(frame)
    train_end = int(row_count * 0.70)
    validation_end = int(row_count * 0.85)

    frame["split"] = "test"
    frame.loc[: train_end - 1, "split"] = "train"
    frame.loc[train_end : validation_end - 1, "split"] = "validation"

    # Remove the final horizon rows before each boundary. Their labels use prices
    # from the next split and would otherwise leak across the evaluation boundary.
    purge_positions = list(range(train_end - HORIZON, train_end)) + list(
        range(validation_end - HORIZON, validation_end)
    )
    frame = frame.drop(index=purge_positions).reset_index(drop=True)
    return frame


def validate(training: pd.DataFrame, feature_columns: list[str]) -> None:
    assert training["date"].is_monotonic_increasing
    assert not training["date"].duplicated().any()
    assert training[[*feature_columns, "target_class", "split"]].isna().sum().sum() == 0
    assert set(training["target_class"]) == {"outperform", "neutral", "underperform"}
    assert set(training["split"]) == {"train", "validation", "test"}
    assert np.isfinite(training[feature_columns].to_numpy()).all()


def main() -> pd.DataFrame:
    prices = pd.read_csv(INPUT)
    training, inference, feature_columns = build_features(prices)
    training = add_purged_split(training)
    validate(training, feature_columns)

    training["date"] = training["date"].dt.strftime("%Y-%m-%d")
    ordered_columns = ["date", "split", *feature_columns, "target_class"]
    training = training[ordered_columns]
    training.to_csv(OUTPUT, index=False, float_format="%.8g")

    latest = inference.tail(1).copy()
    assert len(latest) == 1
    assert np.isfinite(latest[feature_columns].to_numpy()).all()
    latest["date"] = latest["date"].dt.strftime("%Y-%m-%d")
    latest.to_csv(LATEST_OUTPUT, index=False, float_format="%.8g")

    split_summary = {}
    for split, part in training.groupby("split", sort=False):
        split_summary[split] = {
            "rows": len(part),
            "first_date": part["date"].min(),
            "last_date": part["date"].max(),
            "class_counts": part["target_class"].value_counts().to_dict(),
        }

    manifest = {
        "input": str(INPUT.relative_to(ROOT)).replace("\\", "/"),
        "input_sha256": sha256(INPUT),
        "output": str(OUTPUT.relative_to(ROOT)).replace("\\", "/"),
        "latest_inference_output": str(LATEST_OUTPUT.relative_to(ROOT)).replace("\\", "/"),
        "latest_inference_date": latest["date"].iloc[0],
        "rows": len(training),
        "feature_count": len(feature_columns),
        "first_date": training["date"].min(),
        "last_date": training["date"].max(),
        "target": "MSFT 5-trading-day return minus SPY 5-trading-day return",
        "class_threshold": THRESHOLD,
        "horizon_trading_days": HORIZON,
        "split_method": "chronological 70/15/15 with 5-row purge before validation and test",
        "splits": split_summary,
        "feature_columns": feature_columns,
    }
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return training


if __name__ == "__main__":
    main()
