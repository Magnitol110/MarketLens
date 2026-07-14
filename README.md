# MarketLens

An educational web application that analyses historical market signals. It does **not** provide investment advice, trading instructions, target prices, or guaranteed-return claims.

## MVP

For Microsoft stock (`MSFT`) only, MarketLens predicts one of three experimental next-five-trading-day outcomes relative to SPY:

- `outperform` — more than 1% above SPY;
- `neutral` — within ±1% of SPY;
- `underperform` — more than 1% below SPY.

The first model uses only information available before its prediction: MSFT price/volume features, SPY market features, and—only when sufficient timestamped historical coverage exists—news sentiment.

Historical Kaggle data provides a reproducible training snapshot. A separate, key-protected end-of-day collector will refresh MSFT and SPY after market close; its newest values must never be added to the held-out test period without recording a new dataset version.

## Project rules

- Keep raw data, API keys, trained-model files, and generated data out of Git.
- Every data decision, experiment, and metric must have an entry in `docs/` and an associated Colab notebook.
- Do not randomly shuffle time-series data. Train, validation, and test periods must be chronological.
- The UI must display the data-snapshot date and an educational disclaimer.

## Structure

- `notebooks/` — reproducible Colab evidence for sources, cleaning, training, and evaluation.
- `data/` — local-only data folders plus dataset documentation.
- `backend/` — future FastAPI inference service.
- `frontend/` — future Vue 3 + Vite interface.
- `docs/` — progress, data sources, experiment log, and decisions.
