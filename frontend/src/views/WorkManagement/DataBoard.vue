<!-- 数据看板 -->
<template>
  <div class="dashboard-page">
    <el-alert v-if="!allowed" title="数据看板仅对领导和管理员开放" type="warning" :closable="false" />
    <template v-else>
      <!-- 顶部切换数据源 -->
      <header class="board-toolbar">
        <div class="toolbar-groups">
          <div class="segments" aria-label="统计周期">
            <button v-for="p in periods" :key="p.value" :class="{ selected: period === p.value }" @click="changePeriod(p.value)">
              {{ p.label }}
            </button>
          </div>
          <div class="segments" aria-label="统计维度">
            <button v-for="d in availableDimensions" :key="d.value" :class="{ selected: dimension === d.value }" @click="dimension = d.value">
              {{ d.label }}
            </button>
          </div>
          <!-- 只有“年＋时间”时，才允许选择横轴粒度。 -->
          <div v-if="period === 'year' && dimension === 'time'" class="segments" aria-label="时间粒度">
            <button :class="{ selected: yearGranularity === 'month' }" @click="yearGranularity = 'month'">
              按月
            </button>
            <button :class="{ selected: yearGranularity === 'quarter' }" @click="yearGranularity = 'quarter'">
              按季度
            </button>
          </div>
          <div class="segments" aria-label="统计单位">
            <button :class="{ selected: metric === 'count' }" @click="metric = 'count'">数量</button>
            <button :class="{ selected: metric === 'score' }" @click="metric = 'score'">分值</button>
          </div>
        </div>
        
        <div class="period-navigation">
          <el-button text :icon="ArrowLeft" aria-label="上一周期" :disabled="atStart" @click="shiftPeriod(-1)" />
          <button class="period-label" @click="openPeriodPicker">
            {{ periodLabel }} <el-icon><ArrowDown /></el-icon>
          </button>
          <el-dialog v-model="pickerOpen" width="min(480px, 92vw)" align-center append-to-body class="dashboard-period-dialog" @opened="scrollToSelectedYear">
            <div class="scroll-period-picker" :class="{ 'year-only': period === 'year' }">
              <!-- 年份倒序排列，可用滚轮或触摸上下滑动；滚动不会直接发起查询。 -->
              <div ref="yearList" class="year-list" tabindex="0" aria-label="年份列表，可上下滚动">
                <button v-for="y in pickerYears" :key="y" :data-year="y" :class="{ selected: draftYear === y }" :aria-pressed="draftYear === y" @click="selectPickerYear(y)">
                  {{ y }}年
                </button>
              </div>

              <div v-if="period !== 'year'" class="period-grid" aria-label="选择月份或季度">
                <button v-for="n in period === 'month' ? 12 : 4" :key="n" :class="{ selected: draftYear === year && n === (period === 'month' ? month : quarter) }" @click="choosePeriod(n)">
                  {{ period === 'month' ? `${n}月` : `第${n}季度` }}
                </button>
              </div>
            </div>
          </el-dialog>
          <el-button text :icon="ArrowRight" aria-label="下一周期" :disabled="atEnd" @click="shiftPeriod(1)" />
          <el-button text :icon="Refresh" :loading="loading" @click="fetchData">刷新</el-button>
        </div>
      </header>
      
      <el-alert v-if="error" :title="error" type="error" :closable="false" show-icon />
      <p class="calculation-note">按工作项截止日期归入周期，按当前负责人／科室／所属项目统计；完成情况为当前状态。分值为工作项配置分值，不是月度已填分。</p>
      <div v-loading="loading" class="board-content">
        <!-- 工作量统计模块 -->
        <div class="chart-grid">
          <section class="board-card">
            <div class="card-heading">
              <h2>工作量统计</h2>
              <div class="chart-tools">
                <el-button text :aria-pressed="showWorkloadDetails" @click="showWorkloadDetails = !showWorkloadDetails">{{ showWorkloadDetails ? '关闭详细数据' : '显示详细数据' }}</el-button>
                <el-button text :icon="Download" :disabled="loading || !!error || !rows.length" @click="exportChart('workload')">导出图片</el-button>
                <el-button 
                  text 
                  :icon="chartType === 'bar' ? TrendCharts : Histogram" 
                  :aria-label="chartType === 'bar' ? '切换折线图' : '切换柱状图'" 
                  @click="chartType = chartType === 'bar' ? 'line' : 'bar'">
                  {{ chartType === 'bar' ? '折线' : '柱状' }}
                </el-button>
                <el-button text :icon="FullScreen" aria-label="放大查看工作量图表" @click="expanded = true" />
              </div>
            </div>

            <DashboardChart ref="workloadChartRef" :style="{ height: workloadChartHeight + 'px' }" 
              v-if="rows.length && !error" 
              :option="barOption" 
              :label="`${dimensionLabel}工作量${chartType === 'bar' ? '柱状' : '折线'}图`" 
            />
            <el-empty v-else :description="error ? '数据加载失败，请重试' : '所选周期暂无工作项'" :image-size="100" />
          </section>

          <section class="board-card report-card">
            <div class="card-heading">
              <h2>{{ dimensionLabel }}报表</h2>
              <el-button text :icon="Download" :disabled="loading || !!error || reportTotal <= 0" @click="exportChart('report')">导出图片</el-button>
            </div>
            <DashboardChart ref="reportChartRef" v-if="reportTotal > 0 && !error" :option="pieOption" :label="`${dimensionLabel}${reportLabel}占比`" />
            <el-empty v-else :description="error ? '数据加载失败' : '暂无可展示的占比数据'" :image-size="100" />
            <div class="segments report-switch">
              <button 
                v-for="r in reportModes" 
                :key="r.value" 
                :class="{ selected: reportMode === r.value }" 
                @click="reportMode = r.value">{{ r.label }}
              </button>
            </div>
          </section>
        </div>

        <!-- 工作总览模块 -->
        <section class="board-card overview-report">
          <div class="card-heading">
            <h2>工作总览 
              <span class="overview-unit">单位：{{ unit }}</span>
            </h2>
            <el-input v-model="search" clearable :placeholder="`搜索${dimensionLabel}`" :prefix-icon="Search" style="width: 220px" />
          </div>
          <el-table :data="pagedRows" show-summary :summary-method="overviewSummary" :empty-text="error ? '数据加载失败' : '暂无匹配数据'" style="width:100%">
            <el-table-column prop="name" :label="dimensionLabel" min-width="200" />
            <el-table-column label="总计" min-width="110" align="right">
              <template #default="{ row }">{{ format(row.total) }}</template>
            </el-table-column>
            <el-table-column label="已完成" min-width="110" align="right">
              <template #default="{ row }">
                <span class="green">{{ format(row.completed) }}</span>
              </template>
            </el-table-column>
            <el-table-column label="未完成" min-width="110" align="right">
              <template #default="{ row }">
                <span class="coral">{{ format(row.pending) }}</span>
              </template>
            </el-table-column>
            <el-table-column label="完成占比" min-width="110" align="right">
              <template #default="{ row }">
                {{ row.total > 0 ? (row.completed / row.total * 100).toFixed(1) + '%' : '—' }}
              </template>
            </el-table-column>
          </el-table>

          <el-pagination 
            v-model:current-page="page" 
            :page-size="20" 
            :total="filteredRows.length" 
            layout="total, prev, pager, next" 
            class="report-pagination" />
        </section>

      </div>
      <el-dialog v-model="expanded" title="工作量统计" fullscreen destroy-on-close>
        <p>{{ periodLabel }} · 按{{ dimensionLabel }} · 单位：{{ unit }}</p>
        <el-button :aria-pressed="showWorkloadDetails" @click="showWorkloadDetails = !showWorkloadDetails">{{ showWorkloadDetails ? '关闭详细数据' : '显示详细数据' }}</el-button>
        <DashboardChart v-if="expanded" :option="barOption" label="工作量统计放大图" :style="{ height: `max(calc(100vh - 150px), ${workloadChartHeight}px)` }" />
      </el-dialog>
    </template>
  </div>
