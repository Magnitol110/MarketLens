"""Build canonical MarketLens price datasets from raw Kaggle and Nasdaq files."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"

MSFT_KAGGLE = RAW_DIR / "msft_kaggle_1986-03-13_2025-07-11.csv"
MSFT_NASDAQ = RAW_DIR / "msft_nasdaq_2025-07-12_2026-07-14.json"
SPY_NASDAQ = RAW_DIR / "spy_nasdaq_1993-01-29_2026-07-14.json"

PRICE_COLUMNS = ["open", "high", "low", "close"]


def clean_number(value: object) -> float | None:
    """Convert Nasdaq strings such as '$390.99', '28,914,880', or 'N/A'."""
    if value is None:
        return None
    text = str(value).strip().replace("$", "").replace(",", "")
    if text in {"", "N/A", "None", "null"}:
        return None
    return float(text)


def load_kaggle_msft(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    frame.columns = [column.strip().lower().replace(" ", "_") for column in frame.columns]
    frame["date"] = pd.to_datetime(frame["date"], errors="coerce").dt.normalize()
    for column in [*PRICE_COLUMNS, "volume"]:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")

    # The source contains one non-data ticker row and a stale adjusted-close field.
    # Raw close is retained consistently across Kaggle and Nasdaq sources.
    frame = frame.dropna(subset=["date", *PRICE_COLUMNS, "volume"])
    frame = frame[["date", *PRICE_COLUMNS, "volume"]]
    frame["source"] = "kaggle_matiflatif"
    return frame


def load_nasdaq(path: Path, source_name: str) -> pd.DataFrame:
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = payload["data"]["tradesTable"]["rows"]
    frame = pd.DataFrame(rows)
    frame["date"] = pd.to_datetime(frame["date"], format="%m/%d/%Y", errors="coerce")
    for column in [*PRICE_COLUMNS, "volume"]:
        frame[column] = frame[column].map(clean_number)
    frame = frame.dropna(subset=["date", *PRICE_COLUMNS, "volume"])
    frame = frame[["date", *PRICE_COLUMNS, "volume"]]
    frame["source"] = source_name
    return frame


def validate_and_format(frame: pd.DataFrame, label: str) -> pd.DataFrame:
    frame = frame.sort_values("date").drop_duplicates("date", keep="last").reset_index(drop=True)

    valid_prices = (frame[PRICE_COLUMNS] > 0).all(axis=1)
    valid_volume = frame["volume"] > 0
    valid_ohlc = (
        (frame["low"] <= frame[["open", "close"]].min(axis=1))
        & (frame["high"] >= frame[["open", "close"]].max(axis=1))
        & (frame["low"] <= frame["high"])
    )
    invalid = ~(valid_prices & valid_volume & valid_ohlc)
    if invalid.any():
        bad_dates = frame.loc[invalid, "date"].dt.strftime("%Y-%m-%d").tolist()
        raise ValueError(f"{label}: invalid rows remain for dates {bad_dates[:10]}")

    frame["date"] = frame["date"].dt.strftime("%Y-%m-%d")
    frame[PRICE_COLUMNS] = frame[PRICE_COLUMNS].round(6)
    frame["volume"] = frame["volume"].round().astype("int64")
    return frame


def main() -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    msft_archive = load_kaggle_msft(MSFT_KAGGLE)
    msft_recent = load_nasdaq(MSFT_NASDAQ, "nasdaq")
    msft = validate_and_format(pd.concat([msft_archive, msft_recent], ignore_index=True), "MSFT")

    spy_raw = load_nasdaq(SPY_NASDAQ, "nasdaq")
    # Nasdaq may return occasional incomplete rows (for example N/A volume).
    spy = validate_and_format(spy_raw, "SPY")

    msft.to_csv(PROCESSED_DIR / "msft_daily.csv", index=False)
    spy.to_csv(PROCESSED_DIR / "spy_daily.csv", index=False)

    msft_model = msft.drop(columns="source").add_prefix("msft_").rename(columns={"msft_date": "date"})
    spy_model = spy.drop(columns="source").add_prefix("spy_").rename(columns={"spy_date": "date"})
    model_table = msft_model.merge(spy_model, on="date", how="inner", validate="one_to_one")
    model_table.to_csv(PROCESSED_DIR / "msft_spy_daily.csv", index=False)

    print(
        json.dumps(
            {
                "msft": {"rows": len(msft), "min_date": msft.date.min(), "max_date": msft.date.max()},
                "spy": {"rows": len(spy), "min_date": spy.date.min(), "max_date": spy.date.max()},
                "model_table": {
                    "rows": len(model_table),
                    "min_date": model_table.date.min(),
                    "max_date": model_table.date.max(),
                },
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
