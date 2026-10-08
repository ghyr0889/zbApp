<template>
  <div class="work-time-page">
    <h2>工时记录</h2>
    <el-tabs v-model="tab">
      <el-tab-pane label="工作项计时" name="timer">
        <WorkTimeTracker :items="options" :loading="optionsLoading" :error="optionsError" @refresh="loadOptions" />
      </el-tab-pane>
      <el-tab-pane label="我的工时" name="mine">
        <div class="controls">
          <el-date-picker v-model="dates" type="daterange" value-format="YYYY-MM-DD" start-placeholder="开始日期" end-placeholder="结束日期" style="width: 260px; flex-grow: 0" />
          <el-select v-model="project" clearable filterable placeholder="全部项目" style="width: 180px" @change="pkg = undefined; item = undefined">
            <el-option v-for="option in projects" :key="option.id" :value="option.id" :label="option.name" />
          </el-select>
          <el-select v-model="pkg" clearable filterable placeholder="全部工作包" style="width: 180px" @change="item = undefined">
            <el-option v-for="option in packages" :key="option.id" :value="option.id" :label="option.name" />
          </el-select>
          <el-select v-model="item" clearable filterable placeholder="全部工作项" style="width: 210px">
            <el-option v-for="option in filteredItems" :key="option.id" :value="option.id" :label="`${option.name}（${option.id}）`" />
          </el-select>
          <el-button type="primary" @click="page = 1; fetchRecords()">查询</el-button>
          <el-button @click="resetFilters">重置</el-button>
        </div>
        <el-alert v-if="error" :title="error" type="error" :closable="false" />
        <p>所选期间累计：<strong>{{ formatDuration(totalSeconds) }}</strong>（{{ (totalSeconds / 3600).toFixed(2) }} 小时），共 {{ total }} 条记录</p>
        <el-table :data="records" v-loading="loading" border empty-text="所选条件下暂无工时记录">
          <el-table-column prop="project_name" label="项目" min-width="140" />
          <el-table-column prop="work_package_name" label="工作包" min-width="140" />
          <el-table-column prop="work_item_name" label="工作项" min-width="170" />
          <el-table-column label="状态" width="100"><template #default="{ row }"><el-tag :type="row.status === 'RUNNING' ? 'success' : 'info'">{{ statusNames[row.status] }}</el-tag></template></el-table-column>
          <el-table-column label="开始时间（北京）" width="180"><template #default="{ row }">{{ displayDate(row.started_at) }}</template></el-table-column>
          <el-table-column label="结束时间（北京）" width="180"><template #default="{ row }">{{ displayDate(row.ended_at) }}</template></el-table-column>
          <el-table-column label="本次累计" width="115"><template #default="{ row }">{{ formatDuration(row.elapsed_seconds) }}</template></el-table-column>
          <el-table-column label="所选期间工时" width="130"><template #default="{ row }">{{ formatDuration(row.period_seconds) }}</template></el-table-column>
        </el-table>
        <el-pagination class="pagination" v-model:current-page="page" :page-size="20" :total="total" layout="total, prev, pager, next" @current-change="fetchRecords" />
        <p class="hint">工时按开始到结束之间的时间统计。列表约每 30 秒同步；跨日、跨月记录仅统计落在筛选期间内的部分。</p>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { computed, onMounted, onBeforeUnmount, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { getWorkTimeOptionsApi, getMyWorkTimeApi } from '../../api'
import { useUserStore } from '../../stores/user'
import { useWorkTimeStore, formatDuration } from '../../stores/workTime'
import WorkTimeTracker from '../../components/WorkTimeTracker.vue'

const route = useRoute(), user = useUserStore(), timer = useWorkTimeStore()
const tab = ref(route.query.view === 'timer' ? 'timer' : route.query.item ? 'mine' : 'timer'), options = ref([]), project = ref(), pkg = ref()
const optionsLoading = ref(false), optionsError = ref('')
const item = ref(Number(route.query.item) || undefined)
const today = new Intl.DateTimeFormat('sv-SE', { timeZone: 'Asia/Shanghai' }).format(new Date())
const dates = ref([`${today.slice(0, 7)}-01`, today])
const records = ref([]), total = ref(0), totalSeconds = ref(0), page = ref(1), loading = ref(false), error = ref('')
const statusNames = { RUNNING: '计时中', PAUSED: '历史未结束', FINISHED: '已结束' }
const unique = (rows, key, name) => [...new Map(rows.map(x => [x[key], { id: x[key], name: x[name] }])).values()]
const projects = computed(() => unique(options.value, 'project_id', 'project_name'))
const packages = computed(() => unique(options.value.filter(x => !project.value || x.project_id === project.value), 'work_package_id', 'work_package_name'))
const filteredItems = computed(() => options.value.filter(x => (!project.value || x.project_id === project.value) && (!pkg.value || x.work_package_id === pkg.value)))
const displayDate = value => value ? new Date(value).toLocaleString('zh-CN', { timeZone: 'Asia/Shanghai', hour12: false }) : '—'
let sequence = 0, disposed = false
async function fetchRecords() {
  const request = ++sequence
  loading.value = true
  error.value = ''
  try {
    const { data } = await getMyWorkTimeApi({ date_from: dates.value?.[0], date_to: dates.value?.[1],
      project_id: project.value || undefined, work_package_id: pkg.value || undefined, work_item_id: item.value || undefined,
      page: page.value, page_size: 20 })
    // 防止较早的筛选请求覆盖后发请求。
    if (request !== sequence || disposed) return
    records.value = data.data.items
    total.value = data.data.total
    totalSeconds.value = data.data.total_seconds
  } catch (e) {
    if (request === sequence && !disposed) { error.value = e.response?.data?.detail || '工时记录加载失败，请重试'; records.value = []; total.value = 0; totalSeconds.value = 0 }
  } finally { if (request === sequence && !disposed) loading.value = false }
}
async function loadOptions() {
  optionsLoading.value = true; optionsError.value = ''
  try { const { data } = await getWorkTimeOptionsApi(); if (!disposed) options.value = data.data }
  catch { if (!disposed) optionsError.value = '工作项加载失败，请点击刷新重试' }
  finally { if (!disposed) optionsLoading.value = false }
}
function resetFilters() { dates.value = []; project.value = undefined; pkg.value = undefined; item.value = undefined; page.value = 1; fetchRecords() }
watch(() => timer.revision, () => { if (user.accessToken) fetchRecords() })
watch(() => route.fullPath, () => { item.value = Number(route.query.item) || undefined; tab.value = route.query.view === 'timer' ? 'timer' : route.query.item ? 'mine' : 'timer'; page.value = 1; fetchRecords() })
onMounted(() => { loadOptions(); fetchRecords() })
onBeforeUnmount(() => { disposed = true; sequence++ })
</script>

<style scoped>
.work-time-page { flex: 1; min-height: 0; overflow: auto; padding: 16px 20px; background: #fff; }
h2 { margin: 0 0 12px; font-size: 22px; }
.controls { display: flex; flex-wrap: wrap; gap: 10px; align-items: center; margin: 16px 0; }
.hint { color: #64748b; font-size: 13px; }
.pagination { margin: 18px 0; }
</style>
