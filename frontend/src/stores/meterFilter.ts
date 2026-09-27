import { reactive } from 'vue'
import { defineStore } from 'pinia'

/**
 * 关口计量读数查询条件。
 * 列表页与明细页共用：查看明细后返回列表，条件仍在；
 * 离开计量点模块（去别的页面）时由路由守卫清空「计量点位置」，避免旧位置带到下次值班。
 */
export const useMeterFilterStore = defineStore('meter-filter', () => {
  const filters = reactive({
    keyword: '',
    location: '',
    expireBefore: '',
    status: '',
  })

  function reset() {
    filters.keyword = ''
    filters.location = ''
    filters.expireBefore = ''
    filters.status = ''
  }

  function clearLocation() {
    filters.location = ''
  }

  return { filters, reset, clearLocation }
})
