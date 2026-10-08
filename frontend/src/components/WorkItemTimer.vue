<template>
  <span v-if="!item.id || item.isNew">—</span>
  <span v-else-if="loading && seconds === null">加载中…</span>
  <span v-else-if="error" :title="error">—</span>
  <span v-else title="该工作项全部累计工时，包含正在计时的部分；约每30秒同步">
    {{ formatDuration(seconds) }}
  </span>
</template>

<script setup>
import { ref, watch, onBeforeUnmount } from 'vue'
import { getWorkItemTimeSummaryApi } from '../api'
import { useWorkTimeStore, formatDuration } from '../stores/workTime'
import { useUserStore } from '../stores/user'

const props = defineProps({ item: { type: Object, required: true }, locked: Boolean })
const timer = useWorkTimeStore(), user = useUserStore()
const seconds = ref(null), loading = ref(false), error = ref('')
let sequence = 0, disposed = false

// 只查询累计工时，不提供开始、结束或跳转入口。
async function refresh() {
  const request = ++sequence, token = user.accessToken
  if (!props.item.id || props.item.isNew || !token) {
    seconds.value = null; error.value = ''; loading.value = false
    return
  }
  loading.value = true
  try {
    const { data } = await getWorkItemTimeSummaryApi(props.item.id)
    if (disposed || request !== sequence || token !== user.accessToken) return
    seconds.value = data.data.total_seconds
    error.value = ''
  } catch (e) {
    if (disposed || request !== sequence || token !== user.accessToken) return
    // 查询失败不显示0，避免被误解为没有记录工时。
    seconds.value = null
    error.value = typeof e.response?.data?.detail === 'string' ? e.response.data.detail : '累计工时加载失败'
  } finally {
    if (!disposed && request === sequence) loading.value = false
  }
}
// 全局计时状态约每30秒校准；开始或结束后也会通知本列重新查询。
watch(() => [props.item.id, props.item.isNew, user.accessToken], () => {
  seconds.value = null
  refresh()
}, { immediate: true })
watch(() => timer.revision, refresh)
onBeforeUnmount(() => { disposed = true; sequence++ })
</script>
