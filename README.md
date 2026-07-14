# MarketLens

An educational web application that analyses historical market signals. It does **not** provide investment advice, trading instructions, target prices, or guaranteed-return claims.

## MVP

For a fixed set of liquid US-company tickers, MarketLens predicts one of three experimental next-five-trading-day outcomes relative to SPY:

- `outperform` — more than 1% above SPY;
- `neutral` — within ±1% of SPY;
- `underperform` — more than 1% below SPY.

The first model uses only information available before its prediction: price/volume features, market features, and—only when sufficient timestamped historical coverage exists—news sentiment.

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
