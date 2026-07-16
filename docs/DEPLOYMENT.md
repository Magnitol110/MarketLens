# Public deployment

The recommended split is Vercel for the Vue frontend and Render for the FastAPI backend. Both can deploy directly from the same GitHub repository.

## 1. Deploy the API on Render

1. Push the repository to GitHub.
2. In Render choose **New → Blueprint** and select the MarketLens repository.
3. Render reads `render.yaml`; confirm the `marketlens-api` service.
4. Wait for `/api/health` to return `status: ok`.
5. Copy the public service URL, for example `https://marketlens-api.onrender.com`.

The production service uses `backend/marketlens_model.npz`, so PyTorch and a GPU are not needed for inference.

## 2. Deploy the frontend on Vercel

1. Import the same GitHub repository into Vercel.
2. Set **Root Directory** to `frontend`.
3. Keep framework preset **Vite**, build command `npm run build`, and output directory `dist`.
4. Add environment variable `VITE_API_BASE_URL` with the Render URL, without a trailing slash.
5. Deploy and copy the public Vercel URL.

## 3. Allow the frontend in Render

In the Render service add:

```text
MARKETLENS_CORS_ORIGINS=https://your-marketlens-site.vercel.app
```

Redeploy the API, then open the Vercel site and verify Dashboard, MSFT prediction, and all three chart ranges.

## Final smoke test

- `/api/health` reports the model as loaded;
- the dashboard shows a snapshot date rather than mock data;
- the MSFT page shows 1Y, 5Y, and MAX candles;
- dates and months are in English;
- refreshing `/stock/MSFT` does not return 404;
- the educational disclaimer remains visible.

Free Render services may need a short cold start after being idle. This is acceptable for the classroom MVP, but should be mentioned before the live demonstration.
