<!-- xiangmu/frontend/src/views/AdminPanel.vue -->
<template>
  <div class="admin-panel-page">
    <el-card shadow="never" class="box-card">
      <template #header>
        <div class="card-header">
          <span class="title">后台管理</span>
          <el-button
            v-if="activeTab === 'score'"
            type="primary"
            size="small"
            :loading="saving"
            @click="handleSaveScoreRules"
          >保存系数配置</el-button>
          <el-button
            v-if="activeTab === 'users'"
            type="primary"
            size="small"
            @click="pmRef?.fetchAllData()"
            icon="Refresh"
          >刷新数据</el-button>
        </div>
      </template>

      <el-tabs v-model="activeTab">
        <!-- 人员管理 -->
        <el-tab-pane label="人员管理" name="users">
          <PersonnelManagement ref="pmRef" />
        </el-tab-pane>

        <el-tab-pane label="信息管理" name="information" lazy>
          <InformationManagement @changed="pmRef?.fetchAllData()" />
        </el-tab-pane>

        <el-tab-pane label="计算得分系数" name="score">
          <div class="score-rule-wrapper">
            <el-alert
              type="info"
              :closable="false"
              show-icon
              class="rule-tip"
              title="计算得分 = 本月分值 ×（ 难度系数 + 创新度系数 + 重要度系数）+ 质量分（档位查不到按 0）"
            />

            <!-- 顶部筛选操作区 -->
            <div class="filter-container" style="display: flex; gap: 24px; margin: 16px 0; align-items: center;">
              
              <!-- 1. 变量下拉框 -->
              <div class="filter-item">
                <span style="margin-right: 12px; font-weight: 600; color: #334155;">请选择变量:</span>
                <el-select 
                  v-model="selectedVariable" 
                  @change="handleVariableChange"
                  placeholder="请选择变量" 
                  style="width: 200px;"
                >
                  <el-option
                    v-for="item in variableOptions"
                    :key="item.value"
                    :label="item.label"
                    :value="item.value"
                  />
                </el-select>
              </div>

              <!-- 2. 职级下拉框 (重点：利用 v-if 仅在需要时显示) -->
              <div class="filter-item" v-if="showJobGradeSelector">
                <span style="margin-right: 12px; font-weight: 600; color: #334155;">请选择职级:</span>
                <el-select 
                  v-model="selectedJobgrade" 
                  placeholder="请选择职级" 
                  style="width: 200px;"
                >
                  <el-option
                    v-for="item in jobgradeOptions"
                    :key="item.value"
                    :label="item.label"
                    :value="item.value"
                  />
                </el-select>
              </div>

            </div>

            <!-- 表格：根据变量和职级双重过滤 -->
            <el-table
              :data="currentTableData"
              border
              stripe
              v-loading="loading"
              style="width: 100%"
              height="calc(100vh - 400px)"
              empty-text="请在上方完成选择，或暂无匹配的档位数据"
              :header-cell-style="{ background: '#f8fafc', color: '#334155', fontWeight: '600' }"
            >
              <el-table-column prop="level" label="档位" min-width="120" align="center">
                <template #default="{ row }">
                  <el-tag size="small" type="info" effect="plain">{{ row.level }}</el-tag>
                </template>
              </el-table-column>

              <el-table-column label="系数" width="250" align="center">
                <template #default="{ row }">
                  <el-input-number
                    v-model="row.factor"
                    :min="0"
                    :max="5"
                    :precision="3"
                    :step="0.01"
                    size="small"
                    style="width: 130px"
                    controls-position="right"
                  />
                </template>
              </el-table-column>
            </el-table>

            
          </div>
        </el-tab-pane>

        <el-tab-pane label="档位管理" name="level">
          <div class="level-def-header">
            <el-button type="primary" :loading="savingDefs" @click="handleSaveLevelDefs">
              保存档位设置
            </el-button>
            <el-alert
              title="保存后会按新档位重建系数矩阵（已有系数保留，新增档位默认 0）"
              type="info"
              show-icon
              :closable="false"
              class="level-tip-alert"
            />
          </div>
          <div class="level-def-grid">
            <el-card 
              v-for="g in levelDefGroups" 
              :key="g.key" 
              class="level-def-card" 
              shadow="hover"
            >
              <template #header>
                <div class="level-def-title">{{ g.label }}</div>
              </template>
              <div class="level-def-tags-vertical">
                <el-tag
                  v-for="(name, i) in levelDefs[g.key]"
                  :key="name"
                  closable
                  size="large"
                  effect="light"
                  class="vertical-tag"
                  :disable-transitions="true"
                  @close="removeLevelDef(g.key, i)"
                >
                  {{ name }}
                </el-tag>
              </div>
              <div class="level-def-add">
                <el-input
                  v-model="levelDefInputs[g.key]"
                  placeholder="输入新档位名称"
                  @keyup.enter="addLevelDef(g.key)"
                >
                  <template #append>
                    <el-button @click="addLevelDef(g.key)">添加</el-button>
                  </template>
                </el-input>
              </div>
            </el-card>
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { getComputedScoreDimensionsApi, putComputedScoreDimensionsApi, getLevelDefsApi, putLevelDefsApi } from '../../api'
import { useUserStore } from '../../stores/user'
import PersonnelManagement from './PersonnelManagement.vue'
import InformationManagement from './InformationManagement.vue'

