<!-- xiangmu/frontend/src/views/DataBoard.vue -->
<!-- 数据看板：由「积分查看」页拆分而出，承载 完成情况 / 项目汇总 两个看板 -->
<template>
  <div class="data-board-page">
    <el-card class="box-card" shadow="never">
      <!-- 无权限提示：两个看板都只对领导/管理员开放 -->
      <el-alert
        v-if="!canViewBoard"
        type="warning"
        show-icon
        :closable="false"
        title="数据看板仅对领导 / 管理员开放"
        description="当前角色没有查看完成情况和项目汇总的权限。" />

      <template v-else>
        <!-- 项目汇总：查看方式 + 查询维度 + 周期 -->
        <div v-if="showPeriodFilter" class="global-filter">
          <el-select v-model="summaryViewType" size="default"
            style="width: 150px" @change="fetchProjectSummary">
            <el-option label="查看项目" value="project" />
            <el-option label="查看工作包" value="work_package" />
          </el-select>
          <span class="filter-label">查询维度：</span>
          <el-select v-model="queryMode" size="default" style="width: 120px" @change="onPeriodChange">
            <el-option label="按月份" value="month" />
            <el-option label="按季度" value="quarter" />
            <el-option label="按年份" value="year" />
          </el-select>
          <el-date-picker
            v-if="queryMode === 'month'"
            v-model="selectedMonth"
            type="month"
            value-format="YYYY-MM"
            size="default"
            style="width: 150px"
            placeholder="选择月份"
            @change="onPeriodChange"
          />
          <template v-else-if="queryMode === 'quarter'">
            <el-select v-model="selectedYear" size="default" style="width: 110px" @change="onPeriodChange">
              <el-option v-for="y in yearOptions" :key="y" :label="`${y}年`" :value="y" />
            </el-select>
            <el-select v-model="selectedQuarter" size="default" style="width: 100px" @change="onPeriodChange">
              <el-option label="第1季度" :value="1" />
              <el-option label="第2季度" :value="2" />
              <el-option label="第3季度" :value="3" />
              <el-option label="第4季度" :value="4" />
            </el-select>
          </template>
          <el-select v-else-if="queryMode === 'year'" v-model="selectedYear" size="default" style="width: 110px" @change="onPeriodChange">
            <el-option v-for="y in yearOptions" :key="y" :label="`${y}年`" :value="y" />
          </el-select>
          <span class="period-label">当前查看：{{ periodLabel }}</span>
        </div>

        <!-- 完成情况：查询对象与月份 -->
        <div v-if="activeTab === 'situation'" class="view-controls">
          <el-select v-model="viewType" size="default" style="width: 150px" @change="onViewChange" placeholder="选择查看方式">
            <el-option label="查看项目" value="project" />
            <el-option label="查看工作包类别" value="category" />
          </el-select>
          <!-- 对象选择 -->
          <el-select v-model="situationTarget" filterable
            :placeholder="viewType === 'project' ? '选择项目' : '选择工作包类别'"
            style="width: 220px; margin-left: 12px" @change="fetchSituation">
            <el-option v-for="opt in situationOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
          </el-select>
          <!-- 月份（可选：空 = 累计全部月份） -->
          <el-date-picker v-model="situationMonth" type="month" value-format="YYYY-MM" clearable
            placeholder="全部月份（累计）" style="width: 160px; margin-left: 12px" @change="fetchSituation" />
        </div>

        <!-- 主体内容区：Tabs 顶格显示 -->
        <el-tabs v-model="activeTab" class="custom-tabs">
          <el-tab-pane label="自定义图表" name="custom" lazy>
            <CustomChartBoard v-if="activeTab === 'custom'" />
          </el-tab-pane>
          <!-- 完成情况 -->
          <el-tab-pane v-if="canViewSituation" label="完成情况" name="situation">
            <div class="tab-content">
              <el-table
                :data="situationPeople"
                v-loading="loading"
                border
                style="width: 100%"
                height="calc(100vh - 330px)"
                empty-text="该对象下暂无人员数据"
                :header-cell-style="{ background: '#f8fafc', color: '#334155' }"
                show-summary
                :summary-method="situationSummary">
                <el-table-column prop="username" label="人员" min-width="140" align="center" fixed="left" />
                <el-table-column prop="total_score" label="总分值" min-width="110" align="center">
                  <template #default="{ row }"><span class="score-text">{{ row.total_score ?? 0 }}</span></template>
                </el-table-column>
                <el-table-column prop="filled_score" label="已填分" min-width="110" align="center">
                  <template #default="{ row }"><span class="score-text">{{ row.filled_score ?? 0 }}</span></template>
                </el-table-column>
                <el-table-column prop="unfilled_score" label="未填分" min-width="110" align="center">
                  <template #default="{ row }">
                    <span :class="(row.unfilled_score ?? 0) < 0 ? 'penalty-text' : 'muted-text'">{{ row.unfilled_score ?? 0 }}</span>
                  </template>
                </el-table-column>
              </el-table>
            </div>
          </el-tab-pane>

          <!-- 项目汇总：项目 / 工作包 分值汇总（按 月/季/年） -->
          <el-tab-pane v-if="canViewSummary" label="项目汇总" name="summary">
            <div class="tab-content">
              <el-table
                :data="pagedSummaryItems"
                v-loading="loading"
                border
                style="width: 100%"
                height="calc(100vh - 330px)"
                :empty-text="summaryViewType === 'project' ? '暂无项目数据' : '暂无工作包数据'"
                :header-cell-style="{ background: '#f8fafc', color: '#334155' }"
                show-summary
                :summary-method="summaryTableSummary">
                <el-table-column :label="summaryViewType === 'project' ? '项目名称' : '工作包名称'" min-width="200" fixed="left" show-overflow-tooltip>
                  <template #default="{ row }"><span class="employee-text">{{ row.name }}</span></template>
                </el-table-column>
                <el-table-column prop="code" label="编号" min-width="150" align="center" show-overflow-tooltip />
                <el-table-column v-if="summaryViewType === 'work_package'" prop="parent_code" label="所属项目" min-width="150" show-overflow-tooltip />
                <el-table-column v-if="summaryViewType === 'work_package'" prop="category_name" label="类别" min-width="110" align="center" />
                <el-table-column prop="child_count" :label="summaryViewType === 'project' ? '所含工作包数' : '所含工作项数'" width="120" align="center">
                  <template #default="{ row }"><span class="score-text">{{ row.child_count || 0 }}</span></template>
                </el-table-column>
                <el-table-column v-if="summaryViewType === 'project'" prop="work_item_count" label="工作项总数" width="110" align="center">
                  <template #default="{ row }"><span class="score-text">{{ row.work_item_count || 0 }}</span></template>
                </el-table-column>
                <el-table-column prop="total_score" label="总分值" width="110" align="center">
                  <template #default="{ row }"><span class="score-text">{{ row.total_score ?? 0 }}</span></template>
                </el-table-column>
                <el-table-column prop="filled_score" label="已填分值" width="110" align="center">
                  <template #default="{ row }"><span class="score-text">{{ row.filled_score ?? 0 }}</span></template>
                </el-table-column>
                <el-table-column prop="unfilled_score" label="未填分值" width="120" align="center">
                  <template #default="{ row }">
                    <span :class="(row.unfilled_score ?? 0) < 0 ? 'penalty-text' : 'muted-text'">{{ row.unfilled_score ?? 0 }}</span>
                  </template>
                </el-table-column>
                <el-table-column label="状态" width="100" align="center">
                  <template #default="{ row }">
                    <el-tag v-if="row.closed_status" type="danger" size="small">已关闭</el-tag>
                    <el-tag v-else-if="row.complete_status" type="success" size="small">已完成</el-tag>
                    <el-tag v-else type="primary" size="small">进行中</el-tag>
                  </template>
                </el-table-column>
              </el-table>
              <div class="pagination-bar">
                <el-pagination
                  background layout="total, prev, pager, next, sizes"
                  :total="summaryItems.length"
                  :current-page="summaryPage"
                  :page-size="summaryPageSize"
                  :page-sizes="[10, 20, 50]"
                  @current-change="(p) => summaryPage = p"
                  @size-change="(s) => { summaryPageSize = s; summaryPage = 1 }" />
              </div>
            </div>
          </el-tab-pane>
        </el-tabs>
      </template>
    </el-card>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import {
  getCompletedSituationApi,
  getAllProjectsApi,
  getWorkCategoriesApi,
  getProjectSummaryApi
} from '../../api'
import { useUserStore } from '../../stores/user'

