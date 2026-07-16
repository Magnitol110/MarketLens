export type SignalLabel = 'underperform' | 'neutral' | 'outperform'
export type HistoryPeriod = '1y' | '5y' | 'max'

export interface PredictionResponse {
  symbol: string
  as_of_date: string
  current_price: number
  daily_change_percent: number
  prediction: SignalLabel
  confidence: number
  probabilities: Record<SignalLabel, number>
  horizon_trading_days: number
  benchmark: string
  model_version: string
  disclaimer: string
}

export interface Candle {
  time: string
  open: number
  high: number
  low: number
  close: number
  volume: number
}

interface AssetsResponse {
  assets: PredictionResponse[]
}

interface HistoryResponse {
  symbol: string
  period: HistoryPeriod
  as_of_date: string
  candles: Candle[]
}

const apiBaseUrl = (import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/$/, '')

async function requestJson<T>(path: string): Promise<T> {
  const response = await fetch(`${apiBaseUrl}${path}`)
  if (!response.ok) {
    const detail = await response.text()
    throw new Error(detail || `Request failed with status ${response.status}`)
  }
  return response.json() as Promise<T>
}

export function getAssets(): Promise<AssetsResponse> {
  return requestJson<AssetsResponse>('/api/assets')
}

export function getPrediction(symbol: string): Promise<PredictionResponse> {
  return requestJson<PredictionResponse>(`/api/predict/${encodeURIComponent(symbol)}`)
}

export function getHistory(symbol: string, period: HistoryPeriod): Promise<HistoryResponse> {
  return requestJson<HistoryResponse>(
    `/api/history/${encodeURIComponent(symbol)}?period=${encodeURIComponent(period)}`,
  )
}
