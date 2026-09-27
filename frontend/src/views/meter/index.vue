<template>
  <section class="page" data-module="meter">
    <header class="page-head">
      <div>
        <h2>关口计量管理</h2>
        <p class="page-desc">维护计量表计，围绕表计编号、表计型号、计量点位置、倍率做登记、筛选与状态流转。</p>
      </div>
      <div class="page-actions">
        <button class="btn primary" type="button" @click="openCreate">登记计量表计</button>
        <button class="btn" type="button" @click="exportRows">导出关口计量清单</button>
      </div>
    </header>

    <div class="stat-row">
      <article v-for="item in stats" :key="item.label" class="stat-card">
        <span class="stat-label">{{ item.label }}</span>
        <strong class="stat-value">{{ item.value }}</strong>
      </article>
    </div>

    <form class="filter-bar" @submit.prevent="reload">
      <label class="filter-item">
        <span>表计编号</span>
        <input v-model="filters.keyword" placeholder="按表计编号检索" />
      </label>
      <label class="filter-item">
        <span>计量点位置</span>
        <input v-model="filters.location" placeholder="按计量点位置检索" />
      </label>
      <label class="filter-item">
        <span>检定有效期起</span>
        <input v-model="filters.validFrom" type="date" />
      </label>
      <label class="filter-item">
        <span>检定有效期止</span>
        <input v-model="filters.validTo" type="date" />
      </label>
      <button class="btn" type="submit">查询</button>
      <button class="btn ghost" type="button" @click="resetFilters">重置条件</button>
    </form>

    <section v-if="selected" class="detail-panel">
      <header class="detail-head">
        <strong>表计明细 · {{ selected['表计编号'] }}</strong>
        <span class="detail-tip">查询条件已保留，收起明细后可继续按原条件筛选</span>
        <button class="link" type="button" @click="closeDetail">收起明细</button>
      </header>
      <dl class="detail-grid">
        <div
          v-for="column in columns"
          :key="column"
          class="detail-item"
          :class="{ reading: readingFields.includes(column) }"
        >
          <dt>{{ column }}</dt>
          <dd>{{ selected[column] ?? '—' }}</dd>
        </div>
      </dl>
    </section>

    <table class="data-table">
      <thead>
        <tr>
          <th v-for="column in columns" :key="column">{{ column }}</th>
          <th>可执行动作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="row in rows" :key="String(row.id)">
          <td v-for="column in columns" :key="column">{{ row[column] ?? '—' }}</td>
          <td class="row-actions">
            <button class="link" type="button" @click="openDetail(row)">查看明细</button>
            <button
              v-for="action in actions"
              :key="action"
              class="link"
              type="button"
              @click="runAction(action, row)"
            >
              {{ action }}
            </button>
          </td>
        </tr>
        <tr v-if="!rows.length">
          <td :colspan="columns.length + 1" class="empty-state">{{ emptyHint }}</td>
        </tr>
      </tbody>
    </table>

    <footer class="page-foot">
      <span>共 {{ total }} 条关口计量记录</span>
      <span v-if="errorMessage" class="error-text">{{ errorMessage }}</span>
    </footer>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'

import { request } from '@/api/client'

type Row = Record<string, string | number | null>

const ENDPOINT = '/api/meter'
const columns = ["表计编号", "表计型号", "计量点位置", "倍率", "上次示数", "当前示数", "校验日期", "表计状态"]
const readingFields = ["倍率", "上次示数", "当前示数"]
const actions = ["记录示数", "标记异常", "送检校验"]
const statuses = ["正常运行", "通讯中断", "示数异常", "待校验"]
const stats = [{"label": "正常表计", "value": 0}, {"label": "异常表计", "value": 0}, {"label": "待校验表计", "value": 0}]

const rows = ref<Row[]>([])
const total = ref(0)
const errorMessage = ref('')
const conditionError = ref('')
const selected = ref<Row | null>(null)
const filters = ref({ keyword: '', location: '', validFrom: '', validTo: '' })

const hasConditions = computed(() =>
  Boolean(filters.value.keyword || filters.value.location || filters.value.validFrom || filters.value.validTo),
)

const emptyHint = computed(() => {
  if (conditionError.value) {
    return conditionError.value
  }
  if (hasConditions.value) {
    return '按当前计量点位置与检定有效期查询无匹配表计（无结果），可调整条件后重试'
  }
  return '暂无关口计量数据，可先登记计量表计'
})

// 离开计量点时，旧表计的明细位置一并清空，避免停留在上一个计量点的表计上
watch(() => filters.value.location, () => {
  selected.value = null
})

function resetFilters() {
  filters.value = { keyword: '', location: '', validFrom: '', validTo: '' }
  selected.value = null
  void reload()
}

function exportRows() {
  window.open(`${ENDPOINT}/export`, '_blank')
}

function openCreate() {
  errorMessage.value = '计量表计登记入口尚未接入审批流'
}

function closeDetail() {
  selected.value = null
}

async function openDetail(row: Row) {
  errorMessage.value = ''
  try {
    const response = await request(`${ENDPOINT}/${row.id}`)
    if (!response.ok) {
      throw new Error('计量表计明细读取失败')
    }
    selected.value = (await response.json()) as Row
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '计量表计明细读取失败'
  }
}

async function runAction(action: string, row: Row) {
  errorMessage.value = ''
  try {
    const response = await request(`${ENDPOINT}/${row.id}/actions`, {
      method: 'POST',
      body: JSON.stringify({ action }),
    })
    if (!response.ok) {
      throw new Error('关口计量动作未生效，请稍后重试')
    }
    await reload()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '关口计量操作失败'
  }
}

function rejectConditions(message: string) {
  conditionError.value = `查询条件不合法：${message}`
  rows.value = []
  total.value = 0
}

async function reload() {
  errorMessage.value = ''
  conditionError.value = ''
  const { keyword, location, validFrom, validTo } = filters.value
  if (validFrom && validTo && validFrom > validTo) {
    rejectConditions('检定有效期起不能晚于检定有效期止，请调整后再查')
    return
  }
  const query = new URLSearchParams()
  if (keyword) query.set('keyword', keyword)
  if (location) query.set('location', location)
  if (validFrom) query.set('valid_from', validFrom)
  if (validTo) query.set('valid_to', validTo)
  try {
    const response = await request(`${ENDPOINT}?${query.toString()}`)
    if (response.status === 400) {
      const payload = (await response.json().catch(() => null)) as { detail?: string } | null
      rejectConditions(payload?.detail ?? '请检查计量点位置与检定有效期的填写')
      return
    }
    if (!response.ok) {
      throw new Error('计量表计列表读取失败')
    }
    const payload = await response.json()
    rows.value = payload.items ?? []
    total.value = payload.total ?? rows.value.length
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '关口计量列表读取失败'
  }
}

onMounted(reload)
</script>
