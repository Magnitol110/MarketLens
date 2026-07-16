# MarketLens

MarketLens is an educational AI web application that turns historical market data into an experimental five-trading-day signal. It does **not** provide investment advice, target prices, or guaranteed-return claims.

## Current MVP

The deployed contract can support multiple tickers, while the first trained model covers Microsoft (`MSFT`). It predicts performance relative to the S&P 500 ETF (`SPY`):

- `outperform` — MSFT beats SPY by more than 1%;
- `neutral` — the difference stays within ±1%;
- `underperform` — MSFT trails SPY by more than 1%.

The current snapshot ends on 14 July 2026. The site shows real OHLCV candles, the latest class probabilities, confidence, model version, and snapshot date.

## What is implemented

- Vue 3 + TypeScript interface with English chart dates;
- FastAPI read-only backend;
- portable 55 KiB NumPy inference artifact trained from a GPU PyTorch MLP;
- chronological, leakage-safe train/validation/test split;
- held-out comparison against a tree baseline and dummy classifier;
- reproducible notebooks for sources, cleaning, training, and final evaluation;
- Render and Vercel deployment configuration.

## Local demo

```powershell
python -m pip install -r requirements-backend.txt
python -m uvicorn backend.app:app --reload --port 8000
```

In a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open `http://127.0.0.1:5173`. API documentation is available at `http://127.0.0.1:8000/docs`.

## Repository map

- `notebooks/` — Colab evidence for sources, cleaning, training, and evaluation;
- `data/processed/` — versioned market snapshots and model-ready features;
- `backend/` — FastAPI and portable inference code;
- `frontend/` — Vue 3 website;
- `docs/` — metrics, figures, deployment guide, presentation, and decisions;
- `scripts/` — repeatable data and notebook generation scripts.

## Evidence

The untouched chronological test contains 374 observations from 6 January 2025 to 7 July 2026. The frozen MLP achieved macro-F1 `0.339`, compared with `0.281` for the tree baseline and `0.169` for the dummy classifier. Absolute performance is modest, so every result is presented as an experimental educational signal.

See `notebooks/04_evaluation.ipynb` and `docs/final-test-metrics.json` for the complete evaluation.