const userStore = useUserStore()
const activeTab = ref('users')
const loading = ref(false)
const saving = ref(false)
const dimensions = ref([])
const selectedVariable = ref('')
const selectedJobgrade = ref('')

const pmRef = ref(null)

// 把「维度 → 档位列表」拍平为表格行，方便直接编辑每个档位的系数
const flatRows = computed(() => {
  const rows = []
  dimensions.value.forEach(d => {
    ;(d.levels || []).forEach(lv => {
      // 直接引用原始 lv 对象（不浅拷贝），让表格 v-model 编辑能回写到 dimensions 数据
      rows.push(Object.assign(lv, { variable: d.variable, variable_name: d.name || d.variable }))
    })
  })
  return rows
})

const variableOptions = computed(() => {
  if (!flatRows.value) return []
  const uniqueNames = [...new Set(flatRows.value.map(row => row.variable_name))]
  return uniqueNames.map(name => ({ label: name, value: name }))
})

const showJobGradeSelector = computed(() => {
  // 只有当选中 "难度" 或 "重要度" 时，才返回 true
  // 注意：如果你的字典里叫 "difficulty" 或 "难度系数"，请自行修改这里的字符串匹配
  return ['难度', '重要度'].includes(selectedVariable.value)
})

const jobgradeOptions = computed(() => {
  if (!showJobGradeSelector.value || !flatRows.value) return []
  
  // 从当前选中的变量数据中，提取出所有不重复的职级
  const rowsForVar = flatRows.value.filter(row => row.variable_name === selectedVariable.value)
  // 过滤掉空的职级
  const uniqueRanks = [...new Set(rowsForVar.map(row => row.job_grade).filter(Boolean))]
  return uniqueRanks.map(rank => ({ label: rank, value: rank }))
})

const handleVariableChange = () => {
  if (showJobGradeSelector.value) {
    // 如果切到了难度/重要度，为了方便用户，默认帮他选中第一个职级
    if (jobgradeOptions.value.length > 0) {
      selectedJobgrade.value = jobgradeOptions.value[0].value
    } else {
      selectedJobgrade.value = ''
    }
  } else {
    // 如果切到了创新度等不需要职级的变量，清空职级选中状态
    selectedJobgrade.value = ''
  }
}

const currentTableData = computed(() => {
  // 还没选变量时，啥也不显示
  if (!selectedVariable.value) return []

  if (showJobGradeSelector.value) {
    // 【情况A】如果是难度/重要度：必须“变量”和“职级”同时对上号才显示
    if (!selectedJobgrade.value) return [] 
    return flatRows.value.filter(row => 
      row.variable_name === selectedVariable.value && 
      row.job_grade === selectedJobgrade.value
    )
  } else {
    // 【情况B】如果是普通变量：只要“变量”对上号就显示
    return flatRows.value.filter(row => row.variable_name === selectedVariable.value)
  }
})

const fetchRules = async () => {
  loading.value = true
  try {
    const res = await getComputedScoreDimensionsApi()
    if (res.data?.code === 200) dimensions.value = res.data.data || []
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '获取评分规则失败')
  } finally {
    loading.value = false
  }
}

