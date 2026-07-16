<template>
  <UiContainer size="2xl" padded class="flex flex-col gap-xl h-full">
    <div class="mb-sm">
      <UiHeading level="1" class="mb-xs">Market Signal Workspace</UiHeading>
      <UiText color="secondary">
        Explore the trained models currently available in this educational research demo.
      </UiText>
    </div>

    <UiCard v-if="loading">
      <UiText color="secondary">Loading the latest model snapshot…</UiText>
    </UiCard>

    <UiCard v-else-if="errorMessage">
      <UiHeading level="4" class="mb-xs">API unavailable</UiHeading>
      <UiText color="secondary">{{ errorMessage }}</UiText>
    </UiCard>

    <UiCard v-else noPadding>
      <UiTable>
        <UiThead>
          <UiTr :hoverable="false">
            <UiTh>Ticker</UiTh>
            <UiTh>Coverage</UiTh>
            <UiTh>Five-day signal</UiTh>
            <UiTh>Confidence</UiTh>
            <UiTh>Snapshot</UiTh>
            <UiTh align="right">Action</UiTh>
          </UiTr>
        </UiThead>
        <UiTbody>
          <UiTr v-for="asset in assets" :key="asset.symbol">
            <UiTd width="12%">
              <UiText mono weight="bold" size="lg">{{ asset.symbol }}</UiText>
            </UiTd>
            <UiTd>
              <UiText color="secondary" size="sm">US Equity · trained model</UiText>
            </UiTd>
            <UiTd width="20%">
              <UiBadge :variant="asset.prediction" />
            </UiTd>
            <UiTd>
              <UiText mono weight="bold">{{ formatPercent(asset.confidence) }}</UiText>
            </UiTd>
            <UiTd>
              <UiText color="secondary" size="sm">{{ formatDate(asset.as_of_date) }}</UiText>
            </UiTd>
            <UiTd align="right">
              <UiButton variant="secondary" :to="`/app/stock/${asset.symbol}`">
                Analyze
              </UiButton>
            </UiTd>
          </UiTr>
        </UiTbody>
      </UiTable>
    </UiCard>

    <UiText size="xs" color="muted">
      Coverage grows ticker by ticker after a model passes the same chronological validation process.
    </UiText>
  </UiContainer>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { getAssets, type PredictionResponse } from '../api'
import UiContainer from '../components/ui/UiContainer.vue'
import UiHeading from '../components/ui/UiHeading.vue'
import UiText from '../components/ui/UiText.vue'
import UiCard from '../components/ui/UiCard.vue'
import UiBadge from '../components/ui/UiBadge.vue'
import UiButton from '../components/ui/UiButton.vue'
import UiTable from '../components/ui/UiTable.vue'
import UiThead from '../components/ui/UiThead.vue'
import UiTbody from '../components/ui/UiTbody.vue'
import UiTr from '../components/ui/UiTr.vue'
import UiTh from '../components/ui/UiTh.vue'
import UiTd from '../components/ui/UiTd.vue'

const assets = ref<PredictionResponse[]>([])
const loading = ref(true)
const errorMessage = ref('')

const formatPercent = (value: number) => `${Math.round(value * 100)}%`
const formatDate = (value: string) => new Intl.DateTimeFormat('en-US', {
  day: '2-digit',
  month: 'short',
  year: 'numeric',
  timeZone: 'UTC',
}).format(new Date(`${value}T00:00:00Z`))

onMounted(async () => {
  try {
    const response = await getAssets()
    assets.value = response.assets
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : 'Could not load model signals.'
  } finally {
    loading.value = false
  }
})
</script>