</template>

<script setup>
import { computed, ref, watch, onBeforeUnmount, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { ArrowLeft, ArrowRight, ArrowDown, Refresh, FullScreen, Histogram, TrendCharts, Search, Download } from '@element-plus/icons-vue'
import DashboardChart from '../../components/DashboardChart.vue'
import { getDashboardOverviewApi } from '../../api'
import { useUserStore } from '../../stores/user'
// 两个 ref 分别对应两张图表，避免导出错图。
const workloadChartRef = ref(null)
const reportChartRef = ref(null)
async function exportChart(kind) {
  if (loading.value || error.value) return
  try {
    // 等待 Vue 将最近的数量、分值或图形切换同步到子组件。
    await nextTick() // nextTick用来等待 Vue 完成本轮界面更新。
    if (loading.value || error.value) return
    const isReport = kind === 'report' // 扇形图

    if (isReport ? reportTotal.value <= 0 : !rows.value.length) return

    const instance = isReport ? reportChartRef.value : workloadChartRef.value 
    const name = isReport ? `${reportLabel.value}占比` : `工作量${chartType.value === 'bar' ? '柱状图' : '折线图'}`
    const granularity = dimension.value === 'time' && period.value === 'year'
      ? `_${yearGranularity.value === 'month' ? '按月' : '按季度'}` : ''
    const filename = `${periodLabel.value}_${dimensionLabel.value}${granularity}_${name}_${unit.value}`
    
    if (!instance?.exportImage(filename)) ElMessage.warning('暂无可导出的图表')
  } catch (e) {
    console.error('导出图表失败', e)
    ElMessage.error('图片导出失败，请重试')
  }
}
const user = useUserStore()
const allowed = computed(() => user.isAdmin || user.isLEADER)
const today = new Date()
const period = ref('month'), dimension = ref('department'), metric = ref('count'), yearGranularity = ref('month') //周期/维度/分值还是数量
const year = ref(today.getFullYear()), month = ref(today.getMonth() + 1)
const quarter = computed(() => Math.ceil(month.value / 3))
const draftYear = ref(year.value), pickerOpen = ref(false)
const yearList = ref(null)
const pickerYears = Array.from({ length: 101 }, (_, i) => 2100 - i) //生成年份列表
function openPeriodPicker() {
  draftYear.value = year.value
  pickerOpen.value = true
}
function scrollToSelectedYear() {
  // 每次打开都定位到已选年份，仅滚动列表本身，不移动背景页面。
  const list = yearList.value
  const selected = list?.querySelector(`[data-year="${draftYear.value}"]`)
  if (selected) list.scrollTop = selected.offsetTop - list.clientHeight / 2 + selected.offsetHeight / 2
}
function selectPickerYear(year) {
  //点击年份
  draftYear.value = year
  if (period.value === 'year') {
    choosePeriod(1)
  }
}
function changePeriod(newPeriod) {
  if (newPeriod === period.value) return
  period.value = newPeriod
  if (newPeriod === 'month' && dimension.value === 'time') dimension.value = 'department'
  pickerOpen.value = false
}

const periods = [
  { value: 'month', label: '月' }, 
  { value: 'quarter', label: '季' }, 
  { value: 'year', label: '年' }
]
const dimensions = [
  { value: 'department', label: '科室' }, 
  { value: 'person', label: '人员' }, 
  { value: 'project', label: '项目' },
  { value: 'time', label: '时间' }, 
]
const availableDimensions = computed(() => {
  if (period.value === 'month') return dimensions.filter(d => d.value !== 'time')
  return dimensions
})
const reportModes = [{ value: 'total', label: '总计' }, { value: 'completed', label: '已完成' }, { value: 'pending', label: '未完成' }]
const dimensionLabel = computed(() => dimensions.find(d => d.value === dimension.value).label)
const unit = computed(() => metric.value === 'count' ? '项' : '分')
const periodLabel = computed(() => period.value === 'year' ? `${year.value}年` : period.value === 'quarter' ? `${year.value}年第${quarter.value}季度` : `${year.value}-${String(month.value).padStart(2, '0')}`)
const atStart = computed(() => year.value === 2000 && (period.value === 'year' || (period.value === 'quarter' ? quarter.value === 1 : month.value === 1)))
const atEnd = computed(() => year.value === 2100 && (period.value === 'year' || (period.value === 'quarter' ? quarter.value === 4 : month.value === 12)))

function shiftPeriod(direction) {
  // 上一周期或下一周期
  const step = period.value === 'year' ? 12 : period.value === 'quarter' ? 3 : 1
  const next = new Date(year.value, month.value - 1 + direction * step, 1)
  if (next.getFullYear() < 2000 || next.getFullYear() > 2100) return
  year.value = next.getFullYear(); month.value = next.getMonth() + 1
}

watch(pickerOpen, value => { if (value) draftYear.value = year.value })

function choosePeriod(n) {
  //选择月份或季度
  if (!Number.isInteger(draftYear.value) || draftYear.value < 2000 || draftYear.value > 2100) return
  year.value = draftYear.value
  if (period.value !== 'year') month.value = period.value === 'quarter' ? (n - 1) * 3 + 1 : n
  pickerOpen.value = false
}
const raw = ref([]), loading = ref(false), error = ref('')
let requestId = 0

async function fetchData() {
  //向后端查询，加载数据
  const request = ++requestId
  raw.value = []; error.value = ''; page.value = 1
  if (!allowed.value) { loading.value = false; return }
  loading.value = true
  try {
    const { data } = await getDashboardOverviewApi(
      { period: period.value, 
        year: year.value, 
        month: month.value, 
        quarter: quarter.value, 
        dimension: dimension.value,
        year_granularity: period.value === 'year' && dimension.value === 'time' ? yearGranularity.value : undefined
      }
    )
    if (request === requestId) raw.value = data.data.items
  } catch (e) {
    if (request === requestId){ 
      error.value = typeof e.response?.data?.detail === 'string' ? e.response.data.detail : '加载失败，请确认后端已更新并重启后重试'
    }
  } finally { if (request === requestId) loading.value = false }
}

const rows = computed(() => raw.value.map(
  //两种数据（分值/数量）统一格式
  r => (
    { id: r.id,
      name: r.name,
      project_code: r.project_code, 
      total: r[metric.value], 
      completed: r[`completed_${metric.value}`], 
      pending: r[`pending_${metric.value}`] 
    }
  )
).sort((a,b) => b.total - a.total))

const totals = computed(
  //总量和数据格式
  () => rows.value.reduce(
    (sum, r) => (
      { total: sum.total + r.total, 
        completed: sum.completed + r.completed, 
        pending: sum.pending + r.pending 
      }
    ), 
    { total: 0, 
      completed: 0, 
      pending: 0 
    }
  )
)

const format = value => Number(value).toLocaleString('zh-CN', { maximumFractionDigits: metric.value === 'score' ? 2 : 0 }) //格式化函数
const showWorkloadDetails = ref(false)
const chartType = ref('bar'), expanded = ref(false), reportMode = ref('total') //图标类型
const reportLabel = computed(() => reportModes.find(r => r.value === reportMode.value).label)
const reportTotal = computed(() => totals.value[reportMode.value])
const ranking = computed(() => [...rows.value].sort((a,b) => b[reportMode.value] - a[reportMode.value]))
const colors = ['#ffad3b', '#ff7046', '#26bf8c', '#8ed163', '#4389f9', '#16b4d9', '#9377dc']
const colorOf = id => colors[raw.value.findIndex(r => r.id === id) % colors.length]
// 图例、总览和明细共用 rows，数量／分值切换不重复请求且口径保持一致。
const workloadNames = computed(() => rows.value.map(row => {
  const name = String(row.name || '')
  if (dimension.value === 'project') return row.project_code || name.match(/（([^（）]*)）$/)?.[1] || name
  const suffix = `（${row.id}）`
  return dimension.value === 'person' && name.endsWith(suffix) ? name.slice(0, -suffix.length) : name
}))
// 按字符估算85px标签宽度，最多两行，保留完整值供悬浮查看。
function shortAxisLabel(name) {
  const chars = Array.from(String(name))
  const lines = ['']
  let width = 0
  for (const char of chars) {
    const size = /[^\x00-\xff]/.test(char) ? 12 : 7
    if (width + size > 85 || char === '\n') {
      if (lines.length === 2) {
        lines[1] = Array.from(lines[1]).slice(0, -1).join('') + '…'
        return lines.join('\n')
      }
      lines.push(''); width = 0
    }
    if (char !== '\n') { lines[lines.length - 1] += char; width += size }
  }
  return lines.join('\n')
}
const workloadAxisNames = computed(() => workloadNames.value.map(shortAxisLabel))
const workloadChartHeight = computed(() => 376)
const barOption = computed(() => ({
  //描述图标内容和样式
  color: ['#4389f9', '#26bf8c', '#f16d73'], 
  animation: false, // 切换后立即完成绘制，导出与当前标注状态一致
  tooltip: { show: false, triggerOn: 'none' }, // 使用按钮统一控制数据标注
  legend: { top: 6, icon: 'circle' }, //总计、已完成、未完成图例
  grid: { left: 55, right: 24, top: 65, bottom: rows.value.length > 8 ? 45 : 20, containLabel: true }, //坐标绘图区的边距
  xAxis: { 
    type: 'category',
    triggerEvent: true,
    data: workloadNames.value, 
    axisTick: { show: false }, 
    axisLabel: { interval: 0, lineHeight: 16, formatter: (name, index) => workloadAxisNames.value[index] ?? name }, 
    axisLine: { lineStyle: { color: '#b7bdc5' } } 
  }, //横轴名称
  yAxis: { 
    type: 'value', 
    name: `工作量（${unit.value}）`, 
    minInterval: metric.value === 'count' ? 1 : undefined, 
    splitLine: { lineStyle: { color: '#f0f1f4' } } 
  }, //纵轴刻度和单位
  dataZoom: rows.value.length > 8 ? [{ type: 'slider', startValue: 0, endValue: 7, bottom: 8 }] : [], //数据较多时的滚动选择条
  series: reportModes.map(
    r => (
      { name: r.label, 
        type: chartType.value, 
        data: rows.value.map(row => row[r.value]), 
        barMaxWidth: 24,
        label: {
          show: showWorkloadDetails.value,
          position: 'top',
          distance: 6,
          color: '#334155',
          fontSize: 11,
          formatter: params => format(params.value)
        },
        emphasis: { label: { show: showWorkloadDetails.value } }, 
        itemStyle: { borderRadius: chartType.value === 'bar' ? [4,4,0,0] : 0 }, 
        smooth: false }
      )
    ) //真正要绘制的数据系列
}))

const pieOption = computed(() => ({
  tooltip: { trigger: 'item', renderMode: 'richText' },
  title: { text: `${reportLabel.value}占比`, left: 'center', top: '47%', textStyle: { fontSize: 15, fontWeight: 500 } },
  series: [{ type: 'pie', radius: ['43%', '65%'], center: ['50%', '50%'], minShowLabelAngle: 8,
    label: { formatter: '{b}\n{d}%', overflow: 'truncate', width: 80, fontSize: 11 },
    data: ranking.value.filter(r => r[reportMode.value] > 0).map(r => ({ name: r.name, value: r[reportMode.value], itemStyle: { color: colorOf(r.id) } })) }]
}))
const search = ref(''), page = ref(1)
const filteredRows = computed(
  //搜索结果
  () => rows.value.filter(r => r.name.toLowerCase().includes(search.value.trim().toLowerCase()))
)
// 汇总全部搜索结果，不只汇总当前分页；占比按总量计算。
function overviewSummary() {
  const sums = filteredRows.value.reduce((result, row) => {
    for (const key of ['total', 'completed', 'pending']) result[key] += Number(row[key]) || 0
    return result
  }, { total: 0, completed: 0, pending: 0 })
  return ['总计', format(sums.total), format(sums.completed), format(sums.pending),
    sums.total > 0 ? (sums.completed / sums.total * 100).toFixed(1) + '%' : '—']
}
const pagedRows = computed(() => filteredRows.value.slice((page.value - 1) * 20, page.value * 20)) //分页
watch(search, () => { page.value = 1 })

watch([period, year, month, dimension, allowed, yearGranularity], fetchData, { immediate: true })

onBeforeUnmount(() => { requestId++ })
</script>

<style scoped>
.dashboard-page { flex: 1; min-height: 0; overflow: auto; background: #f5f6f8; color: #20242a; padding: 24px; }
.board-toolbar { background: #fff; border-radius: 16px; padding: 22px 26px 14px; }
.board-title { display: flex; align-items: baseline; gap: 16px; margin-bottom: 20px; }
h1 { margin: 0; font-size: 23px; } .board-title span { font-size: 13px; color: #90969e; }
.toolbar-groups { display: flex; justify-content: space-between; gap: 16px; flex-wrap: wrap; }
.segments { display: inline-flex; padding: 5px; background: #f1f2f4; border-radius: 12px; gap: 4px; }
.segments button, .period-grid button { border: 0; border-radius: 9px; background: transparent; padding: 9px 23px; cursor: pointer; font-size: 14px; color: #8b929c; }
.segments button.selected { color: #20242a; background: #fff; box-shadow: 0 2px 6px #00000008; }
button:focus-visible { outline: 2px solid #409eff; outline-offset: 2px; }
.period-navigation { display: flex; justify-content: center; align-items: center; gap: 12px; padding-top: 14px; }
.period-label { background: transparent; border: 0; color: #20242a; font-size: 20px; font-weight: 600; cursor: pointer; display: flex; align-items: center; gap: 10px; }
.scroll-period-picker { display: grid; grid-template-columns: 38% 62%; height: min(360px, 60vh); background: #fff; }
.year-list { position: relative; overflow-y: auto; overscroll-behavior: contain; touch-action: pan-y; scrollbar-width: thin; padding: 8px 12px; border-right: 1px solid #f0f1f3; }
.year-list button { display: block; width: 100%; border: 0; background: transparent; border-radius: 28px; padding: 11px 0; margin: 7px 0; font-size: 19px; color: #20242a; cursor: pointer; }
.year-list button.selected { background: #409eff; color: #fff; }
.period-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); grid-auto-rows: minmax(52px, 1fr); overflow-y: auto; overscroll-behavior: contain; touch-action: pan-y; padding: 8px 10px; }
.period-grid button { padding: 10px 4px; color: #20242a; font-size: 19px; }
.period-grid button.selected { color: #409eff; background: transparent; }
.year-only { grid-template-columns: 1fr; }
.year-only .year-list { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); align-content: start; border: 0; gap: 4px 10px; }
.segments button:focus-visible, .period-label:focus-visible, .period-grid button:focus-visible, .year-list button:focus-visible { outline: 2px solid #409eff; outline-offset: -2px; }

.calculation-note { margin: 14px 4px; color: #8b929c; font-size: 12px; line-height: 1.8; }
.board-content { display: flex; flex-direction: column; gap: 22px; }
.board-card { background: #fff; border-radius: 16px; padding: 24px; min-width: 0; }
h2 { font-size: 18px; margin: 0; font-weight: 600; }
.report-card > h2 { text-align: center; }
.green { color: #26b886; } .coral { color: #ed6d75; }
.chart-grid { display: grid; grid-template-columns: minmax(0, 1.6fr) minmax(0, 1fr); gap: 22px; align-items: start; }
.card-heading { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-bottom: 20px; }
.chart-tools { display: flex; flex-wrap: wrap; justify-content: flex-end; } .chart-tools .el-button { margin: 0; color: #9299a2; }
.report-switch { display: flex; width: fit-content; margin: 0 auto 24px; }
.report-switch button { padding: 8px 12px; }
.report-pagination { justify-content: flex-end; margin-top: 20px; overflow-x: auto; }
.overview-unit { margin-left: 12px; font-size: 12px; font-weight: 400; color: #9399a2; }
.overview-report :deep(.el-table th.el-table__cell) { background: #fff; color: #303133; padding: 16px 0 !important; }
.overview-report :deep(.el-table td.el-table__cell) { padding: 14px 0 !important; }
@media (max-width: 1150px) { .chart-grid { grid-template-columns: 1fr; } }
@media (max-width: 650px) { .dashboard-page { padding: 12px; } .board-toolbar, .board-card { padding: 18px 12px; } .segments button { padding: 8px 13px; } .board-title { flex-wrap: wrap; gap: 8px; } .card-heading { flex-wrap: wrap; } }
</style>
