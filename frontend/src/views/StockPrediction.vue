<template>
  <div class="flex flex-col h-full w-full app-bg overflow-hidden">
    <div class="flex justify-between items-center p-md px-lg border-b signal-header">
      <div class="flex flex-col gap-xs">
        <router-link to="/app/dashboard" class="text-muted text-xs uppercase tracking-wider font-medium">
          ← Market signals
        </router-link>
        <div class="flex items-baseline gap-md">
          <h1 class="font-mono font-extrabold text-xl text-primary">{{ ticker }}</h1>
          <span class="font-mono font-bold text-lg text-primary">${{ currentPrice.toFixed(2) }}</span>
          <span class="font-mono font-bold text-sm" :class="dailyChange >= 0 ? 'text-positive' : 'text-negative'">
            {{ dailyChange >= 0 ? '+' : '' }}{{ dailyChange.toFixed(2) }}%
          </span>
        </div>
      </div>

      <div class="forecast-summary">
        <span class="text-xs uppercase tracking-wider text-secondary">ML signal · 5 trading days</span>
        <strong class="text-lg uppercase" :class="signalClass">{{ signalText }}</strong>
        <span class="text-xs text-muted">
          {{ prediction ? `${Math.round(prediction.confidence * 100)}% confidence · vs ${prediction.benchmark}` : 'Loading frozen model…' }}
        </span>
      </div>
    </div>

    <div class="chart-toolbar border-b">
      <div class="flex items-center gap-xs">
        <button
          v-for="option in periodOptions"
          :key="option.value"
          type="button"
          class="range-button"
          :class="{ active: selectedPeriod === option.value }"
          @click="changePeriod(option.value)"
        >
          {{ option.label }}
        </button>
      </div>
      <span class="text-xs text-muted">
        Data snapshot: {{ prediction ? formatDate(prediction.as_of_date) : '—' }} · daily candles
      </span>
    </div>

    <div v-if="errorMessage" class="api-error">
      <strong>Live model API unavailable.</strong> {{ errorMessage }}
    </div>

    <div class="flex-1 w-full" style="min-height: 360px;" ref="chartContainerRef"></div>

    <div class="signal-note border-t">
      <span>Signal means expected performance relative to SPY, not guaranteed price direction.</span>
      <span>Experimental educational model · not investment advice.</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { CandlestickSeries, ColorType, createChart } from 'lightweight-charts'
import type { IChartApi, Time } from 'lightweight-charts'
import {
  getHistory,
  getPrediction,
  type HistoryPeriod,
  type PredictionResponse,
} from '../api'

const props = defineProps<{ ticker: string }>()

const prediction = ref<PredictionResponse | null>(null)
const currentPrice = ref(0)
const dailyChange = ref(0)
const errorMessage = ref('')
const selectedPeriod = ref<HistoryPeriod>('5y')
const chartContainerRef = ref<HTMLElement | null>(null)
const periodOptions: Array<{ label: string; value: HistoryPeriod }> = [
  { label: '1Y', value: '1y' },
  { label: '5Y', value: '5y' },
  { label: 'MAX', value: 'max' },
]

let chart: IChartApi | null = null
let candlestickSeries: any = null
let resizeObserver: ResizeObserver | null = null

const signalText = computed(() => prediction.value?.prediction ?? 'Loading')
const signalClass = computed(() => prediction.value ? `text-${prediction.value.prediction}` : 'text-muted')

const formatDate = (value: string) => new Intl.DateTimeFormat('en-US', {
  day: '2-digit',
  month: 'short',
  year: 'numeric',
  timeZone: 'UTC',
}).format(new Date(`${value}T00:00:00Z`))

async function loadPrediction() {
  prediction.value = await getPrediction(props.ticker)
  currentPrice.value = prediction.value.current_price
  dailyChange.value = prediction.value.daily_change_percent
}