const userStore = useUserStore()
const currentUser = computed(() => userStore.userInfo)

const activeTab = ref('custom')
const loading = ref(false)

// ====================== 周期（年 / 季 / 月） ======================
const now = new Date()
const queryMode = ref('month')
const selectedMonth = ref(`${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`)
const selectedYear = ref(now.getFullYear())
const selectedQuarter = ref(1)
const yearOptions = computed(() => {
  const cur = now.getFullYear()
  return [cur - 3, cur - 2, cur - 1, cur, cur + 1]
})

// 当前查看周期文案
const periodLabel = computed(() => {
  if (queryMode.value === 'month') {
    const [y, m] = selectedMonth.value.split('-')
    return `${y}年${+m}月`
  }
  if (queryMode.value === 'quarter') return `${selectedYear.value}年第${selectedQuarter.value}季度`
  if (queryMode.value === 'year') return `${selectedYear.value}年`
  return ''
})

// 周期选择器只服务于「项目汇总」：完成情况用的是它自己的月份选择器
const showPeriodFilter = computed(() => activeTab.value === 'summary')

// 两个看板的权限口径一致，额外给一个总开关用于整页提示
const canViewSituation = computed(() => ['LEADER', 'ADMIN'].includes(String(currentUser.value?.role || '').toUpperCase()))
const canViewSummary = computed(() => ['LEADER', 'ADMIN'].includes(String(currentUser.value?.role || '').toUpperCase()))
const canViewBoard = computed(() => canViewSituation.value || canViewSummary.value)

