<!-- xiangmu/frontend/src/views/WorkItemList.vue -->
<template>
  <div class="work-item-page">
    <el-card class="box-card" shadow="never">
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <el-button link @click="goBack">← 返回</el-button>
            <span class="title">工作项管理</span>
          </div>
          <div v-if="canManage" class="header-actions">
            <el-button type="primary" plain :disabled="!stagedCount" :loading="saving" @click="handleOpenBatchSubmit">
              提交<el-badge v-if="stagedCount" :value="stagedCount" class="batch-badge" />
            </el-button>
            <el-button type="success" plain @click="handleAddWorkItem">
              新增工作项
            </el-button>
          </div>
        </div>
      </template>

      <!-- 工作包信息概览 (按要求精简为3项) -->
      <div class="wp-info" v-if="workPackage">
        <el-descriptions :column="4" border size="small">
          <el-descriptions-item label="工作包编号">{{ workPackage.id }}</el-descriptions-item>
          <el-descriptions-item label="所属项目编号">{{ workPackage.project_code }}</el-descriptions-item>
          <el-descriptions-item label="所属项目名称">{{ workPackage.project_name }}</el-descriptions-item>
          <el-descriptions-item label="工作包负责人">
            {{ workPackage.owner_name || workPackage.owner_id || '未指定' }}
          </el-descriptions-item>
        </el-descriptions>
      </div>

      <!-- 工作项列表 -->
      <el-table
        :data="workItems"
        v-loading="loading"
        border
        stripe
        :row-class-name="rowClassName"
        style="width: 100%"
        empty-text="该工作包下暂无工作项，点击右上角可新增"
      >
        <el-table-column prop="name" label="工作项名称" min-width="150">
          <template #default="{ row }">
            <el-input v-if="row.isEdit" v-model="row.name" size="small" placeholder="请输入名称" />
            <span v-else>{{ row.name }}</span>
          </template>
        </el-table-column>

        <el-table-column prop="standard" label="完成标准" min-width="180">
          <template #default="{ row }">
            <el-input v-if="row.isEdit" type="textarea" autosize v-model="row.standard" size="small" placeholder="描述标准" />
            <span v-else>{{ row.standard || '-' }}</span>
          </template>
        </el-table-column>

        <el-table-column prop="difficulty" label="难度" width="90" align="center">
          <template #default="{ row }">
            <el-select v-if="row.isEdit" v-model="row.difficulty" size="small">
              <el-option v-for="o in ['P1', 'P2', 'P3', 'P4']" :key="o" :label="o" :value="o" />
            </el-select>
            <el-tag v-else size="small" >
              {{ row.difficulty || '-' }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="importance" label="重要度" width="90" align="center">
          <template #default="{ row }">
            <el-select v-if="row.isEdit" v-model="row.importance" size="small">
              <el-option v-for="o in ['Ⅰ级', 'Ⅱ级', 'Ⅲ级', 'Ⅳ级']" :key="o" :label="o" :value="o" />
            </el-select>
            <el-tag v-else size="small" >
              {{ row.importance || '-' }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="innovation" label="创新度" width="90" align="center">
          <template #default="{ row }">
            <el-select v-if="row.isEdit" v-model="row.innovation" size="small">
              <el-option v-for="o in ['无','低', '中', '高']" :key="o" :label="o" :value="o" />
            </el-select>
            <span v-else>{{ row.innovation || '-' }}</span>
          </template>
        </el-table-column>

        <el-table-column prop="category" label="类别" width="120" align="center">
          <template #default="{ row }">
            <el-input v-if="row.isEdit" v-model="row.category" size="small" placeholder="如:类别1" />
            <span v-else>{{ row.category || '-' }}</span>
          </template>
        </el-table-column>

        <el-table-column prop="deadline" label="截止时间" width="130" align="center">
          <template #default="{ row }">
            <el-date-picker 
              v-if="row.isEdit" 
              v-model="row.deadline" 
              type="date" 
              value-format="YYYY-MM-DD" 
              size="small" 
              style="width: 100%" 
              placeholder="选择日期" 
            />
            <el-tag v-else-if="row.deadline" type="danger" effect="plain"> {{ row.deadline }}</el-tag>
            <span v-else>-</span>
          </template>
        </el-table-column>

        <el-table-column prop="score" label="分值" width="90" align="center">
          <template #default="{ row }">
            <el-input-number v-if="row.isEdit" v-model="row.score" :min="0" :step="0.5" size="small" style="width: 100%" controls-position="right" />
            <span v-else class="score-text">{{ row.score }}</span>
          </template>
        </el-table-column>

        <el-table-column prop="month_score" label="本月分值" width="90" align="center" fixed="right">
          <template #default="{ row }">
            <template v-if="row.isEditMonth">
              <el-input-number v-model="row.month_score" :min="0" :max="row.score" :step="0.5" size="small" style="width: 100%" controls-position="right" />
              <div class="month-score-actions">
                <el-button type="success" link size="small" :loading="savingMonth" @click="saveMonthScore(row)">保存</el-button>
                <el-button type="info" link size="small" @click="row.isEditMonth = false">取消</el-button>
              </div>
            </template>
            <template v-else>
              <span class="score-text">{{ row.month_score ?? 0 }}</span>
              <el-button v-if="canManage && row.id && !row.complete_status" type="primary" link size="small" @click="row.isEditMonth = true">填写</el-button>
              <el-tag v-if="row.complete_status" size="small" type="success" effect="plain">已完成</el-tag>
            </template>
          </template>
        </el-table-column>

        <el-table-column prop="quality_score" label="质量分" width="90" align="center" fixed="right">
          <template #default="{ row }">
            <template v-if="row.isEditQuality">
              <el-input-number v-model="row.quality_score" :min="-1000" :step="0.5" size="small" style="width: 100%" controls-position="right" />
              <div class="quality-score-actions">
                <el-button type="success" link size="small" :loading="savingQuality" @click="saveQualityScore(row)">保存</el-button>
                <el-button type="info" link size="small" @click="row.isEditQuality = false">取消</el-button>
              </div>
            </template>
            <template v-else>
              <span class="score-text">{{ row.quality_score ?? 0 }}</span>
              <el-button v-if="canManageQuality" type="primary" link size="small" @click="row.isEditQuality = true">填写</el-button>
            </template>
          </template>
        </el-table-column>

        <el-table-column label="进度" width="150" align="center">
          <template #default="{ row }">
            <el-progress :percentage="row.progress || 0" :stroke-width="10" />
          </template>
        </el-table-column>

        <el-table-column v-if="canManage" label="操作" width="100" align="center" fixed="right">
          <template #default="{ row, $index }">
            <template v-if="row.isPending">
              <el-tag size="small" type="warning" effect="plain">待审核</el-tag>
            </template>
            <template v-else-if="row.isEdit">
              <el-button type="success" link size="small" @click="handleSaveLocal(row)">保存</el-button>
              <el-button type="info" link size="small" @click="cancelEdit(row, $index)">取消</el-button>
            </template>
            <template v-else>
              <el-tag v-if="row.isStaged" size="small" type="info" effect="plain" class="staged-tag">已暂存</el-tag>
              <el-tag v-if="row.complete_status" size="small" type="success" effect="plain">已完成</el-tag>
              <el-button v-else type="primary" link size="small" @click="row.isEdit = true">编辑</el-button>
              <el-popconfirm v-if="!row.complete_status" title="确定删除该工作项？" confirm-button-type="danger" @confirm="removeItem(row)">
                <template #reference>
                  <el-button type="danger" link size="small">删除</el-button>
                </template>
              </el-popconfirm>
            </template>
          </template>
        </el-table-column>
      </el-table>

      <!-- 提交审核弹窗：填写本次修改的总体说明，一次提交所有已保存的修改 -->
      <el-dialog v-model="submitDialogVisible" title="提交审核" width="520px" draggable> <!-- 可拖拽 -->
        <el-form label-width="90px">
          <el-form-item label="提交数量">
            <el-tag type="warning" effect="plain">共 {{ batchSubmitItems.length }} 个工作项</el-tag>
          </el-form-item>
          <el-form-item label="工作项清单">
            <div class="submit-item-list">
              <div v-for="(it, idx) in batchSubmitItems" :key="idx" class="submit-item">
                <el-tag :type="it.isNew ? 'success' : 'warning'" size="small" effect="plain">
                  {{ it.isNew ? '新增' : '编辑' }}
                </el-tag>
                <span class="submit-item-name">{{ it.name || '未命名' }}</span>
                <span class="submit-item-score">（{{ it.score ?? 0 }} 分）</span>
              </div>
            </div>
          </el-form-item>
          <el-form-item label="修改说明" required>
            <el-input
              v-model="submitReason"
              type="textarea"
              :rows="4"
              maxlength="500"
              show-word-limit
              placeholder="请填写本次修改的具体内容说明..."
            />
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="submitDialogVisible = false">取消</el-button>
          <el-button type="success" :loading="saving" @click="confirmBatchSubmit">确认提交</el-button>
        </template>
      </el-dialog>
    </el-card>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { createSplitRequestApi, deleteWorkItemApi, getWorkItemsApi, saveMonthScoreApi, saveQualityScoreApi } from '../api'
import { useUserStore } from '../stores/user'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const workPackageId = route.params.id
const workPackage = ref(null)
const workItems = ref([])
const loading = ref(false)
const saving = ref(false)
const savingMonth = ref(false)
const currentMonth = computed(() => {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`
})

// 提交审核弹窗状态
const submitDialogVisible = ref(false)
const batchSubmitItems = ref([])
const submitReason = ref('')

// 已暂存（保存但未提交）的工作项数量
const stagedCount = computed(() => workItems.value.filter(w => w.isStaged).length)

// 管理权限：管理员 / 项目负责人 / 该工作包负责人 可以新增、编辑、删除工作项
const canManage = computed(() => {
  if (!userStore.isLoggedIn) return false
  if (userStore.isAdmin || userStore.isLEADER) return true
  return workPackage.value && String(workPackage.value.owner_id) === String(userStore.userInfo?.id)
})

// 只有领导可以编辑质量分
const canManageQuality = computed(() => userStore.isLEADER)

// 已完成工作项整行灰显
const rowClassName = ({ row }) => (row.complete_status ? 'completed-row' : '')

const fetchData = async () => {
  loading.value = true
  try {
    const res = await getWorkItemsApi(workPackageId)
    if (res.data?.code === 200) {
      workPackage.value = res.data.data.work_package
      // 为每条数据追加编辑状态和历史备份以供取消编辑时回退
      workItems.value = (res.data.data.work_items || []).map(item => ({
        ...item,
        isEdit: false,
        isNew: false,
        isPending: false,
        isStaged: false,
        isEditMonth: false,
        isEditQuality: false,
        _original: JSON.parse(JSON.stringify(item))
      }))
    }
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '获取工作项失败')
  } finally {
    loading.value = false
  }
}

const handleAddWorkItem = () => {
  // 在表格最上方追加一行处于编辑状态的空数据
  workItems.value.unshift({
    id: null,
    name: '',
    standard: '',
    difficulty: '',
    importance: '',
    innovation: '',
    deadline: '',
    score: 0,
    category: '',
    work_package_id: workPackageId,
    isEdit: true,
    isNew: true,
    isPending: false,
    isStaged: false,
    isEditMonth: false,
    isEditQuality: false
  })
}

// 行内「保存」：校验并暂存到本地（不提交审核，等待头部「提交」一起提交）
const handleSaveLocal = (row) => {
  if (!row.name || !row.name.trim()) return ElMessage.warning('请输入工作项名称')
  row.isEdit = false
  row.isStaged = true
  // 以当前保存值为基准，之后若再次编辑取消可还原到这里
  const snapshot = {
    name: row.name,
    standard: row.standard,
    difficulty: row.difficulty,
    importance: row.importance,
    innovation: row.innovation,
    deadline: row.deadline,
    score: row.score,
    category: row.category
  }
  row._original = snapshot
  ElMessage.success('已保存，点击右上角「提交」可一起提交审核')
}

// 头部「提交」：收集所有已暂存的修改，弹出填写总体修改内容的窗口
const handleOpenBatchSubmit = () => {
  const staged = workItems.value.filter(w => w.isStaged)
  if (!staged.length) return ElMessage.warning('暂无可提交的修改，请先保存')
  if (staged.some(w => !w.name || !w.name.trim())) {
    return ElMessage.warning('存在未填写名称的工作项，请先保存')
  }
  batchSubmitItems.value = staged
  submitReason.value = ''
  submitDialogVisible.value = true
}

// 确认提交：把所有已保存的修改一起提交审核，记录存入 WorkPackageSplitRequest 表
const confirmBatchSubmit = async () => {
  const rows = batchSubmitItems.value
  if (!rows.length) return
  const reason = (submitReason.value || '').trim()
  if (!reason) return ElMessage.warning('请填写具体修改内容')

  saving.value = true
  try {
    const res = await createSplitRequestApi({
      applicant_id: userStore.userInfo?.id,
      work_package_id: workPackageId,
      reason: '批量提交工作项：' + reason,
      split_items: rows.map(row => ({
        work_item_id: row.isNew ? null : row.id,
        name: row.name.trim(),
        standard: row.standard,
        difficulty: row.difficulty,
        importance: row.importance,
        innovation: row.innovation,
        deadline: row.deadline || '',
        score: row.score,
        category: row.category
      }))
    })
    if (res.data?.code === 200) {
      ElMessage.success(`已提交 ${rows.length} 个工作项审核，等待领导审批`)
      rows.forEach(row => {
        row.isPending = true  // 本地标记“待审核”，领导通过后刷新页面可见
        row.isStaged = false
      })
      batchSubmitItems.value = []
      submitDialogVisible.value = false
    }
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '提交审核失败')
  } finally {
    saving.value = false
  }
}

// 保存本月分值（员工直接填写、直接生效，不经过审核）
const saveMonthScore = async (row) => {
  if (!row.id) return ElMessage.warning('该工作项尚未保存，无法填写本月分值')
  savingMonth.value = true
  try {
    const res = await saveMonthScoreApi(row.id, {
      user_id: userStore.userInfo?.id,
      month: currentMonth.value,
      score: row.month_score ?? 0
    })
    if (res.data?.code === 200) {
      ElMessage.success('本月分值已保存')
      row.isEditMonth = false
      // 保存后自动刷新，同步进度/计算得分等展示
      await fetchData()
    }
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '保存本月分值失败')
  } finally {
    savingMonth.value = false
  }
}

const savingQuality = ref(false)

const saveQualityScore = async (row) => {
  if (!row.id) return ElMessage.warning('该工作项尚未保存，无法填写质量分')
  savingQuality.value = true
  try {
    const res = await saveQualityScoreApi(row.id, {
      user_id: userStore.userInfo?.id,
      quality_score: row.quality_score ?? 0,
      month: currentMonth.value
    })
    if (res.data?.code === 200) {
      ElMessage.success('质量分已保存')
      row.isEditQuality = false
      // 用后端返回的最新质量分就地更新（避免显示旧快照）
      const saved = Number(res.data?.data?.quality_score)
      row.quality_score = Number.isFinite(saved) ? saved : row.quality_score
      // 保存后自动刷新，同步整页数据（质量分/进度等）
      await fetchData()
    }
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '保存质量分失败')
  } finally {
    savingQuality.value = false
  }
}

const cancelEdit = (row, index) => {
  if (row.isNew) {
    workItems.value.splice(index, 1) // 新增的数据直接移除该行
  } else {
    // 已有的数据撤销编辑，还原到备份的初始状态
    Object.assign(row, row._original)
    row.isEdit = false
  }
}

const removeItem = async (row) => {
  try {
    const res = await deleteWorkItemApi(row.id)
    if (res.data?.code === 200) {
      ElMessage.success('工作项已删除')
      await fetchData()
    }
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '删除失败')
  }
}

const goBack = () => {
  router.push('/project-overview')
}

onMounted(fetchData)
</script>

<style scoped>
.work-item-page {
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
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.04);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.batch-badge {
  margin-left: 6px;
  vertical-align: middle;
}

.staged-tag {
  margin-right: 4px;
}

:deep(.completed-row) {
  background: #f3f4f6 !important;
  color: #9ca3af;
}

:deep(.completed-row td) {
  background: #f3f4f6 !important;
}

:deep(.completed-row .el-button--link) {
  color: #c0c4cc;
  pointer-events: none;
}

.month-score-actions {
  margin-top: 4px;
  display: flex;
  justify-content: center;
  gap: 4px;
}

.submit-item-list {
  width: 100%;
  max-height: 180px;
  overflow-y: auto;
  border: 1px solid #ebeef5;
  border-radius: 6px;
  padding: 8px 10px;
}

.submit-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 3px 0;
  font-size: 13px;
}

.submit-item-name {
  color: #1e293b;
}

.submit-item-score {
  color: #94a3b8;
}

.title {
  font-size: 18px;
  font-weight: 600;
  color: #1e293b;
}

.wp-info {
  margin-bottom: 16px;
}

.score-text {
  color: #67c23a;
  font-weight: 700;
}

.tip-text {
  color: #94a3b8;
  font-size: 13px;
}
</style>