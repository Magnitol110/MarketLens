# MarketLens API

Read-only FastAPI service using a 55 KiB portable NumPy export of the frozen GPU-trained model. Production inference does not require PyTorch.

## Endpoints

- `GET /api/health` — service and model status.
- `GET /api/assets` — all currently trained asset models.
- `GET /api/predict/{symbol}` — latest five-day relative-market signal.
- `GET /api/history/{symbol}?period=1y|5y|max` — OHLCV candles.

## Local run

```powershell
python -m pip install -r requirements-backend.txt
python -m uvicorn backend.app:app --reload --port 8000
```

Interactive API documentation: `http://127.0.0.1:8000/docs`.

The current trained coverage is MSFT, but the endpoint and frontend contracts support adding more tickers without redesigning the product.
