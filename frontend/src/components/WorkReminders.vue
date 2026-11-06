<template>
  <div ref="entry" class="work-reminder-entry" :style="positionStyle">
    <el-badge :value="items.length" :max="99" :hidden="!items.length" class="reminder-badge">
      <button type="button" class="reminder-trigger" aria-label="打开待办提醒，可拖动调整位置" @pointerdown="startDrag" @click="openDrawer">
        <el-icon :size="20"><Bell /></el-icon><span>待办</span>
      </button>
    </el-badge>
  </div>

  <el-drawer v-model="visible" title="我的待办" direction="rtl" size="min(480px, 100vw)" append-to-body>
    <div class="reminder-panel">
      <div class="reminder-summary">
        <div><strong>{{ items.length }}</strong><span> 项待处理</span></div>
        <el-button text :loading="loading" @click="load">刷新</el-button>
      </div>
      <p class="reminder-explain">汇总审批、工作包分解、工作项到期、积分确认和自评待办。</p>
      <el-alert v-if="error" :title="error" type="error" :closable="false" class="reminder-error" />
      <div v-loading="loading" class="reminder-list">
        <el-empty v-if="!loading && !items.length && !error" description="暂无待办提醒" />
        <article v-for="reminder in items" :key="reminder.key" class="reminder-row" :class="`reminder-${reminder.severity}`">
          <div class="reminder-row-head">
            <el-tag :type="tagType(reminder.kind)" size="small" effect="light">{{ kindLabel(reminder.kind) }}</el-tag>
            <span v-if="reminder.deadline" class="reminder-date">{{ reminder.deadline }}</span>
          </div>
          <h3>{{ reminder.title }}</h3>
          <p>{{ reminder.description }}</p>
          <el-button type="primary" link @click="goToWork(reminder)">去完成 <el-icon><ArrowRight /></el-icon></el-button>
        </article>
      </div>
    </div>
  </el-drawer>
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { Bell, ArrowRight } from '@element-plus/icons-vue'
import { getWorkRemindersApi, getMyScoreConfirmationsApi } from '../api'

const router = useRouter()
const route = useRoute()
const visible = ref(false)
const items = ref([])
const loading = ref(false)
const error = ref('')
const entry = ref(null)
const positionStyle = ref({})
const storageKey = 'work-reminder-position'
const margin = 12
let timer = null
let requestId = 0
let drag = null
let suppressClick = false

const kindLabel = kind => (
  { overdue: '已超期', 
    due_today: '今天到期', 
    due_soon: '即将到期', 
    undecomposed: '未分解', 
    split_approval: '工作项审批', 
    package_change_approval: '工作包审批', 
    completion_approval: '完成审批', 
    score_confirmation: '积分确认', 
    score_evaluation: '月度自评' }
  )[kind] || '待办'
const tagType = kind => (
  { overdue: 'danger', 
    due_today: 'warning', 
    due_soon: 'warning', 
    undecomposed: 'info', 
    split_approval: 'primary', 
    package_change_approval: 'primary', 
    completion_approval: 'primary', 
    score_confirmation: 'warning',
    score_evaluation: 'primary' }
  )[kind] || 'info'

async function load() {
  if (document.hidden && !visible.value) return
  const id = ++requestId
  loading.value = true
  error.value = ''
  try {
    const [workResult, scoreResult] = await Promise.allSettled([getWorkRemindersApi(), getMyScoreConfirmationsApi()])
    if (id !== requestId) return
    const workItems = workResult.status === 'fulfilled' ? workResult.value.data?.data?.items || [] : []
    const records = scoreResult.status === 'fulfilled' ? scoreResult.value.data?.data?.records || [] : []
    const scoreItems = []
    for (const record of records) {
      if (record.status === 'PENDING') {
        scoreItems.push({ 
          key: `score-confirm-${record.id}`, 
          kind: 'score_confirmation', 
          severity: 'warning', 
          month: record.month, 
          title: `${record.month} 月积分待确认`, 
          description: '请前往所有人员积分，在本人所在行确认计算总分。' 
        })
      }
      if (record.self_evaluation?.status === 'REQUIRED') {
        scoreItems.push({ 
          key: `score-evaluation-${record.id}`, 
          kind: 'score_evaluation', 
          severity: 'warning', 
          month: record.month, 
          title: `${record.month} 月自评待填写`, 
          description: '请前往所有人员积分，在本人所在行填写月度自评。' 
        })
      }
    }
    items.value = [...scoreItems, ...workItems]
    if (workResult.status === 'rejected' || scoreResult.status === 'rejected') error.value = '部分待办加载失败，请刷新重试。'
  } finally {
    if (id === requestId) loading.value = false
  }
}

function clampPosition(x, y) {
  const width = entry.value?.offsetWidth || 100
  const height = entry.value?.offsetHeight || 48
  return {
    x: Math.max(margin, Math.min(x, window.innerWidth - width - margin)),
    y: Math.max(margin, Math.min(y, window.innerHeight - height - margin)),
  }
}

function place(x, y) {
  const point = clampPosition(x, y)
  positionStyle.value = { left: `${point.x}px`, top: `${point.y}px`, right: 'auto', bottom: 'auto' }
  return point
}