const handleSaveScoreRules = async () => {
  saving.value = true
  try {
    const items = dimensions.value.map(d => ({
      variable: d.variable,
      levels: (d.levels || []).map(lv => ({ level: lv.level, factor: lv.factor, job_grade: lv.job_grade }))
    }))
    const res = await putComputedScoreDimensionsApi({
      user_id: userStore.userInfo?.id,
      items
    })
    if (res.data?.code === 200) {
      ElMessage.success('系数配置已保存')
      await fetchRules()
    }
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

// ---------------------------------------------------------------- 档位管理
const levelDefGroups = [
  { key: 'job_grade', label: '职级' },
  { key: 'difficulty', label: '难度档位' },
  { key: 'importance', label: '重要度档位' },
  { key: 'innovation', label: '创新度档位' }
]
const levelDefs = ref({ job_grade: [], difficulty: [], importance: [], innovation: [] })
const levelDefInputs = ref({ job_grade: '', difficulty: '', importance: '', innovation: '' })
const savingDefs = ref(false)

const fetchLevelDefs = async () => {
  try {
    const res = await getLevelDefsApi()
    if (res.data?.code === 200) levelDefs.value = res.data.data || levelDefs.value
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '获取档位定义失败')
  }
}

const addLevelDef = (key) => {
  const val = (levelDefInputs.value[key] || '').trim()
  if (!val) return
  if (levelDefs.value[key].includes(val)) return ElMessage.warning('该档位已存在')
  levelDefs.value[key].push(val)
  levelDefInputs.value[key] = ''
}

const removeLevelDef = (key, index) => {
  levelDefs.value[key].splice(index, 1)
}

const handleSaveLevelDefs = async () => {
  savingDefs.value = true
  try {
    const res = await putLevelDefsApi({
      user_id: userStore.userInfo?.id,
      job_grade: levelDefs.value.job_grade,
      difficulty: levelDefs.value.difficulty,
      importance: levelDefs.value.importance,
      innovation: levelDefs.value.innovation
    })
    if (res.data?.code === 200) {
      ElMessage.success('档位已保存并重建系数矩阵')
      await fetchLevelDefs()
      await fetchRules()   // 刷新系数配置表格（矩阵已重建）
    }
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '保存档位失败')
  } finally {
    savingDefs.value = false
  }
}

onMounted(() => {
  fetchRules()
  fetchLevelDefs()
})
</script>

<style scoped>
.admin-panel-page {
  padding: 20px;
  animation: fadeIn 0.4s ease;
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  box-sizing: border-box;
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

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

/* 表格固定高度内部滚动，不受全局 flex:1 拉伸影响 */
:deep(.el-table) { flex: none !important; }

.title {
  font-size: 18px;
  font-weight: 600;
  color: #0f172a;
}

.score-rule-wrapper {
  padding: 8px 4px;
}

.rule-tip {
  margin-bottom: 8px;
}

/* 档位管理 */
.level-def-card {
  margin-top: 8px;
  border-radius: 8px;
}
.level-def-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 16px;
  margin-bottom: 16px;
}
.level-def-block {
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 12px;
}
.level-def-title {
  font-weight: 600;
  color: #334155;
  margin-bottom: 8px;
}
.level-def-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  min-height: 32px;
  margin-bottom: 8px;
}
.level-def-add {
  display: flex;
  align-items: center;
  gap: 8px;
}
.level-def-save {
  display: flex;
  align-items: center;
  gap: 12px;
}
.level-def-tip {
  font-size: 12px;
  color: #94a3b8;
}
/* --- 档位管理页面美化 --- */

/* 顶部操作区 */
.level-def-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid #ebeef5;
}

/* 提示条宽度自适应填满剩余空间 */
.level-tip-alert {
  margin: 0;
  flex: 1;
}

/* 修改后的网格布局：强制在一行显示4个，均分宽度 */
.level-def-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr); /* 核心修改：数字 4 代表固定 4 列，1fr 代表宽度平分 */
  gap: 20px;
}

.level-def-card {
  border-radius: 8px;
}

.level-def-title {
  font-weight: 600;
  font-size: 15px;
  color: #303133;
}

/* 【核心实现】：档位竖向排列 */
.level-def-tags-vertical {
  display: flex;
  flex-direction: column; /* 控制内部元素竖向堆叠 */
  gap: 10px;              /* 每个档位上下之间的间距 */
  margin-bottom: 20px;
  min-height: 120px;      /* 没数据时也能撑起一定高度，保持排版整齐 */
}

/* 将 Tag 拉宽到 100%，并将关闭按钮推到最右侧 */
.vertical-tag {
  width: 100%;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 14px;
  padding: 0 12px;
}

/* 输入框区域撑满 */
.level-def-add {
  width: 100%;
}
</style>
