<!-- xiangmu/frontend/src/views/ScoreBoard.vue -->
<template>
  <div class="score-board-page">
    <el-card class="box-card" shadow="never">
      <!-- 全局查询区：选择查看哪个月 / 哪个季度 / 哪一年 -->
      <div class="global-filter">
        <span v-if="showPeriodFilter" class="filter-label">查询维度：</span>
        <el-select v-if="showPeriodFilter" v-model="queryMode" size="default" style="width: 120px" @change="onQueryChange">
          <el-option label="按月份" value="month" />
          <el-option label="按季度" value="quarter" />
          <el-option label="按年份" value="year" />
        </el-select>
        <el-date-picker
          v-if="queryMode === 'month' && showPeriodFilter"
          v-model="selectedMonth"
          type="month"
          value-format="YYYY-MM"
          size="default"
          style="width: 150px"
          placeholder="选择月份"
          @change="onPeriodChange"
        />
        <template v-else-if="queryMode === 'quarter' && showPeriodFilter">
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
        <el-select v-else-if="queryMode === 'year' && showPeriodFilter" v-model="selectedYear" size="default" style="width: 110px" @change="onPeriodChange">
          <el-option v-for="y in yearOptions" :key="y" :label="`${y}年`" :value="y" />
        </el-select>
        <span v-if="showPeriodFilter" class="period-label">当前查看：{{ periodLabel }}</span>
      </div>

    <!-- 视图切换：项目 / 工作包类别 -->
      <div class="view-controls">
      <el-select v-if="activeTab === 'situation'" v-model="viewType" size="default" style="width: 150px" @change="onViewChange"placeholder="选择查看方式">
        <el-option label="查看项目" value="project" />
        <el-option label="查看工作包类别" value="category" />
      </el-select>
        <!-- 对象选择 -->
        <el-select v-if="activeTab === 'situation'" v-model="situationTarget" filterable
          :placeholder="viewType === 'project' ? '选择项目' : '选择工作包类别'"
          style="width: 220px; margin-left: 12px" @change="fetchSituation">
          <el-option v-for="opt in situationOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
        </el-select>
        <!-- 月份（可选：空 = 累计全部月份） -->
        <el-date-picker v-if="activeTab === 'situation'" v-model="situationMonth" type="month" value-format="YYYY-MM" clearable
          placeholder="全部月份（累计）" style="width: 160px; margin-left: 12px" @change="fetchSituation" />
        <!-- 项目汇总：查看方式（项目 / 工作包） -->
        <el-select v-if="activeTab === 'summary'" v-model="summaryViewType" size="default"
          style="width: 150px" @change="fetchProjectSummary">
          <el-option label="按项目查看" value="project" />
          <el-option label="按工作包查看" value="work_package" />
        </el-select>
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
              </div>
            </div>

            <!-- 个人积分详情：嵌套展开表格 -->
            <el-table
              :data="groupedMyDetails"
              v-loading="loading"
              border
              style="width: 100%"
              height="calc(100vh - 380px)"
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
              <el-table-column prop="project_name" label="所属项目名称" min-width="150" show-overflow-tooltip />
              <el-table-column prop="project_code" label="所属项目编号" min-width="150" show-overflow-tooltip />
              <el-table-column prop="work_package_code" label="所属工作包" width="180" align="center" />
              <el-table-column prop="work_package_category" label="所属工作包类型" width="180" align="center" />
            </el-table>
          </div>
        </el-tab-pane>

        <!-- 页面二：所有人员积分 -->
        <el-tab-pane label="所有人员积分" name="all">
          <div class="tab-content">
            
            <!-- 【表格 1：月度表】当查询维度为“月份”时显示 -->
            <el-table
              v-if="queryMode === 'month'"
              :data="peopleList"
              v-loading="loading"
              stripe
              border
              style="width: 100%"
              height="calc(100vh - 330px)"
              empty-text="当前月份暂无积分数据"
              :header-cell-style="{ background: '#f8fafc', color: '#334155' }"
            >
              <el-table-column prop="username" label="人员" width="100" align="center" fixed="left" />
              <!-- 工作项基础分 -->
              <el-table-column label="工作项" align="center">
                <el-table-column prop="month_score" label="基础得分" min-width="80" align="center" />
                <el-table-column prop="calculate_score" label="计算得分" min-width="80" align="center" />
                <el-table-column prop="deducted_score" label="进度扣分" min-width="80" align="center" />
              </el-table-column>
              <!-- 额外加分项 -->
              <el-table-column label="技术提升" align="center">
                <el-table-column prop="patent_score" label="专利" min-width="80" align="center">
                  <template #default="{ row }">
                    <el-input-number v-if="row.isEditing" v-model="row.patent_score" :step="0.5" size="small" style="width: 80px" controls-position="right" />
                    <span v-else>{{ row.patent_score || 0 }}</span>
                  </template>
                </el-table-column>
                <el-table-column prop="knowledge_score" label="知识库" min-width="80" align="center" >
                  <template #default="{ row }">
                    <el-input-number v-if="row.isEditing" v-model="row.knowledge_score" :step="0.5" size="small" style="width: 80px" controls-position="right" />
                    <span v-else>{{ row.knowledge_score || 0 }}</span>
                  </template>
                </el-table-column>
                <el-table-column prop="train_score" label="培训" min-width="80" align="center">
                  <template #default="{ row }">
                    <el-input-number v-if="row.isEditing" v-model="row.train_score" :step="0.5" size="small" style="width: 80px" controls-position="right" />
                    <span v-else>{{ row.train_score || 0 }}</span>
                  </template>
                </el-table-column>
              </el-table-column>

              <el-table-column label="日常管理" align="center">
                <el-table-column prop="deduct_score" label="扣分" min-width="80" align="center">
                  <template #default="{ row }">
                    <el-input-number v-if="row.isEditing" v-model="row.deduct_score" :step="0.5" size="small" style="width: 80px" controls-position="right" />
                    <span v-else>{{ row.deduct_score || 0 }}</span>
                  </template>
                </el-table-column>
                <el-table-column prop="quality_event_score" label="质量事件" min-width="80" align="center">
                  <template #default="{ row }">
                    <el-input-number v-if="row.isEditing" v-model="row.quality_event_score" :step="0.5" size="small" style="width: 80px" controls-position="right" />
                    <span v-else>{{ row.quality_event_score || 0 }}</span>
                  </template>
                </el-table-column>
                <el-table-column prop="carrier_inspection_score" label="载体检查" min-width="80" align="center">
                  <template #default="{ row }">
                    <el-input-number v-if="row.isEditing" v-model="row.carrier_inspection_score" :step="0.5" size="small" style="width: 80px" controls-position="right" />
                    <span v-else>{{ row.carrier_inspection_score || 0 }}</span>
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
                    <el-button type="primary" link size="small" @click="startEdit(row)">编辑</el-button>
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
              <el-table-column prop="total_score" label="得分" min-width="100" align="center">
                <template #default="{ row }">
                  <span class="score-text">{{ row.total_score || 0 }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="final_calculated" label="计算得分" min-width="100" align="center" />
              
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
            <!-- 汇总卡片 -->
            <div class="summary-cards">
              <div class="summary-card">
                <div class="summary-card-label">{{ summaryViewType === 'project' ? '项目数量' : '工作包数量' }}</div>
                <div class="summary-card-value">{{ summaryTotals.count || 0 }}</div>
              </div>
              <div class="summary-card">
                <div class="summary-card-label">工作包 / 工作项</div>
                <div class="summary-card-value">{{ summaryTotals.work_package_count || 0 }} / {{ summaryTotals.work_item_count || 0 }}</div>
              </div>
              <div class="summary-card">
                <div class="summary-card-label">总分值</div>
                <div class="summary-card-value">{{ summaryTotals.total_score ?? 0 }}</div>
              </div>
              <div class="summary-card">
                <div class="summary-card-label">已填分值</div>
                <div class="summary-card-value summary-filled">{{ summaryTotals.filled_score ?? 0 }}</div>
              </div>
              <div class="summary-card">
                <div class="summary-card-label">未填分值</div>
                <div class="summary-card-value summary-unfilled">{{ summaryTotals.unfilled_score ?? 0 }}</div>
              </div>
            </div>
            <el-table
              :data="summaryItems"
              v-loading="loading"
              border
              style="width: 100%"
              height="calc(100vh - 400px)"
              :empty-text="summaryViewType === 'project' ? '暂无项目数据' : '暂无工作包数据'"
              :header-cell-style="{ background: '#f8fafc', color: '#334155' }"
              show-summary
              :summary-method="summaryTableSummary">
              <el-table-column :label="summaryViewType === 'project' ? '项目名称' : '工作包名称'" min-width="200" fixed="left" show-overflow-tooltip>
                <template #default="{ row }"><span class="employee-text">{{ row.name }}</span></template>
              </el-table-column>
              <el-table-column prop="code" label="编号" min-width="150" align="center" show-overflow-tooltip />
              <el-table-column v-if="summaryViewType === 'work_package'" prop="parent_name" label="所属项目" min-width="150" show-overflow-tooltip />
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
          </div>
        </el-tab-pane>

      </el-tabs>
    </el-card>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { getPublicScoreBoardApi, updateMonthlyExtraScoreApi, getCompletedSituationApi, getAllProjectsApi, getWorkCategoriesApi, getProjectSummaryApi } from '../api'
import { useUserStore } from '../stores/user'

const userStore = useUserStore()
const currentUser = computed(() => userStore.userInfo)

const activeTab = ref('personal')
const peopleList = ref([])
const loading = ref(false)

// 查询维度与具体选择：默认按月份看当前月
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
})

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
  return peopleList.value.find(p => String(p.user_id) === String(currentUser.value.id)) || null
})