function restorePosition() {
  let saved
  try { saved = JSON.parse(localStorage.getItem(storageKey) || 'null') } catch { saved = null }
  if (Number.isFinite(saved?.x) && Number.isFinite(saved?.y)) {
    place(saved.x, saved.y)
  } else {
    place(window.innerWidth - (entry.value?.offsetWidth || 100) - 26,
      window.innerHeight - (entry.value?.offsetHeight || 48) - 100)
  }
}

function startDrag(event) {
  if (event.button !== 0) return
  const bounds = entry.value.getBoundingClientRect()
  drag = { id: event.pointerId, x: bounds.left, y: bounds.top, startX: event.clientX, startY: event.clientY, moved: false }
  event.currentTarget.setPointerCapture(event.pointerId)
  event.currentTarget.addEventListener('pointermove', moveDrag)
  event.currentTarget.addEventListener('pointerup', stopDrag, { once: true })
  event.currentTarget.addEventListener('pointercancel', stopDrag, { once: true })
}

function moveDrag(event) {
  if (!drag || event.pointerId !== drag.id) return
  const dx = event.clientX - drag.startX
  const dy = event.clientY - drag.startY
  if (Math.hypot(dx, dy) > 5) drag.moved = true
  if (drag.moved) place(drag.x + dx, drag.y + dy)
}

function stopDrag(event) {
  if (!drag || event.pointerId !== drag.id) return
  event.currentTarget.removeEventListener('pointermove', moveDrag)
  if (drag.moved) {
    suppressClick = true
    const bounds = entry.value.getBoundingClientRect()
    try { 
      localStorage.setItem(storageKey, JSON.stringify({ x: bounds.left, y: bounds.top })) 
    } 
      catch { /* Storage may be disabled. */ }
  }
  drag = null
}

function openDrawer() {
  if (suppressClick) { suppressClick = false; return }
  visible.value = true
  load()
}
function goToWork(reminder) {
  visible.value = false
  if (reminder.kind === 'score_confirmation' || reminder.kind === 'score_evaluation') {
    router.push({ name: 'ScoreBoard', query: { tab: 'all', month: reminder.month } }).then(() => {
      window.dispatchEvent(new CustomEvent('show-score-month', { detail: reminder.month }))
    })
    return
  }
  if (reminder.tab) {
    router.push({ path: '/review', query: { tab: reminder.tab } })
    return
  }
  router.push({
    path: `/project/${reminder.project_id}`,
    query: {
      work_package_id: String(reminder.work_package_id),
      page: String(reminder.package_page || 1),
      ...(reminder.work_item_id ? { work_item_id: String(reminder.work_item_id) } : {}),
    },
  })
}

watch(() => route.fullPath, () => load())
onMounted(() => { 
  restorePosition(); 
  window.addEventListener('resize', restorePosition); 
  window.addEventListener('monthly-score-confirmed', load); 
  load(); 
  timer = window.setInterval(load, 60000) 
})
onBeforeUnmount(() => { 
  window.removeEventListener('resize', restorePosition);
  window.removeEventListener('monthly-score-confirmed', load); 
  if (timer) window.clearInterval(timer); requestId++ 
  })
</script>

<style scoped>
.work-reminder-entry { position: fixed; right: 26px; bottom: 100px; z-index: 1900; }
.reminder-trigger { 
  display: flex; 
  align-items: center; 
  gap: 8px; 
  padding: 12px 18px; 
  border: 1px solid #1d5fe7; 
  border-radius: 999px; 
  background: #2168f3; 
  color: #fff; 
  box-shadow: 0 10px 28px rgba(28, 91, 201, .24); 
  font: inherit; 
  font-weight: 600; 
  cursor: grab; 
  touch-action: none; 
  user-select: none; 
  transition: transform .18s ease, 
  box-shadow .18s ease; 
}
.reminder-trigger:active { cursor: grabbing; }
.reminder-trigger:hover { transform: translateY(-2px); box-shadow: 0 14px 30px rgba(28, 91, 201, .31); }
.reminder-trigger:focus-visible { outline: 3px solid #93c5fd; outline-offset: 3px; }
.reminder-summary { 
  display: flex; 
  align-items: 
  center; 
  justify-content: space-between; 
  padding: 14px 16px; 
  background: #edf4ff; 
  border: 1px solid #d8e7fc; 
  border-radius: 12px; 
  color: #284669; 
}
.reminder-summary strong { color: #1555c7; font-size: 24px; }
.reminder-explain { margin: 12px 2px 18px; color: #71829a; font-size: 13px; }
.reminder-error { margin-bottom: 12px; }
.reminder-list { min-height: 180px; }
.reminder-row { 
  margin-bottom: 12px; 
  padding: 15px 16px 12px; 
  border: 1px solid #e5ebf4; 
  border-left: 3px solid #8da5c4; 
  border-radius: 10px; 
  background: #fff; 
}
.reminder-overdue { border-left-color: #e85d5d; }
.reminder-warning { border-left-color: #e8aa36; }
.reminder-row-head { display: flex; align-items: center; justify-content: space-between; gap: 8px; }
.reminder-date { color: #8391a5; font-size: 12px; }
.reminder-row h3 { margin: 10px 0 5px; color: #27354b; font-size: 15px; line-height: 1.5; }
.reminder-row p { margin: 0 0 8px; color: #728098; font-size: 13px; line-height: 1.5; }
.reminder-row .el-button { padding-left: 0; }
@media (max-width: 600px) { .work-reminder-entry { right: 16px; bottom: 100px; } }
</style>
