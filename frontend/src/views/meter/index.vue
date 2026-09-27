<template>
  <section class="page" data-module="meter">
    <header class="page-head">
      <div>
        <h2>关口计量管理</h2>
        <p class="page-desc">维护计量表计，支持按计量点位置与检定有效期找到目标表计，并查看上次示数、当前示数与倍率。</p>
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
        <input v-model="store.filters.keyword" placeholder="按表计编号检索" />
      </label>
      <label class="filter-item">
        <span>计量点位置</span>
        <input v-model="store.filters.location" placeholder="如：110kV升压站关口计量柜" />
      </label>
      <label class="filter-item">
        <span>检定有效期至</span>
        <input v-model="store.filters.expireBefore" type="date" />
      </label>
      <label class="filter-item">
        <span>表计状态</span>
        <select v-model="store.filters.status">
          <option value="">全部状态</option>
          <option v-for="option in statuses" :key="option" :value="option">{{ option }}</option>
        </select>
      </label>
      <button class="btn" type="submit">查询</button>
      <button class="btn ghost" type="button" @click="resetFilters">重置条件</button>
    </form>

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
          <td :colspan="columns.length + 1" class="empty-state">
            <span v-if="invalidMessage" class="error-text">{{ invalidMessage }}</span>
            <span v-else-if="hasActiveFilters">未查询到匹配的计量表计，请调整计量点位置或检定有效期后重试</span>
            <span v-else>暂无关口计量数据，可先登记计量表计</span>
          </td>
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
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import { request } from '@/api/client'
import { useMeterFilterStore } from '@/stores/meterFilter'

type Row = Record<string, string | number | null>

const ENDPOINT = '/api/meter'
const columns = ["表计编号", "表计型号", "计量点位置", "倍率", "上次示数", "当前示数", "校验日期", "检定有效期", "表计状态"]
const actions = ["记录示数", "标记异常", "送检校验"]
const statuses = ["正常运行", "通讯中断", "示数异常", "待校验"]

const router = useRouter()
const store = useMeterFilterStore()

const rows = ref<Row[]>([])
const total = ref(0)
const errorMessage = ref('')
// 条件不合法（后端 400）单独展示在空结果处，与「确实无匹配记录」区分开。
const invalidMessage = ref('')

const stats = computed(() => [
  { label: "正常表计", value: rows.value.filter((row) => row.status === '正常运行').length },
  { label: "异常表计", value: rows.value.filter((row) => row.status === '通讯中断' || row.status === '示数异常').length },
  { label: "待校验表计", value: rows.value.filter((row) => row.status === '待校验').length },
])

const hasActiveFilters = computed(() =>
  Object.values(store.filters).some((value) => value.trim() !== ''),
)

function resetFilters() {
  store.reset()
  void reload()
}

function exportRows() {
  window.open(`${ENDPOINT}/export`, '_blank')
}

function openCreate() {
  errorMessage.value = '计量表计登记入口尚未接入审批流'
}

function openDetail(row: Row) {
  void router.push({ name: 'meter-detail', params: { id: String(row.id) } })
}

async function runAction(action: string, row: Row) {
  errorMessage.value = ''
  invalidMessage.value = ''
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

async function reload() {
  errorMessage.value = ''
  invalidMessage.value = ''
  const params = new URLSearchParams()
  if (store.filters.keyword.trim()) params.set('keyword', store.filters.keyword.trim())
  if (store.filters.location.trim()) params.set('location', store.filters.location.trim())
  if (store.filters.expireBefore.trim()) params.set('expire_before', store.filters.expireBefore.trim())
  if (store.filters.status.trim()) params.set('status', store.filters.status.trim())
  try {
    const response = await request(`${ENDPOINT}?${params.toString()}`)
    if (response.status === 400) {
      const payload = (await response.json().catch(() => null)) as { detail?: string } | null
      invalidMessage.value = payload?.detail ?? '查询条件不合法，请检查后重试'
      rows.value = []
      total.value = 0
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
