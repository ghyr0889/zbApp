<template>
  <div v-if="timer.current || timer.syncError" class="work-time-status">
    <template v-if="timer.current">
      <el-tag :type="timer.current.status === 'RUNNING' ? 'success' : 'warning'">{{ timer.current.status === 'RUNNING' ? '计时中' : '历史未结束' }}</el-tag>
      <router-link :to="{ path: '/work-time', query: { view: 'timer', item: timer.current.work_item_id } }" class="item-name">{{ timer.current.work_item_name }}</router-link>
      <strong>{{ formatDuration(timer.elapsedSeconds) }}</strong>
      <router-link to="/work-time?view=timer">前往计时</router-link>
      <span class="hint">关闭页面不停止计时</span>
    </template>
    <span v-if="timer.syncError" class="error">{{ timer.syncError }}</span>
    <el-button v-if="timer.syncError" size="small" @click="refresh">重试同步</el-button>
  </div>
</template>
<script setup>
import { watch, onBeforeUnmount } from 'vue'
import { useUserStore } from '../stores/user'
import { useWorkTimeStore, formatDuration } from '../stores/workTime'
const user = useUserStore(), timer = useWorkTimeStore()
const refresh = () => { if (user.accessToken && !timer.busy) timer.refresh().catch(() => {}) }
watch(() => user.accessToken, () => { timer.reset(); refresh() }, { immediate: true })
// 页面显示只用单调时钟推算，后台状态每30秒同步，切回前台立即校准。
const ticker = setInterval(() => { timer.tick = performance.now() }, 1000)
const poller = setInterval(() => { if (document.visibilityState === 'visible') refresh() }, 30000)
const onVisible = () => { if (document.visibilityState === 'visible') refresh() }
document.addEventListener('visibilitychange', onVisible)
window.addEventListener('focus', onVisible)
onBeforeUnmount(() => {
  clearInterval(ticker); clearInterval(poller)
  document.removeEventListener('visibilitychange', onVisible)
  window.removeEventListener('focus', onVisible)
  timer.reset()
})
</script>
<style scoped>
.work-time-status { flex: 0 0 auto; display: flex; gap: 12px; align-items: center; flex-wrap: wrap; padding: 10px 20px; background: #edf7ff; border-bottom: 1px solid #d6e9f7; font-size: 13px; }
.item-name { max-width: 240px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; color: #2563eb; }
.hint { color: #64748b; } .error { color: #c2410c; }
</style>