const onPeriodChange = () => {
  if (activeTab.value === 'summary') handleFilterChange()
}

// ====================== 项目汇总（项目 / 工作包 → 分值进度） ======================
const summaryItems = ref([])                 // 当前视图的行数据（项目 或 工作包）
const summaryTotals = ref({})
const summaryViewType = ref('project')       // project | work_package
const summaryPage = ref(1)
const summaryPageSize = ref(20)
const pagedSummaryItems = computed(() => {
  const start = (summaryPage.value - 1) * summaryPageSize.value
  return summaryItems.value.slice(start, start + summaryPageSize.value)
})

const fetchProjectSummary = async () => {
  if (!currentUser.value || !canViewSummary.value) return
  loading.value = true
  try {
    const params = {
      currentUserId: currentUser.value.id,
      target_type: summaryViewType.value,
      period: queryMode.value,
      year: selectedYear.value
    }
    if (queryMode.value === 'month' && selectedMonth.value) {
      params.month = Number(String(selectedMonth.value).split('-')[1])
    }
    if (queryMode.value === 'quarter') {
      params.quarter = selectedQuarter.value
    }
    const res = await getProjectSummaryApi(params)
    if (res?.data?.code === 200) {
      const data = res.data.data || {}
      summaryTotals.value = data.totals || {}
      summaryItems.value = data.items || []
    }
  } catch (err) {
    console.error('获取项目汇总失败:', err)
    ElMessage.error(err.response?.data?.detail || '获取项目汇总失败')
  } finally {
    loading.value = false
  }
}

const handleFilterChange = () => {
  summaryPage.value = 1        // ← 关键：重置到第 1 页
  fetchProjectSummary()
}

// 项目汇总表格底部合计（个数 / 总分值 / 已填 / 未填）
const summaryTableSummary = ({ columns }) => {
  const sums = []
  columns.forEach((col, idx) => {
    if (idx === 0) { sums[idx] = '合计'; return }
    const key = col.property
    if (['child_count', 'work_item_count', 'total_score', 'filled_score', 'unfilled_score'].includes(key)) {
      const totalKey = col.property === 'child_count'
        ? (summaryViewType.value === 'project' ? 'work_package_count' : 'work_item_count')
        : col.property
      const val = summaryTotals.value?.[totalKey]
      sums[idx] = val == null ? '' : parseFloat(Number(val).toFixed(2))
    } else sums[idx] = ''
  })
  return sums
}

// ====================== 完成情况（项目/类别 → 人员分值进度） ======================
const viewType = ref('project')        // project | category
const situationTarget = ref('')        // 当前选中的 项目id 或 类别名
const situationMonth = ref('')         // 空 = 累计全部月份
const situationOptions = ref([])       // 项目或类别下拉选项
const situationPeople = ref([])        // 接口返回的人员行

