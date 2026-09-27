import { createRouter, createWebHistory } from 'vue-router'

import { useMeterFilterStore } from '@/stores/meterFilter'

import Dashboard from '@/views/Dashboard.vue'
const Plant = () => import('@/views/plant/index.vue')
const Inspection = () => import('@/views/inspection/index.vue')
const PanelClean = () => import('@/views/panel_clean/index.vue')
const Inverter = () => import('@/views/inverter/index.vue')
const PowerData = () => import('@/views/power_data/index.vue')
const Fault = () => import('@/views/fault/index.vue')
const SparePart = () => import('@/views/spare_part/index.vue')
const Transformer = () => import('@/views/transformer/index.vue')
const Switchgear = () => import('@/views/switchgear/index.vue')
const Meter = () => import('@/views/meter/index.vue')
const MeterDetail = () => import('@/views/meter/detail.vue')
const Weather = () => import('@/views/weather/index.vue')
const GridConnect = () => import('@/views/grid_connect/index.vue')
const Cable = () => import('@/views/cable/index.vue')
const Security = () => import('@/views/security/index.vue')
const Maintenance = () => import('@/views/maintenance/index.vue')
const DcBox = () => import('@/views/dc_box/index.vue')
const EnergySaving = () => import('@/views/energy_saving/index.vue')
const Training = () => import('@/views/training/index.vue')

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'dashboard', component: Dashboard },
    { path: '/plant', name: 'plant', component: Plant },
    { path: '/inspection', name: 'inspection', component: Inspection },
    { path: '/panel_clean', name: 'panel_clean', component: PanelClean },
    { path: '/inverter', name: 'inverter', component: Inverter },
    { path: '/power_data', name: 'power_data', component: PowerData },
    { path: '/fault', name: 'fault', component: Fault },
    { path: '/spare_part', name: 'spare_part', component: SparePart },
    { path: '/transformer', name: 'transformer', component: Transformer },
    { path: '/switchgear', name: 'switchgear', component: Switchgear },
    { path: '/meter', name: 'meter', component: Meter },
    { path: '/meter/:id', name: 'meter-detail', component: MeterDetail, props: true },
    { path: '/weather', name: 'weather', component: Weather },
    { path: '/grid_connect', name: 'grid_connect', component: GridConnect },
    { path: '/cable', name: 'cable', component: Cable },
    { path: '/security', name: 'security', component: Security },
    { path: '/maintenance', name: 'maintenance', component: Maintenance },
    { path: '/dc_box', name: 'dc_box', component: DcBox },
    { path: '/energy_saving', name: 'energy_saving', component: EnergySaving },
    { path: '/training', name: 'training', component: Training },
  ],
})

// 离开计量点模块（列表 -> 明细仍属同一模块，保留）时，清空旧的计量点位置查询条件。
router.afterEach((to, from) => {
  const leavingMeter = from.path.startsWith('/meter') && !to.path.startsWith('/meter')
  if (leavingMeter) {
    useMeterFilterStore().clearLocation()
  }
})

export default router
