<!-- 积分查看 -->
<template>
  <div class="score-board-page">
    <el-card class="box-card" shadow="never">
      <!-- 与数据看板一致：周期分段按钮、前后切换和弹出日期选择。 -->
      <div v-if="showPeriodFilter" class="global-filter">
        <div class="period-segments" aria-label="统计周期">
          <button v-for="p in periodOptions" :key="p.value" :class="{ selected: queryMode === p.value }" @click="changeQueryMode(p.value)">
            {{ p.label }}
          </button>
        </div>
        <div class="period-navigation">
          <el-button text :icon="ArrowLeft" aria-label="上一周期" :disabled="atStart" @click="shiftPeriod(-1)" />
          <button class="period-label" @click="openPeriodPicker">{{ pickerLabel }} <el-icon><ArrowDown /></el-icon></button>
          <el-dialog v-model="pickerOpen" title="选择统计时间" width="min(480px, 92vw)" align-center append-to-body class="score-period-dialog" @opened="scrollToSelectedYear">
            <div class="scroll-period-picker" :class="{ 'year-only': queryMode === 'year' }">
              <!-- 年份倒序排列，可用滚轮或触摸上下滑动；滚动不会直接发起查询。 -->
              <div ref="yearList" class="year-list" tabindex="0" aria-label="年份列表，可上下滚动">
                <button 
                  v-for="y in pickerYears" 
                  :key="y" 
                  :data-year="y" 
                  :class="{ selected: draftYear === y }" 
                  :aria-pressed="draftYear === y" 
                  @click="selectPickerYear(y)"
                >{{ y }}年
                </button>
              </div>
              <div v-if="queryMode !== 'year'" class="period-grid" aria-label="选择月份或季度">
                <button 
                  v-for="n in queryMode === 'month' ? 12 : 4" 
                  :key="n" 
                  :class="{ selected: draftYear === selectedYear && n === (queryMode === 'month' ? monthNumber : selectedQuarter) }" 
                  @click="choosePeriod(n)">{{ queryMode === 'month' ? `${n}月` : `第${n}季度` }}
                </button>
              </div>
            </div>
          </el-dialog>
          <el-button text :icon="ArrowRight" aria-label="下一周期" :disabled="atEnd" @click="shiftPeriod(1)" />
          <el-button text :icon="Refresh" :loading="loading" @click="onPeriodChange">刷新</el-button>
        </div>
        <el-button
          v-if="activeTab === 'all'"
          class="export-excel-button"
          :icon="Download"
          :loading="exporting"
          :disabled="loading || savingRow || !peopleList.length"
          @click="exportExcel"
        >导出 Excel
        </el-button>
      </div>

    <!-- 主体内容区：Tabs 顶格显示 -->
      <el-tabs v-model="activeTab" class="custom-tabs">
        
        <!-- 页面一：个人积分 -->
        <el-tab-pane label="个人积分" name="personal">
          <div class="tab-content">
            
            <!-- 个人积分仪表盘：显示所选周期的基础得分与计算得分 -->
            <div class="dashboard-container">
              <div class="dashboard-card">
                <!-- 统计项 1：基础得分 -->
                <div class="stat-item">
                  <span class="stat-title">{{ periodLabel }}基础得分：</span>
                  <span class="stat-value" style="color: #475569;">{{ periodBaseScore || 0 }}</span>
                </div>
                
                <!-- 中间的分隔线 -->
                <div class="divider"></div>
                
                <!-- 统计项 2：计算得分 -->
                <div class="stat-item">
                  <span class="stat-title">{{ periodLabel }}计算得分：</span>
                  <span class="stat-value" style="color: #475569;">{{ periodCalculatedScore || 0 }}</span>
                </div>
                <div class="divider"></div>
                <div class="stat-item">
                  <span class="stat-title">{{ periodLabel }}进度扣分：</span>
                  <span class="stat-value penalty-text">{{ Number(currentPeriodPersonalData?.deducted_score || 0).toFixed(1) }} 分</span>
                </div>
              </div>
            </div>

            <p class="muted-text">进度扣分随所选周期显示：已入账月份采用确认时保存的结果，未入账月份显示实时预览；季、年可查看周期内各月扣分，正式总分仍以入账结果为准。已完成工作项的扣分计算至完成日期。</p>
            <!-- 个人积分详情：嵌套展开表格 -->
            <el-table
              :data="groupedMyDetails"
              v-loading="loading"
              border
              style="width: 100%"
              height="calc(100vh - 409px)"
              empty-text="当前周期暂无您的积分记录"
              :header-cell-style="{ background: '#f8fafc', color: '#334155' }"
            >
              <!-- 展开列：内层表格显示具体工作项、分值及扣除分值 -->
              <el-table-column type="expand">
                <template #default="{ row }">
                  <div class="inner-table-container">
                    <el-table :data="row.items" border size="small" :header-cell-style="{ background: '#f1f5f9' }">
                      <el-table-column prop="work_item_name" label="工作项名称" />
                      <el-table-column prop="work_item_standard" label="工作项标准" />
                      <el-table-column prop="deadline" label="截止时间" />
                      <el-table-column prop="difficulty" label="难度" width="80" align="center">
                      <template #default="{ row: item }">
                        <span>{{ item.difficulty || '-' }}</span>
                      </template>
                    </el-table-column>
                    <el-table-column prop="importance" label="重要度" width="80" align="center">
                      <template #default="{ row: item }">
                        <span>{{ item.importance || '-' }}</span>
                      </template>
                    </el-table-column>
                    <el-table-column prop="innovation" label="创新度" width="80" align="center">
                      <template #default="{ row: item }">
                        <span>{{ item.innovation || '-' }}</span>
                      </template>
                    </el-table-column>
                      <el-table-column prop="score" label="本周期得分" width="110" align="center">
                        <template #default="scope">
                          <span class="score-text" v-if="scope.row.score > 0">{{ scope.row.score }}</span>
                          <span class="muted-text" v-else>0</span>
                        </template>
                      </el-table-column>
                      <el-table-column prop="quality_score" label="质量分" width="100" align="center">
                        <template #default="scope">
                          <span :class="scope.row.quality_score < 0 ? 'penalty-text' : 'score-text'">{{ scope.row.quality_score ?? 0 }}</span>
                        </template>
                      </el-table-column>
                      <el-table-column prop="calculate_score" label="计算得分" width="110" align="center">
                        <template #default="scope">
                          <span class="score-text" v-if="scope.row.calculate_score > 0">{{ scope.row.calculate_score }}</span>
                          <span class="muted-text" v-else>0</span>
                        </template>
                      </el-table-column>
                      <el-table-column prop="deducted_score" label="进度扣分" width="110" align="center">
                        <template #default="scope">
                          <span class="penalty-text" v-if="scope.row.deducted_score > 0">-{{ scope.row.deducted_score }}</span>
                          <span class="muted-text" v-else>0</span>
                        </template>
                      </el-table-column>
                    </el-table>
                  </div>
                </template>
              </el-table-column>

              <!-- 外层表格：显示项目及工作包信息 -->
              <el-table-column prop="project_name" label="所属项目名称" min-width="150" />
              <el-table-column prop="project_code" label="所属项目编号" min-width="150" />
              <el-table-column prop="work_package_code" label="所属工作包" width="180" align="center" />
              <el-table-column prop="work_package_category" label="所属工作包类型" width="180" align="center" />
              <el-table-column prop="deducted_score" label="本周期进度扣分" width="150" align="center">
                <template #default="{ row }">
                  <span :class="row.deducted_score > 0 ? 'penalty-text' : 'muted-text'">{{ Number(row.deducted_score || 0).toFixed(1) }} 分</span>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-tab-pane>

        <!-- 页面二：所有人员积分 -->
        <el-tab-pane label="所有人员积分" name="all">
          <HistoricalScoreEntry v-if="String(currentUser?.role).toUpperCase() === 'ADMIN'" />

          <el-button type="primary" plain @click="openMyConfirmations">积分与自评提醒</el-button>
          <div class="tab-content">
            <p class="score-formula-tip">月度未入账时显示实时分数，仅供核对；入账后显示冻结结果。季度、年度仅汇总正式入账及历史数据。月度折算分在确认时锁定。</p>
            <p class="score-formula-tip">
              计算总分＝工作项计算得分＋技术提升＋日常管理－进度扣分；
              折算总分＝计算总分÷折算系数，
              折算系数＝本周期第5名计算总分÷90.01
              （不足5人取最高分，基准为0时系数取1）。
            </p>

            <!-- 【表格 1：月度表】当查询维度为“月份”时显示 -->
            <el-table
              v-if="queryMode === 'month'"
              :data="peopleList"
              v-loading="loading"
              stripe
              border
              style="width: 100%"
              height="calc(100vh - 332px)"
              empty-text="当前月份暂无积分数据"
              :header-cell-style="{ background: '#f8fafc', color: '#334155' }"
            >
              <el-table-column prop="username" label="人员" width="100" align="center" fixed="left" />
              <el-table-column label="入账状态" width="140">
                <template #default="{ row }">
                  <el-button v-if="isOwnScore(row) && row.confirmation_status === 'PENDING'" link type="primary" @click="runScoreAction('confirm')">确认积分</el-button>
                  <span v-else>{{ ({ IMPORTED: '历史补录已入账', PENDING: '待确认（未入账）', CONFIRMED: '本人已确认', AUTO: '逾期自动入账', PARTIAL: '部分月份未确认', SETTLED: '已入账', HISTORY: '历史积分', UNCONFIRMED: '暂存（未入账）' })[row.confirmation_status] || '历史积分' }}</span>
                </template>
              </el-table-column>
              <el-table-column label="月度自评" width="160" align="center">
                <template #default="{ row }">
                  <el-button v-if="isOwnScore(row) && ['REQUIRED', 'SUBMITTED'].includes(row.self_evaluation?.status)" link type="primary" @click="runScoreAction('evaluate')">{{ row.self_evaluation.status === 'SUBMITTED' ? '查看／修改自评' : '填写自评' }}</el-button>
                  <el-button v-else-if="row.self_evaluation?.status === 'SUBMITTED'" link type="primary" @click="evaluationDetail = row; evaluationVisible = true">查看自评</el-button>
                  <span v-else>{{ ({ REQUIRED: '待填写', WAITING: '待全员入账', NOT_REQUIRED: '无需填写' })[row.self_evaluation?.status] || '—' }}</span>
                </template>
              </el-table-column>
              <!-- 工作项基础分 -->
              <el-table-column label="工作项" align="center">
                <el-table-column prop="month_score" label="基础得分" min-width="80" align="center" />
                <el-table-column prop="calculate_score" label="计算得分" min-width="80" align="center" />
                <el-table-column prop="deducted_score" label="进度扣分" min-width="80" align="center" />
              </el-table-column>
              <!-- 额外加分项 -->
              <el-table-column label="技术提升" align="center">
                <el-table-column prop="tech_improve" label="合计" min-width="80" />
                <el-table-column prop="patent_score" label="专利" min-width="80" align="center">
                  <template #default="{ row }">
                    <el-input-number v-if="row.isEditing" v-model="row.patent_score" :step="0.5" size="small" style="width: 80px" controls-position="right" />
                    <span v-else>{{ row.summary_only ? '—' : (row.patent_score || 0) }}</span>
                  </template>
                </el-table-column>
                <el-table-column prop="knowledge_score" label="知识库" min-width="80" align="center" >
                  <template #default="{ row }">
                    <el-input-number v-if="row.isEditing" v-model="row.knowledge_score" :step="0.5" size="small" style="width: 80px" controls-position="right" />
                    <span v-else>{{ row.summary_only ? '—' : (row.knowledge_score || 0) }}</span>
                  </template>
                </el-table-column>
                <el-table-column prop="train_score" label="培训" min-width="80" align="center">
                  <template #default="{ row }">
                    <el-input-number v-if="row.isEditing" v-model="row.train_score" :step="0.5" size="small" style="width: 80px" controls-position="right" />
                    <span v-else>{{ row.summary_only ? '—' : (row.train_score || 0) }}</span>
                  </template>
                </el-table-column>
              </el-table-column>

              <el-table-column label="日常管理" align="center">
                <el-table-column prop="daily_manage" label="合计" min-width="80" />
                <el-table-column prop="deduct_score" label="扣分" min-width="80" align="center">
                  <template #default="{ row }">
                    <el-input-number v-if="row.isEditing" v-model="row.deduct_score" :step="0.5" size="small" style="width: 80px" controls-position="right" />
                    <span v-else>{{ row.summary_only ? '—' : (row.deduct_score || 0) }}</span>
                  </template>
                </el-table-column>
                <el-table-column prop="quality_event_score" label="质量事件" min-width="80" align="center">
                  <template #default="{ row }">
                    <el-input-number v-if="row.isEditing" v-model="row.quality_event_score" :step="0.5" size="small" style="width: 80px" controls-position="right" />
                    <span v-else>{{ row.summary_only ? '—' : (row.quality_event_score || 0) }}</span>
                  </template>
                </el-table-column>
                <el-table-column prop="carrier_inspection_score" label="载体检查" min-width="80" align="center">
                  <template #default="{ row }">
                    <el-input-number v-if="row.isEditing" v-model="row.carrier_inspection_score" :step="0.5" size="small" style="width: 80px" controls-position="right" />
                    <span v-else>{{ row.summary_only ? '—' : (row.carrier_inspection_score || 0) }}</span>
                  </template>
                </el-table-column>
              </el-table-column>

              <!-- 汇总计算项 -->
              <el-table-column prop="tech_growth_score" label="技术成长分" min-width="80" align="center" />
              <el-table-column prop="total_calculated" label="计算总分" min-width="80" align="center"/>
              <el-table-column prop="converted_score" label="折算总分" min-width="80" align="center" />
              <!-- 最终等级 -->
              <el-table-column prop="grade" label="等级" width="90" align="center" fixed="right">
                <template #default="{ row }">
                  <el-tag :type="getGradeTagType(row.grade)" effect="dark" size="small">
                    {{ row.grade || '-' }}
                  </el-tag>
                </template>
              </el-table-column>
              <!-- 操作：管理员/领导/科室可编辑 技术提升/日常管理 附加分 -->
              <el-table-column label="操作" width="80" align="center" fixed="right" v-if="isEdit">
                <template #default="{ row }">
                  <template v-if="!row.isEditing">
                    <el-button v-if="!row.month_locked" type="primary" link size="small" @click="startEdit(row)">编辑</el-button><span v-else>已锁定</span>
                  </template>
                  <template v-else>
                    <el-button type="success" link size="small" :loading="savingRow" @click="saveRow(row)">保存</el-button>
                    <el-button type="info" link size="small" @click="cancelEdit(row)">取消</el-button>
                  </template>
                </template>
              </el-table-column>
            </el-table>

            <!-- 【表格 2：季度表 / 年度表】当查询维度为“季度”或“年度”时显示 -->
            <el-table
              v-else
              :data="peopleList"
              v-loading="loading"
              stripe
              border
              style="width: 100%"
              height="calc(100vh - 340px)"
              empty-text="当前周期暂无积分数据"
              :header-cell-style="{ background: '#f8fafc', color: '#334155' }"
            >
              <el-table-column prop="username" label="人员" width="100" align="center" fixed="left" />
              <el-table-column label="入账状态" width="130">
                <template #default="{ row }">{{ ({ IMPORTED: '历史补录已入账', PENDING: '待确认（未入账）', CONFIRMED: '本人已确认', AUTO: '逾期自动入账', PARTIAL: '部分月份未确认', SETTLED: '已入账', HISTORY: '历史积分', UNCONFIRMED: '暂存（未入账）' })[row.confirmation_status] || '历史积分' }}</template>
              </el-table-column>
              
              <!-- 动态生成的子周期列：季度显示3个月，年度可根据后端返回显示12个月或4个季度 -->
              <el-table-column prop="period_1" :label="queryMode === 'quarter' ? '该季度第一个月' : '第一季度'" min-width="130" align="center">
                 <template #default="{ row }">
                  <span>{{ row.period_1 || 0 }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="period_2" :label="queryMode === 'quarter' ? '该季度第二个月' : '第二季度'" min-width="130" align="center">
                 <template #default="{ row }">
                  <span>{{ row.period_2 || 0 }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="period_3" :label="queryMode === 'quarter' ? '该季度第三个月' : '第三季度'" min-width="130" align="center">
                 <template #default="{ row }">
                  <span>{{ row.period_3 || 0 }}</span>
                </template>
              </el-table-column>
              <!-- 若为年度逻辑，可在下方继续使用 v-if="queryMode === 'year'" 增加更多子列 -->
               <el-table-column prop="period_4" v-if = "queryMode === 'year'" label = '第四季度' min-width="130" align="center">
                 <template #default="{ row }">
                  <span>{{ row.period_4 || 0 }}</span>
                </template>
              </el-table-column>

              <!-- 汇总列 -->
              <el-table-column prop="total_score" label="计算总分" min-width="100" align="center">
                <template #default="{ row }">
                  <span class="score-text">{{ row.total_score || 0 }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="final_calculated" label="折算总分" min-width="100" align="center" />
              
              <el-table-column prop="grade" label="等级" width="90" align="center" fixed="right">
                <template #default="{ row }">
                  <el-tag :type="getGradeTagType(row.grade)" effect="dark" size="small">
                    {{ row.grade || '-' }}
                  </el-tag>
                </template>
              </el-table-column>
            </el-table>

          </div>
        </el-tab-pane>

        <!-- 完成情况 / 项目汇总 已迁至「数据看板」页面 -->
      </el-tabs>
    </el-card>
    <el-dialog v-model="evaluationVisible" title="月度自评" width="min(720px, 94vw)" draggable append-to-body>
      <template v-if="evaluationDetail">
        <p>{{ evaluationDetail.username }} · 等级 {{ evaluationDetail.grade }}</p>
        <p>最近保存：{{ evaluationDetail.self_evaluation.submitted_at?.replace('T', ' ') }}</p>
        <div style="white-space: pre-wrap; overflow-wrap: anywhere; line-height: 1.8; max-height: 55vh; overflow-y: auto">{{ evaluationDetail.self_evaluation.content }}</div>
      </template>
      <template #footer><el-button @click="evaluationVisible = false">关闭</el-button></template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, onBeforeUnmount, ref, watch } from 'vue'
import HistoricalScoreEntry from '../../components/HistoricalScoreEntry.vue'
import { useRoute } from 'vue-router'
import { ArrowLeft, ArrowRight, ArrowDown, Refresh, Download } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { getPublicScoreBoardApi, getMyPeriodProgressDeductionsApi, updateMonthlyExtraScoreApi } from '../../api'
import { useUserStore } from '../../stores/user'
import { createScoreSnapshot, downloadScoreExcel } from '../../utils/scoreExport'

const route = useRoute()
const evaluationVisible = ref(false), evaluationDetail = ref(null)
const openMyConfirmations = () => window.dispatchEvent(new Event('open-score-confirmations'))
const userStore = useUserStore()
const currentUser = computed(() => userStore.userInfo)
const isOwnScore = row => currentUser.value?.id != null && String(row.user_id) === String(currentUser.value.id)
function runScoreAction(action) {
  window.dispatchEvent(new CustomEvent('score-row-action', { detail: { action, month: selectedMonth.value } }))
}

const activeTab = ref('personal')
const peopleList = ref([])
const personalProgress = ref(null)
const loading = ref(false)
const exporting = ref(false)

async function exportExcel() {
  if (exporting.value || loading.value || savingRow.value || !peopleList.value.length) return
  // 未保存的附加分与接口返回的总分可能不一致，先完成编辑再导出。
  if (peopleList.value.some(row => row.isEditing)) {
    ElMessage.warning('请先保存或取消正在编辑的积分，再导出 Excel')
    return
  }
  exporting.value = true
  try {
    const snapshot = createScoreSnapshot(peopleList.value, queryMode.value, periodLabel.value, selectedQuarter.value)
    await downloadScoreExcel(snapshot)
    ElMessage.success('已生成 Excel 文件，请查看浏览器下载记录')
  } catch (error) {
    console.error('导出积分失败:', error)
    ElMessage.error(error.message || '导出失败，请稍后重试')
  } finally {
    exporting.value = false
  }
}

// 查询维度与具体选择：默认按月份看当前月
const now = new Date()
const queryMode = ref('month')
const selectedMonth = ref(`${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`)
const selectedYear = ref(now.getFullYear())
const selectedQuarter = ref(Math.ceil((now.getMonth() + 1) / 3))
const periodOptions = [{ value: 'month', label: '月' }, { value: 'quarter', label: '季' }, { value: 'year', label: '年' }]
const pickerOpen = ref(false)
const draftYear = ref(selectedYear.value)
const yearList = ref(null)
const pickerYears = Array.from({ length: 101 }, (_, i) => 2100 - i)
function openPeriodPicker() {
  draftYear.value = selectedYear.value
  pickerOpen.value = true
}
function scrollToSelectedYear() {
  // 每次打开都定位到已选年份，仅滚动列表本身，不移动背景页面。
  const list = yearList.value
  const selected = list?.querySelector(`[data-year="${draftYear.value}"]`)
  if (selected) list.scrollTop = selected.offsetTop - list.clientHeight / 2 + selected.offsetHeight / 2
}
function selectPickerYear(year) {
  draftYear.value = year
  if (queryMode.value === 'year') choosePeriod(1)
}
const monthNumber = computed(() => Number(selectedMonth.value.slice(5, 7)))
const pickerLabel = computed(() => queryMode.value === 'month' ? selectedMonth.value : periodLabel.value)
const atStart = computed(() => selectedYear.value === 2000 && (queryMode.value === 'year' || (queryMode.value === 'quarter' ? selectedQuarter.value === 1 : monthNumber.value === 1)))
const atEnd = computed(() => selectedYear.value === 2100 && (queryMode.value === 'year' || (queryMode.value === 'quarter' ? selectedQuarter.value === 4 : monthNumber.value === 12)))

// 三种周期共享所选年月，切换模式时不会意外跳回当前年份。
function setSelectedDate(year, month) {
  selectedYear.value = year
  selectedMonth.value = `${year}-${String(month).padStart(2, '0')}`
  selectedQuarter.value = Math.ceil(month / 3)
}
function changeQueryMode(mode) {
  if (queryMode.value === mode) return
  queryMode.value = mode
  pickerOpen.value = false
  onPeriodChange()
}
function shiftPeriod(direction) {
  const step = queryMode.value === 'year' ? 12 : queryMode.value === 'quarter' ? 3 : 1
  const next = new Date(selectedYear.value, monthNumber.value - 1 + direction * step, 1)
  if (next.getFullYear() < 2000 || next.getFullYear() > 2100) return
  setSelectedDate(next.getFullYear(), next.getMonth() + 1)
  pickerOpen.value = false
  onPeriodChange()
}
function choosePeriod(n) {
  if (!Number.isInteger(draftYear.value) || draftYear.value < 2000 || draftYear.value > 2100) return
  const month = queryMode.value === 'month' ? n : queryMode.value === 'quarter' ? (n - 1) * 3 + 1 : monthNumber.value
  setSelectedDate(draftYear.value, month)
  pickerOpen.value = false
  onPeriodChange()
}

// 当前查看周期文案
const periodLabel = computed(() => {
  if (queryMode.value === 'month') {
    const [y, m] = selectedMonth.value.split('-')
    return `${y}年${+m}月`
  }
  if (queryMode.value === 'quarter') return `${selectedYear.value}年第${selectedQuarter.value}季度`
  if (queryMode.value === 'year') return `${selectedYear.value}年`
})

// 查询维度选择器：个人积分 / 所有人员积分 两个页签共用
const showPeriodFilter = computed(() => ['personal', 'all'].includes(activeTab.value))

// 所选周期总得分（仪表盘）
const periodBaseScore = computed(() => {
  // 如果没有数据，直接返回 0
  if (!currentPeriodPersonalData.value || !currentPeriodPersonalData.value.details) return 0
  // 遍历 details 数组，把所有的基础分 (score) 累加起来
  const total = currentPeriodPersonalData.value.details.reduce((sum, item) => sum + (item.score || 0), 0)
  // 保留两位小数，防止 JavaScript 浮点数计算出现 0.000000001 的精度问题
  return parseFloat(total.toFixed(2))
})
const periodCalculatedScore = computed(() => {
  if (!currentPeriodPersonalData.value || !currentPeriodPersonalData.value.details) return 0
  
  // 遍历 details 数组，把所有的计算分 (calculate_score) 累加起来
  const total = currentPeriodPersonalData.value.details.reduce((sum, item) => sum + (item.calculate_score || 0), 0)
  return parseFloat(total.toFixed(2))
})

// 提取当前选中周期下登录人的数据总览（用于下方详情展示的基础数据）
const currentPeriodPersonalData = computed(() => {
  if (!currentUser.value) return null
  const person = peopleList.value.find(p => String(p.user_id) === String(currentUser.value.id))
  if (!person || !personalProgress.value) return person || null

  const penalties = new Map(personalProgress.value.details.map(detail =>
    [`${detail.month}:${detail.work_item_id}`, detail]))
  const matched = new Set()
  const details = (person.details || []).map(detail => {
    const key = `${detail.month}:${detail.work_item_id}`
    const penalty = penalties.get(key)
    if (penalty) matched.add(key)
    return { ...detail, deducted_score: penalty?.deducted_score || 0 }
  })
  for (const [key, detail] of penalties) {
    if (!matched.has(key)) details.push(detail)
  }
  return { ...person, deducted_score: personalProgress.value.deducted_score, details }
})

// 计算个人的分组详情数据（外层项目/工作包，内层具体工作项+扣分）
const groupedMyDetails = computed(() => {
  const scoreDetails = currentPeriodPersonalData.value?.details || []
  // 旧版历史季度/年度直接按工作项去重；启用确认后的季度/年度则汇总各月快照。
  const legacyAggregate = queryMode.value !== 'month' &&
    currentPeriodPersonalData.value && !('confirmation_status' in currentPeriodPersonalData.value)
  const legacyDeductedItems = new Set()
  const map = {}
  const itemRows = {}   // work_item_id -> 行对象（跨月合并用）

  scoreDetails.forEach((item, index) => {
    const pName = item.project_name || '未归属项目'
    const pCode = item.project_code || '无项目编号'
    const wpId = item.work_package_id || '无编号'
    const wpCode = item.work_package_code || '无编号'
    const key = `${pName}_${wpId}`

    if (!map[key]) {
      map[key] = {
        project_name: pName,
        project_code: pCode,
        work_package_id: wpId,
        work_package_code: wpCode,
        work_package_category: item.work_package_category || '-',
        items: []
      }
    }

    // 同一工作项跨月只显示一行；得分与各月已入账进度扣分分别累加。
    const iid = item.work_item_id ?? `missing-${index}`
    if (!itemRows[iid]) {
      const row = {
        work_item_name: item.work_item_name || item.work_package_name || '未命名工作项',
        work_item_standard: item.work_item_standard || '-',
        deadline: item.work_item_deadline ? String(item.work_item_deadline).slice(0, 10) : '-',
        score: 0,
        quality_score: item.quality_score || 0,
        difficulty: item.work_item_difficulty || null,
        importance: item.work_item_importance || null,
        innovation: item.work_item_innovation || null,
        calculate_score: 0,
        deducted_score: 0
      }
      itemRows[iid] = row
      map[key].items.push(row)
    }
    const row = itemRows[iid]
    row.score += Number(item.score || 0)
    row.calculate_score += Number(item.calculate_score || 0)
    if (!legacyAggregate || !legacyDeductedItems.has(iid)) {
      row.deducted_score += Number(item.deducted_score || 0)
      legacyDeductedItems.add(iid)
    }
    // 质量分：同一工作项不同月可能不同，保留该工作项最近一条的值
    row.quality_score = item.quality_score ?? row.quality_score
    row.difficulty = item.work_item_difficulty
    row.importance = item.work_item_importance
    row.innovation = item.work_item_innovation
  })

  const groups = Object.values(map).map(group => ({
    ...group,
    deducted_score: group.items.reduce((sum, item) => sum + Number(item.deducted_score || 0), 0)
  }))
  const periodDeduction = Number(currentPeriodPersonalData.value?.deducted_score || 0)
  const detailedDeduction = groups.reduce((sum, group) => sum + group.deducted_score, 0)
  const summaryOnlyDeduction = Number((periodDeduction - detailedDeduction).toFixed(2))
  if (summaryOnlyDeduction > 0) {
    groups.push({
      project_name: '周期汇总数据', project_code: '-', work_package_id: 'summary-only',
      work_package_code: '-', work_package_category: '-', deducted_score: summaryOnlyDeduction,
      items: [{ work_item_name: '仅有汇总数据，无工作项明细', work_item_standard: '-', deadline: '-',
        score: 0, quality_score: 0, calculate_score: 0, deducted_score: summaryOnlyDeduction }]
    })
  }
  return groups
})

// 周期（年/季/月）变化时重新查询积分数据
const onPeriodChange = () => {
  fetchPublicScoreBoard()
}

// 按所选维度与具体年月/季/年拉取积分数据
let scoreRequestId = 0
onBeforeUnmount(() => { scoreRequestId++ })
const fetchPublicScoreBoard = async () => {
  const requestId = ++scoreRequestId
  peopleList.value = []
  personalProgress.value = null
  loading.value = true
  try {
    let year = '', month = '', quarter = ''
    if (queryMode.value === 'month') {
      year = selectedMonth.value ? +selectedMonth.value.slice(0, 4) : now.getFullYear()
      month = selectedMonth.value ? +selectedMonth.value.slice(5, 7) : now.getMonth() + 1
    } else if (queryMode.value === 'quarter') {
      year = selectedYear.value
      quarter = selectedQuarter.value
    } else if (queryMode.value === 'year') {
      year = selectedYear.value
    }
    const [boardResult, progressResult] = await Promise.allSettled([
      getPublicScoreBoardApi(queryMode.value, year, month, quarter),
      getMyPeriodProgressDeductionsApi(queryMode.value, year, month, quarter)
    ])
    if (requestId !== scoreRequestId) return
    if (boardResult.status === 'rejected') throw boardResult.reason
    const res = boardResult.value
    if (res?.data?.code === 200) {
      peopleList.value = res.data.data.people || []
    }
    if (progressResult.status === 'fulfilled' && progressResult.value?.data?.code === 200) {
      personalProgress.value = progressResult.value.data.data
    } else {
      ElMessage.warning('个人进度扣分加载失败，请刷新重试')
    }
  } catch (err) {
    if (requestId !== scoreRequestId) return
    console.error('获取公开积分数据报错:', err)
    ElMessage.error('获取公开积分数据失败')
  } finally {
    if (requestId === scoreRequestId) loading.value = false
  }
}

const getGradeTagType = (grade) => {
  if (grade === 'S') return 'danger'   // 红色
  if (grade === 'A') return 'warning'  // 橙色
  if (grade === 'B') return 'success'  // 绿色
  if (grade === 'C') return 'info'     // 灰色
  return ''                            // 默认 D 为无色/常规色
}

const isEdit = computed(() => {
  if (!currentUser.value) return false
  return ['ADMIN', 'DEPARTMENT', 'LEADER'].includes(String(currentUser.value.role).toUpperCase())
})

const editBackup = new Map()

const startEdit = (row) => {
  // 把该行原来的分数备份起来
  editBackup.set(row.user_id, {
    patent_score: row.patent_score,
    knowledge_score: row.knowledge_score,
    train_score: row.train_score,
    deduct_score: row.deduct_score,
    quality_event_score: row.quality_event_score,
    carrier_inspection_score: row.carrier_inspection_score
  })
  // 正式统计不含待确认分；编辑时加载原始附加分，避免用0覆盖。
  if (row._draft_extra) Object.assign(row, row._draft_extra)
  row.isEditing = true
}

const cancelEdit = (row) => {
  // 从备份中恢复原始数据
  const backup = editBackup.get(row.user_id)
  if (backup) {
    row.patent_score = backup.patent_score
    row.knowledge_score = backup.knowledge_score
    row.train_score = backup.train_score
    row.deduct_score = backup.deduct_score
    row.quality_event_score = backup.quality_event_score
    row.carrier_inspection_score = backup.carrier_inspection_score
  }
  // 关闭编辑模式
  row.isEditing = false
}

const savingRow = ref(false)
const saveRow = async (row) => {
  savingRow.value = true
  try {
    const res = await updateMonthlyExtraScoreApi({
      user_id: row.user_id,
      month: selectedMonth.value,
      updated_by_id: currentUser.value?.id,
      patent_score: row.patent_score,
      knowledge_score: row.knowledge_score,
      train_score: row.train_score,
      deduct_score: row.deduct_score,
      quality_event_score: row.quality_event_score,
      carrier_inspection_score: row.carrier_inspection_score
    })

    if (res?.data?.code === 200) {
      ElMessage.success('附加积分修改成功')
      row.isEditing = false
      fetchPublicScoreBoard()
    }
  } catch (err) {
    console.error(err)
    ElMessage.error(err.response?.data?.detail || '保存失败')
  } finally {
    savingRow.value = false
  }
}

function selectReminderMonth(month) {
  if (typeof month !== 'string' || !/^\d{4}-(0[1-9]|1[0-2])$/.test(month)) return false
  activeTab.value = 'all'
  queryMode.value = 'month'
  setSelectedDate(Number(month.slice(0, 4)), Number(month.slice(5)))
  return true
}
function showScoreMonth(event) {
  if (selectReminderMonth(event.detail)) fetchPublicScoreBoard()
}
watch(() => [route.query.tab, route.query.month], () => {
  if (route.query.tab === 'all' && selectReminderMonth(route.query.month)) fetchPublicScoreBoard()
})
onBeforeUnmount(() => {
  window.removeEventListener('monthly-score-confirmed', fetchPublicScoreBoard)
  window.removeEventListener('show-score-month', showScoreMonth)
})
onMounted(() => {
  window.addEventListener('monthly-score-confirmed', fetchPublicScoreBoard)
  window.addEventListener('show-score-month', showScoreMonth)
  if (route.query.tab === 'all') selectReminderMonth(route.query.month)
  fetchPublicScoreBoard()
})
</script>

<style scoped>
.score-board-page {
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

/* 顶部栏使用 flex 布局，自动占用按钮左侧空白，将按钮推到右侧 */
.global-filter > .export-excel-button {
  margin-left: auto;
  flex-shrink: 0;
}

/* 表格固定高度内部滚动，不受全局 flex:1 拉伸影响 */
:deep(.el-table) { flex: none !important; }

/* 仅修改积分查看的周期选择，不影响积分表格和编辑按钮。 */
.global-filter { 
  display: flex; 
  align-items: center;
   gap: 14px; 
   padding: 8px 4px 12px; 
   overflow-x: auto; 
  }

.period-segments { 
  display: inline-flex; 
  flex-shrink: 0; 
  padding: 3px; 
  background: #f1f2f4; 
  border-radius: 8px; 
  gap: 2px; 
}

.period-segments button, .period-grid button { 
  border: 0; 
  border-radius: 9px; 
  background: transparent; 
  padding: 9px 23px; 
  cursor: pointer; 
  font-size: 14px; 
  color: #8b929c; 
}

.period-segments button {
  padding: 5px 14px;
  font-size: 13px;
  border-radius: 6px;
}

.period-segments button.selected {
  color: #20242a;
  background: #fff;
  box-shadow: 0 2px 6px #00000008;
}

.period-navigation {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
}

.period-navigation :deep(.el-button) {
  height: 28px;
  padding: 5px 8px;
  font-size: 13px;
  margin-left: 0;
}

.period-label {
  background: transparent;
  border: 0;
  color: #20242a;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 5px;
  white-space: nowrap;
}

.scroll-period-picker {
  display: grid;
  grid-template-columns: 38% 62%;
  height: min(360px, 60vh);
  background: #fff;
}

.year-list {
  position: relative;
  overflow-y: auto;
  overscroll-behavior: contain;
  touch-action: pan-y;
  scrollbar-width: thin;
  padding: 8px 12px;
  border-right: 1px solid #f0f1f3;
}

.year-list button {
  display: block;
  width: 100%;
  border: 0;
  background: transparent;
  border-radius: 28px;
  padding: 11px 0;
  margin: 7px 0;
  font-size: 19px;
  color: #20242a;
  cursor: pointer;
}

.year-list button.selected {
  background: #409eff;
  color: #fff;
}

.period-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  grid-auto-rows: minmax(52px, 1fr);
  overflow-y: auto;
  overscroll-behavior: contain;
  touch-action: pan-y;
  padding: 8px 10px;
}

.period-grid button {
  padding: 10px 4px;
  color: #20242a;
  font-size: 19px;
}

.period-grid button.selected {
  color: #409eff;
  background: transparent;
}

.year-only {
  grid-template-columns: 1fr;
}

.year-only .year-list {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  align-content: start;
  border: 0;
  gap: 4px 10px;
}

.period-segments button:focus-visible, .period-label:focus-visible, .period-grid button:focus-visible, .year-list button:focus-visible {
  outline: 2px solid #409eff;
  outline-offset: -2px;
}

.employee-text {
  color: #1e293b;
  font-weight: 500;
}

.tip-text {
  color: #94a3b8;
  font-size: 13px;
}

/* 顶部仪表盘样式 */
.dashboard-container {
  margin-bottom: 20px;
}

.dashboard-card {
  display: flex;
  align-items: center;
  background-color: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  padding: 16px 0; /* 上下留白，左右由内部控制 */
}

.stat-item {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.divider {
  width: 1px;
  height: 32px;
  background-color: #cbd5e1;
}

.stat-title {
  font-size: 16px;
  color: #475569;
  font-weight: 500;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #000403c1;
}

@media (max-width: 600px) {
  .dashboard-card {
    flex-direction: column;
    padding: 16px;
    gap: 16px;
  }
  .divider {
    width: 100%;
    height: 1px;
  }
  .stat-item {
    width: 100%;
    justify-content: space-between;
    padding: 0 16px;
  }
}

/* 筛选条样式 */
.filter-bar {
  display: flex;
  align-items: center;
  margin-bottom: 16px;
  padding: 0 4px;
}

.filter-label {
  font-size: 14px;
  color: #475569;
  font-weight: 500;
  margin-right: 12px;
}

/* 内层表格容器留白调整 */
.inner-table-container {
  padding: 16px 48px;
  background-color: #fcfcfc;
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

.rank-badge {
  display: inline-flex;
  justify-content: center;
  align-items: center;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  font-weight: bold;
  color: #475569;
  background-color: #f1f5f9;
}

.rank-1 { background-color: #fef0f0; color: #f56c6c; }
.rank-2 { background-color: #fdf6ec; color: #e6a23c; }
.rank-3 { background-color: #f0f9eb; color: #67c23a; }

@media (max-width: 768px) {
  .dashboard-container {
    flex-direction: column;
    gap: 16px;
  }
}
/* 积分计算说明：小号灰色文字，窄屏时自动换行 */
.score-formula-tip {
  margin: 0 0 12px;
  padding: 0 2px;
  color: #64748b;
  font-size: 12px;
  line-height: 1.7;
  overflow-wrap: anywhere;
}
</style>
