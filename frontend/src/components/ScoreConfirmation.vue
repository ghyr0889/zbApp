<template>
  <el-button v-if="pending.length || evaluationsPending.length" class="score-confirmation-entry" type="primary" @click="open">
    积分待确认（{{ pending.length }}）· 待自评（{{ evaluationsPending.length }}）
  </el-button>
  <el-dialog class="score-confirmation-dialog" top="4vh" v-model="visible" title="积分与自评待办提醒" width="min(720px, 94vw)" draggable append-to-body
    :close-on-click-modal="false" :close-on-press-escape="!saving" :show-close="!saving">
    <div class="confirmation-toolbar">
      <div class="confirmation-toolbar-row">
        <el-alert title="每月1—3日确认上月积分。确认后保存当次结果；4日起未确认的自动按系统得分入账并锁定。" type="info" :closable="false" />
        <el-button :loading="loading" :disabled="saving" @click="refresh">刷新</el-button>
      </div>
      <el-alert v-if="error" :title="error" type="error" :closable="false" />
    </div>
    <div v-loading="loading" class="confirmation-scroll" tabindex="0" aria-label="积分与自评待办提醒">
      <template v-if="!error">
        <p v-for="record in pending" :key="`confirm-${record.id}`" class="reminder-row"><span>{{ record.month }} 月积分待确认</span><el-button type="primary" plain @click="goToScore(record.month)">去确认</el-button></p>
        <p v-for="record in evaluationsPending" :key="`evaluation-${record.id}`" class="reminder-row"><span>{{ record.month }} 月自评待填写</span><el-button type="primary" plain @click="goToScore(record.month)">去填写</el-button></p>
        <p v-if="pending.length || evaluationsPending.length">请前往“所有人员积分”，选择对应月份，在本人所在行确认积分或填写自评。</p>
        <p v-else-if="!loading">暂无待确认积分或待填写自评。</p>
      </template>
    </div>
    <template #footer><el-button :disabled="saving" @click="visible = false">关闭</el-button></template>
  </el-dialog>