// 计算个人的分组详情数据（外层项目/工作包，内层具体工作项+扣分）
const groupedMyDetails = computed(() => {
  if (!currentPeriodPersonalData.value || !currentPeriodPersonalData.value.details) return []
  const map = {}
  const itemRows = {}   // work_item_id -> 行对象（跨月合并用）

  currentPeriodPersonalData.value.details.forEach(item => {
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

    // 按工作项合并：同一工作项跨月只显示一行；本月得分/计算得分累加；扣除分取该工作项判定（超期1/未超期0）
    const iid = item.work_item_id
    if (!itemRows[iid]) {
      const row = {
        work_item_name: item.work_item_name || item.work_package_name || '未命名工作项',
        work_item_standard: item.work_item_standard || '-',
        score: 0,
        quality_score: item.quality_score || 0,
        difficulty: item.work_item_difficulty || null,
        importance: item.work_item_importance || null,
        innovation: item.work_item_innovation || null,
        calculate_score: 0,
        deducted_score: item.deducted_score || 0
      }
      itemRows[iid] = row
      map[key].items.push(row)
    }
    const row = itemRows[iid]
    row.score += item.score || 0
    row.calculate_score += item.calculate_score || 0
    // 质量分：同一工作项不同月可能不同，保留该工作项最近一条的值
    row.quality_score = item.quality_score ?? row.quality_score
    row.difficulty = item.work_item_difficulty
    row.importance = item.work_item_importance
    row.innovation = item.work_item_innovation
  })

  return Object.values(map)
})