async function loadHistory(period: HistoryPeriod) {
  const response = await getHistory(props.ticker, period)
  const candles = response.candles.map(candle => ({
    time: candle.time as Time,
    open: candle.open,
    high: candle.high,
    low: candle.low,
    close: candle.close,
  }))
  candlestickSeries?.setData(candles)
  chart?.timeScale().fitContent()
}

async function changePeriod(period: HistoryPeriod) {
  selectedPeriod.value = period
  try {
    errorMessage.value = ''
    await loadHistory(period)
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : 'Could not load chart history.'
  }
}

onMounted(async () => {
  if (!chartContainerRef.value) return

  chart = createChart(chartContainerRef.value, {
    localization: { locale: 'en-US', dateFormat: 'dd MMM yyyy' },
    layout: { background: { type: ColorType.Solid, color: '#0b0f19' }, textColor: '#94a3b8' },
    grid: {
      vertLines: { color: 'rgba(255, 255, 255, 0.05)' },
      horzLines: { color: 'rgba(255, 255, 255, 0.05)' },
    },
    rightPriceScale: { borderColor: 'rgba(255, 255, 255, 0.1)', mode: 2, autoScale: true },
    timeScale: { borderColor: 'rgba(255, 255, 255, 0.1)', timeVisible: true },
    crosshair: {
      vertLine: { color: '#64748b', width: 1, style: 1, labelBackgroundColor: '#1e293b' },
      horzLine: { color: '#64748b', width: 1, style: 1, labelBackgroundColor: '#1e293b' },
    },
  })

  candlestickSeries = chart.addSeries(CandlestickSeries, {
    upColor: '#10b981',
    downColor: '#ef4444',
    borderVisible: false,
    wickUpColor: '#10b981',
    wickDownColor: '#ef4444',
  })

  resizeObserver = new ResizeObserver(entries => {
    const entry = entries[0]
    if (!entry || entry.target !== chartContainerRef.value) return
    chart?.applyOptions({ height: entry.contentRect.height, width: entry.contentRect.width })
  })
  resizeObserver.observe(chartContainerRef.value)

  try {
    await Promise.all([loadPrediction(), loadHistory(selectedPeriod.value)])
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : 'Could not load MarketLens API.'
  }
})

onUnmounted(() => {
  resizeObserver?.disconnect()
  chart?.remove()
})
</script>

<style scoped>
.signal-header {
  background: rgba(15, 23, 42, 0.72);
}

.forecast-summary {
  min-width: 260px;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 2px;
  padding: 10px 14px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border-subtle);
  background: rgba(255, 255, 255, 0.03);
}

.chart-toolbar,
.signal-note {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-sm);
  padding: 8px var(--space-md);
  background: rgba(15, 23, 42, 0.42);
}

.range-button {
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-sm);
  padding: 4px 10px;
  color: var(--text-muted);
  background: transparent;
  cursor: pointer;
  font: inherit;
  font-size: 0.75rem;
  font-weight: 700;
}

.range-button:hover,
.range-button.active {
  color: white;
  border-color: var(--accent-primary);
  background: rgba(59, 130, 246, 0.18);
}

.api-error {
  padding: 8px var(--space-md);
  color: #fecaca;
  background: rgba(127, 29, 29, 0.35);
  border-bottom: 1px solid rgba(239, 68, 68, 0.35);
  font-size: 0.85rem;
}

.signal-note {
  color: var(--text-muted);
  font-size: 0.72rem;
}

.text-outperform { color: var(--signal-outperform-text); }
.text-neutral { color: var(--signal-neutral-text); }
.text-underperform { color: var(--signal-underperform-text); }

@media (max-width: 760px) {
  .signal-header,
  .chart-toolbar,
  .signal-note {
    align-items: flex-start;
    flex-direction: column;
  }

  .forecast-summary {
    min-width: 0;
    width: 100%;
    align-items: flex-start;
  }
}
</style>
