<template>
  <div>
    <div class="filters">
      <el-date-picker v-model="dates" type="daterange" value-format="YYYY-MM-DD" :clearable="false" start-placeholder="开始日期" end-placeholder="结束日期" style="width: 270px; flex-grow: 0" />
      <el-select v-model="dimension" style="width: 180px" placeholder="横轴维度">
        <el-option v-for="option in dimensions" :key="option.value" :value="option.value" :label="`按${option.label}汇总`" />
      </el-select>
      <el-select v-model="chartType" style="width: 130px"><el-option value="bar" label="柱状图" /><el-option value="line" label="折线图" /></el-select>
      <el-input v-model="employee" clearable placeholder="员工工号（可选）" style="width: 190px" />
      <el-button type="primary" :loading="loading" @click="fetchReport">查询</el-button>
    </div>
    <el-alert v-if="error" :title="error" type="error" :closable="false" />
    <p>累计有效工时：<strong>{{ (totalSeconds / 3600).toFixed(2) }} 小时</strong>（{{ formatDuration(totalSeconds) }}）</p>
    <p class="hint">{{ note || '横轴可选择人员、科室、项目、工作包、工作项、日期或月份；纵轴为有效工时（小时）。' }}</p>
    <div ref="chartElement" v-loading="loading" class="chart" />
    <el-table :data="rows" border max-height="400" empty-text="暂无工时记录">
      <el-table-column prop="name" :label="appliedLabel" min-width="220" />
      <el-table-column label="工时（小时）" width="160"><template #default="{ row }">{{ row.hours.toFixed(2) }}</template></el-table-column>
      <el-table-column label="累计时长" width="160"><template #default="{ row }">{{ formatDuration(row.seconds) }}</template></el-table-column>
    </el-table>
    <p class="hint">工时来自员工手动开始和结束的记录；未开始计时的工作不会自动计入。工时不能单独代表工作质量或工作量是否达标。</p>
  </div>
</template>
<script setup>
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import * as echarts from 'echarts'
import { getWorkTimeReportApi } from '../api'
import { formatDuration } from '../stores/workTime'
const today = new Intl.DateTimeFormat('sv-SE', { timeZone: 'Asia/Shanghai' }).format(new Date())
const dates = ref([`${today.slice(0, 7)}-01`, today]), dimension = ref('employee'), employee = ref(''), chartType = ref('bar')
const dimensions = [{ value: 'employee', label: '员工' }, { value: 'department', label: '科室' }, { value: 'project', label: '项目' },
  { value: 'work_package', label: '工作包' }, { value: 'work_item', label: '工作项' }, { value: 'day', label: '日期' }, { value: 'month', label: '月份' }]
const rows = ref([]), totalSeconds = ref(0), note = ref(''), error = ref(''), loading = ref(false), chartElement = ref(), appliedLabel = ref('员工')
let chart, observer, sequence = 0, disposed = false
function draw() {
  if (!chart) return
  chart.setOption({ tooltip: { trigger: 'axis', renderMode: 'richText' }, grid: { left: 65, right: 30, top: 45, bottom: 100 },
    xAxis: { type: 'category', name: appliedLabel.value, data: rows.value.map(x => x.name), axisLabel: { rotate: 25, width: 120, overflow: 'truncate' } },
    yAxis: { type: 'value', name: '有效工时（小时）', min: 0 },
    dataZoom: [{ type: 'slider', start: 0, end: rows.value.length > 30 ? 30 / rows.value.length * 100 : 100 }],
    series: [{ name: '有效工时（小时）', type: chartType.value, data: rows.value.map(x => x.hours), itemStyle: { color: '#409eff' } }],
    graphic: rows.value.length ? [] : [{ type: 'text', left: 'center', top: 'middle', style: { text: '暂无工时数据', fill: '#64748b' } }],
  }, true)
}
async function fetchReport() {
  if (!dates.value?.length) { error.value = '请选择统计日期'; return }
  const request = ++sequence, label = dimensions.find(x => x.value === dimension.value).label
  loading.value = true; error.value = ''
  try {
    const { data } = await getWorkTimeReportApi({ date_from: dates.value[0], date_to: dates.value[1], dimension: dimension.value, user_id: employee.value.trim() || undefined })
    if (disposed || request !== sequence) return
    rows.value = data.data.items; totalSeconds.value = data.data.total_seconds; note.value = data.data.note; appliedLabel.value = label; draw()
  } catch (e) {
    if (!disposed && request === sequence) { error.value = e.response?.data?.detail || '工时汇总加载失败'; rows.value = []; totalSeconds.value = 0; draw() }
  } finally { if (!disposed && request === sequence) loading.value = false }
}
watch(chartType, draw)
onMounted(() => { chart = echarts.init(chartElement.value); observer = new ResizeObserver(() => chart?.resize()); observer.observe(chartElement.value); fetchReport() })
onBeforeUnmount(() => { disposed = true; sequence++; observer?.disconnect(); chart?.dispose(); chart = null })
</script>
<style scoped>
.filters { display: flex; flex-wrap: wrap; align-items: center; gap: 12px; margin: 12px 0; }
.chart { width: 100%; height: 380px; }
.hint { color: #64748b; font-size: 13px; line-height: 1.6; }
</style>