// 切换查询维度时按当前标签页分发（季度/年份/月份选择器绑定 onPeriodChange）
const onQueryChange = () => {
  onPeriodChange()
}

// 周期（年/季/月）变化时：项目汇总页查汇总，其余页查积分
const onPeriodChange = () => {
  if (activeTab.value === 'summary') {
    fetchProjectSummary()
    return
  }
  fetchPublicScoreBoard()
}

// 按所选维度与具体年月/季/年拉取积分数据
const fetchPublicScoreBoard = async () => {
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
    const res = await getPublicScoreBoardApi(queryMode.value, year, month, quarter)
    if (res?.data?.code === 200) {
      peopleList.value = res.data.data.people || []
    }
  } catch (err) {
    console.error('获取公开积分数据报错:', err)
    ElMessage.error('获取公开积分数据失败')
  } finally {
    loading.value = false
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
  // 开启该行的编辑模式
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

// ====================== 项目汇总（项目 / 工作包 → 分值进度） ======================
const summaryItems = ref([])                 // 当前视图的行数据（项目 或 工作包）
const summaryTotals = ref({})
const summaryViewType = ref('project')       // project | work_package
const canViewSummary = computed(() => {
  const r = String(currentUser.value?.role || '').toUpperCase()
  return r === 'LEADER' || r === 'ADMIN'
})
// 查询维度选择器：个人积分 / 所有人员积分 / 项目汇总 三个页签共用
const showPeriodFilter = computed(() => ['personal', 'all', 'summary'].includes(activeTab.value))

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

// 项目汇总表格底部合计（个数 / 总分值 / 已填 / 未填）
const summaryTableSummary = ({ columns, data }) => {
  const sums = []
  columns.forEach((col, idx) => {
    if (idx === 0) { sums[idx] = '合计'; return }
    const key = col.property
    if (['child_count', 'work_item_count', 'total_score', 'filled_score', 'unfilled_score'].includes(key)) {
      sums[idx] = parseFloat(data.reduce((s, r) => s + (Number(r[key]) || 0), 0).toFixed(2))
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
const canViewSituation = computed(() => {
  const r = String(currentUser.value?.role || '').toUpperCase()
  return r === 'LEADER' || r === 'ADMIN'
})

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

// 切标签页时按需加载：项目汇总 / 完成情况
watch(activeTab, (tab) => {
  if (tab === 'summary' && canViewSummary.value) {
    fetchProjectSummary()
  }
  if (tab === 'situation' && canViewSituation.value && !situationOptions.value.length) {
    loadSituationOptions()
  }
})

onMounted(() => {
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

.period-label {
  color: #475569;
  font-weight: 600;
  margin-left: 8px;
}

/* 项目汇总：顶部统计卡片 */
.summary-cards {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 16px;
}

.summary-card {
  flex: 1 1 150px;
  background-color: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  padding: 12px 16px;
}

.summary-card-label {
  font-size: 13px;
  color: #64748b;
  margin-bottom: 6px;
}

.summary-card-value {
  font-size: 20px;
  font-weight: 600;
  color: #1e293b;
}

.summary-filled { color: #67c23a; }

.summary-unfilled { color: #f56c6c; }

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
</style>