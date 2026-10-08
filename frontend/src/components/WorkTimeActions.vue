<template>
  <span class="work-time-actions">
    <el-button v-if="timer.current" size="small" type="danger" plain :disabled="timer.busy" @click="finish">结束本次</el-button>
  </span>
</template>
<script setup>
import { ElMessage, ElMessageBox } from 'element-plus'
import { useWorkTimeStore } from '../stores/workTime'
const timer = useWorkTimeStore()
async function finish() {
  const currentId = timer.current?.id, currentVersion = timer.current?.version
  try { await ElMessageBox.confirm('结束本次计时？这不会将工作项标记为完成，以后仍可重新开始计时。', '结束计时', { type: 'info' }) }
  catch { return }
  // 确认弹窗打开期间，其他标签页可能已经切换了计时，不能误结束新的记录。
  if (timer.current?.id !== currentId || timer.current?.version !== currentVersion) {
    ElMessage.info('当前计时已变化，请确认最新状态后重新操作')
    return
  }
  try { await timer.finish() }
  catch (error) { ElMessage.error(typeof error.response?.data?.detail === 'string' ? error.response.data.detail : '操作结果未确认，请查看同步后的计时状态再重试') }
}
</script>
<style scoped>.work-time-actions { display: inline-flex; gap: 6px; flex-wrap: wrap; } .work-time-actions .el-button { margin: 0; }</style>
