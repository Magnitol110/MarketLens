# MarketLens frontend

Vue 3 + TypeScript + Vite interface for the MarketLens API.

## Local development

```powershell
npm install
npm run dev
```

Vite proxies `/api` to `http://127.0.0.1:8000`. To use a remote API, copy `.env.example` to `.env` and set `VITE_API_BASE_URL`.

## Verification

```powershell
npm run build
npm test -- --run
```

## Vercel

Use `frontend` as the Root Directory, `npm run build` as the build command, and `dist` as the output directory. Add `VITE_API_BASE_URL` with the public Render API URL before deploying.