const loadSituationOptions = async () => {
  try {
    if (viewType.value === 'project') {
      const res = await getAllProjectsApi()
      const list = res.data?.data || []
      situationOptions.value = list.map(p => ({ label: `${p.name}（${p.code || p.id}）`, value: String(p.id) }))
    } else {
      const res = await getWorkCategoriesApi()
      situationOptions.value = (res.data?.data || []).map(c => ({ label: c, value: c }))
    }
    situationTarget.value = situationOptions.value[0]?.value || ''
    situationPeople.value = []
    if (situationTarget.value) fetchSituation()
  } catch (err) {
    console.error(err)
    ElMessage.error('获取项目/类别列表失败')
  }
}

const onViewChange = () => {
  situationTarget.value = ''
  situationPeople.value = []
  loadSituationOptions()
}

const fetchSituation = async () => {
  if (!currentUser.value || !canViewSituation.value) return
  if (!situationTarget.value) return
  loading.value = true
  try {
    const params = {
      target_type: viewType.value,
      currentUserId: currentUser.value.id,
      month: situationMonth.value || undefined
    }
    if (viewType.value === 'project') params.target_id = Number(situationTarget.value)
    else params.category_name = situationTarget.value
    const res = await getCompletedSituationApi(params)
    if (res?.data?.code === 200) {
      situationPeople.value = res.data.data.people || []
    }
  } catch (err) {
    console.error(err)
    ElMessage.error(err.response?.data?.detail || '获取完成情况失败')
  } finally {
    loading.value = false
  }
}

// 表格底部合计（总分值 / 已填 / 未填）
const situationSummary = ({ columns, data }) => {
  const sums = []
  columns.forEach((col, idx) => {
    if (idx === 0) { sums[idx] = '合计'; return }
    const key = col.property
    if (['total_score', 'filled_score', 'unfilled_score'].includes(key)) {
      sums[idx] = parseFloat(data.reduce((s, r) => s + (Number(r[key]) || 0), 0).toFixed(2))
    } else sums[idx] = ''
  })
  return sums
}

// 切标签页时按需加载
watch(activeTab, (tab) => {
  if (tab === 'summary' && canViewSummary.value) {
    fetchProjectSummary()
  }
  if (tab === 'situation' && canViewSituation.value && !situationOptions.value.length) {
    loadSituationOptions()
  }
})

onMounted(() => {
  if (!canViewBoard.value) return
  if (activeTab.value === 'situation') loadSituationOptions()
  else if (activeTab.value === 'summary') fetchProjectSummary()
})
</script>

<style scoped>
.data-board-page {
  flex: 1;
  min-height: 0;
  overflow: auto;
  padding: 20px;
  animation: fadeIn 0.4s ease;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.box-card {
  border-radius: 12px;
  border: none;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
  min-height: calc(100vh - 120px);
}

.custom-tabs :deep(.el-tabs__item) {
  font-size: 16px;
  padding: 0 24px;
  height: 48px;
  line-height: 48px;
  font-weight: 600;
}

.custom-tabs :deep(.el-tabs__nav-wrap::after) {
  height: 1px;
  background-color: #e2e8f0;
}

.tab-content {
  padding: 16px 4px;
  animation: fadeIn 0.3s ease;
}

/* 表格固定高度内部滚动，不受全局 flex:1 拉伸影响 */
:deep(.el-table) { flex: none !important; }

/* 全局查询区样式 */
.global-filter {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  padding: 12px 4px 8px;
}

.view-controls {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  padding: 0 4px 8px;
}

.filter-label {
  font-size: 14px;
  color: #475569;
  font-weight: 500;
  margin-right: 12px;
}

.period-label {
  color: #475569;
  font-weight: 600;
  margin-left: 8px;
}

.pagination-bar {
  display: flex;
  justify-content: flex-end;
  padding: 12px 4px 0;
}

.employee-text {
  color: #1e293b;
  font-weight: 500;
}

/* 文字与数字样式 */
.score-text {
  color: #10b981;
  font-weight: 700;
  font-size: 15px;
}

.penalty-text {
  color: #ef4444;
  font-weight: 600;
}

.muted-text {
  color: #94a3b8;
}
</style>
