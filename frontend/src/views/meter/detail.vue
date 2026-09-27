<template>
  <section class="page" data-module="meter-detail">
    <header class="page-head">
      <div>
        <h2>计量表计明细</h2>
        <p class="page-desc">查看表计上次示数、当前示数与倍率，返回列表后查询条件继续保留。</p>
      </div>
      <div class="page-actions">
        <button class="btn" type="button" @click="goBack">返回计量表计列表</button>
      </div>
    </header>

    <p v-if="errorMessage" class="detail-error error-text">{{ errorMessage }}</p>

    <template v-else-if="entry">
      <div class="stat-row">
        <article class="stat-card">
          <span class="stat-label">上次示数</span>
          <strong class="stat-value">{{ entry['上次示数'] ?? '—' }}</strong>
        </article>
        <article class="stat-card">
          <span class="stat-label">当前示数</span>
          <strong class="stat-value">{{ entry['当前示数'] ?? '—' }}</strong>
        </article>
        <article class="stat-card">
          <span class="stat-label">倍率</span>
          <strong class="stat-value">{{ entry['倍率'] ?? '—' }}</strong>
        </article>
        <article class="stat-card">
          <span class="stat-label">倍率折算周期电量</span>
          <strong class="stat-value">{{ periodKwh ?? '—' }}</strong>
          <span class="stat-label">kWh（(当前示数 − 上次示数) × 倍率）</span>
        </article>
      </div>

      <table class="data-table detail-table">
        <tbody>
          <tr v-for="field in infoFields" :key="field">
            <th>{{ field }}</th>
            <td>
              {{ entry[field] ?? '—' }}
              <span
                v-if="field === '检定有效期' && expired"
                class="error-text"
              >（已过检定有效期，请尽快安排送检校验）</span>
            </td>
          </tr>
        </tbody>
      </table>
    </template>
  </section>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'

import { request } from '@/api/client'

type Entry = Record<string, string | number | null>

const props = defineProps<{ id: string }>()

const ENDPOINT = '/api/meter'
const infoFields = ["表计编号", "表计型号", "计量点位置", "校验日期", "检定有效期", "表计状态"]

const router = useRouter()
const entry = ref<Entry | null>(null)
const errorMessage = ref('')

const expired = computed(() => {
  const deadline = entry.value?.['检定有效期']
  return typeof deadline === 'string' && deadline < new Date().toISOString().slice(0, 10)
})

const periodKwh = computed(() => {
  if (!entry.value) return null
  const previous = Number(entry.value['上次示数'])
  const current = Number(entry.value['当前示数'])
  const ratio = Number(entry.value['倍率'])
  if (!Number.isFinite(previous) || !Number.isFinite(current) || !Number.isFinite(ratio) || ratio === 0) {
    return null
  }
  return ((current - previous) * ratio).toFixed(2)
})

function goBack() {
  void router.push({ name: 'meter' })
}

async function load() {
  errorMessage.value = ''
  entry.value = null
  try {
    const response = await request(`${ENDPOINT}/${props.id}`)
    if (response.status === 404) {
      const payload = (await response.json().catch(() => null)) as { detail?: string } | null
      errorMessage.value = payload?.detail ?? '计量表计不存在或已归档'
      return
    }
    if (!response.ok) {
      throw new Error('计量表计明细读取失败')
    }
    entry.value = await response.json()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '计量表计明细读取失败'
  }
}

watch(() => props.id, load, { immediate: true })
</script>

<style scoped>
.detail-table {
  max-width: 720px;
}
.detail-table th {
  width: 160px;
  background: #f8fafc;
}
.detail-error {
  margin: 12px 0;
}
</style>