</template>
<script setup>
import { computed, ref, watch, onBeforeUnmount } from 'vue'
import { ElMessage, ElMessageBox, ElNotification } from 'element-plus'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'
import { getMyScoreConfirmationsApi, confirmMyScoreApi, saveScoreSelfEvaluationApi } from '../api'
const router = useRouter()
async function goToScore(month) {
  try {
    await router.push({ name: 'ScoreBoard', query: { tab: 'all', month } })
    window.dispatchEvent(new CustomEvent('show-score-month', { detail: month }))
    visible.value = false
    notification?.close()
  } catch { ElMessage.error('跳转失败，请重试') }
}
const store = useUserStore()
const records = ref([]), visible = ref(false), loading = ref(false), saving = ref(false), error = ref('')
const pending = computed(() => records.value.filter(r => r.status === 'PENDING'))
const evaluationsPending = computed(() => records.value.filter(r => r.self_evaluation?.status === 'REQUIRED'))
let timer, notification, generation = 0
const notified = new Set()
async function refresh() {
  const uid = store.userInfo?.id
  if (!uid || loading.value || saving.value) return
  const current = ++generation
  loading.value = true
  try {
    const { data } = await getMyScoreConfirmationsApi()
    if (current !== generation || store.userInfo?.id !== uid) return
    records.value = data.data.records || []
    error.value = ''
    const unseen = pending.value.filter(r => !notified.has(r.id))
    const unseenEvaluations = evaluationsPending.value.filter(r => !notified.has(`evaluation-${r.id}`))
    if (!pending.value.length && unseenEvaluations.length) {
      unseenEvaluations.forEach(r => notified.add(`evaluation-${r.id}`))
      notification?.close()
      notification = ElNotification({ title: '月度自评待填写', message: `${unseenEvaluations[0].month}月所有人员积分已入账，请填写本人自评。点击查看。`, type: 'warning', duration: 0, onClick: open })
    }
    if (unseen.length) {
      unseen.forEach(r => notified.add(r.id))
      notification?.close()
      notification = ElNotification({ title: '月度积分待确认', message: `请在本月3日结束前确认${unseen[0].month}月积分，逾期自动入账并锁定。点击查看。`,
        type: 'warning', duration: 0, onClick: open })
    }
    if (!pending.value.length && !evaluationsPending.value.length) notification?.close()
  } catch (e) {
    if (current === generation) error.value = e.response?.data?.detail || '积分确认数据加载失败，请刷新重试'
  } finally { if (current === generation) loading.value = false }
}
async function editEvaluation(record) {
  if (saving.value) return
  let value
  try {
    const result = await ElMessageBox.prompt('请填写本月工作完成情况、成绩与不足（最多500字）。', `${record.month}月自评`, {
      customClass: 'score-self-evaluation-prompt',
      inputType: 'textarea', inputValue: record.self_evaluation.content || '', draggable: true,
      confirmButtonText: '保存自评', cancelButtonText: '取消', closeOnClickModal: false,
      inputValidator: text => !!text?.trim() && text.trim().length <= 500 || '请填写1—500字自评'
    })
    value = result.value
  } catch { return }
  saving.value = true
  try {
    await saveScoreSelfEvaluationApi(record.id, value)
    ElMessage.success('自评已保存')
    window.dispatchEvent(new Event('monthly-score-confirmed'))
  } catch (e) { ElMessage.error(e.response?.data?.detail || '自评保存失败') }
  finally { saving.value = false; await refresh() }
}
function open() { visible.value = true; refresh() }
window.addEventListener('open-score-confirmations', open)
let rowActionBusy = false
async function handleRowAction(event) {
  if (rowActionBusy || saving.value || loading.value) {
    ElMessage.info('正在处理，请稍后重试')
    return
  }
  const { action, month } = event.detail || {}
  if (!['confirm', 'evaluate'].includes(action)) return
  rowActionBusy = true
  const uid = store.userInfo?.id
  try {
    await refresh()
    if (store.userInfo?.id !== uid) return
    if (error.value) { ElMessage.error(error.value); return }
    const record = records.value.find(r => r.month === month)
    if (!record) { ElMessage.warning('该月份暂无本人确认记录'); return }
    if (action === 'confirm' && record.status === 'PENDING') await confirm(record)
    else if (action === 'evaluate' && ['REQUIRED', 'SUBMITTED'].includes(record.self_evaluation?.status)) await editEvaluation(record)
    else ElMessage.info('记录状态已更新，请刷新积分表格')
  } finally { rowActionBusy = false; window.dispatchEvent(new Event('monthly-score-confirmed')) }
}
window.addEventListener('score-row-action', handleRowAction)
async function confirm(record) {
  if (saving.value) return
  try {
    await ElMessageBox.confirm(`确认${record.month}月计算总分 ${record.score.total_calculated}、折算总分 ${record.score.converted_score}？确认后结果锁定。`, '确认得分', { draggable: true })
  } catch { return }
  saving.value = true
  try {
    const { data } = await confirmMyScoreApi(record.id, record.fingerprint)
    ElMessage.success(data.message)
    window.dispatchEvent(new Event('monthly-score-confirmed'))
  } catch (e) { ElMessage.error(e.response?.data?.detail || '确认失败') }
  finally { saving.value = false; await refresh() }
}
watch(() => store.userInfo?.id, uid => {
  clearInterval(timer); notification?.close(); generation++; loading.value = false
  records.value = []; visible.value = false; notified.clear()
  if (uid) { refresh(); timer = setInterval(refresh, 60000) }
}, { immediate: true })
onBeforeUnmount(() => { window.removeEventListener('score-row-action', handleRowAction); window.removeEventListener('open-score-confirmations', open); generation++; clearInterval(timer); notification?.close() })
defineExpose({ open })
</script>
<style scoped>
.reminder-row { display: flex; justify-content: space-between; align-items: center; gap: 16px; }
.score-confirmation-entry { position: fixed; right: 24px; bottom: 24px; z-index: 2000; box-shadow: 0 4px 16px #2169c230; }
.confirmation-record { margin: 24px 0; }
.self-evaluation { padding: 16px; margin-top: 16px; background: #f0f7ff; border: 1px solid #d6e7f7; border-radius: 8px; }
.evaluation-hint { margin-top: 16px; color: #526780; }
.confirmation-record h3 { font-size: 17px; }
</style>

<style>
/* This dialog scrolls its records only; header and toolbar stay visible. */
body .el-dialog.score-confirmation-dialog {
  display: flex;
  flex-direction: column;
  max-height: 90vh;
  max-height: 90dvh;
  overflow: hidden;
}
.score-confirmation-dialog > .el-dialog__header,
.score-confirmation-dialog > .el-dialog__footer {
  flex: 0 0 auto;
}
.score-confirmation-dialog > .el-dialog__body {
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow: hidden;
}
.score-confirmation-dialog .confirmation-toolbar {
  flex: 0 0 auto;
  padding-bottom: 12px;
  background: var(--el-bg-color, #fff);
}
.score-confirmation-dialog .confirmation-toolbar-row {
  display: flex;
  align-items: center;
  gap: 12px;
}
.score-confirmation-dialog .confirmation-toolbar-row > .el-button {
  flex: 0 0 auto;
}
.score-confirmation-dialog .confirmation-toolbar-row > .el-alert {
  flex: 1;
  min-width: 0;
}
.score-confirmation-dialog .confirmation-scroll {
  min-height: 0;
  overflow: auto;
  overscroll-behavior: contain;
  scrollbar-gutter: stable;
}
</style>

<style>
.el-message-box.score-self-evaluation-prompt {
  width: min(720px, calc(100vw - 32px));
  max-width: calc(100vw - 32px);
}
.score-self-evaluation-prompt .el-textarea__inner {
  min-height: min(240px, 40vh) !important;
  line-height: 1.7;
  padding: 12px;
  resize: vertical;
}
</style>
