<template>
  <div class="work-item-table">
    <div v-if="canManage" class="table-actions">
      <el-button type="primary" plain :disabled="!stagedCount" :loading="saving" size="small" @click="handleOpenBatchSubmit">
        提交<el-badge v-if="stagedCount" :value="stagedCount" class="batch-badge" />
      </el-button>
      <el-button type="success" plain size="small" @click="handleAddWorkItem">新增工作项</el-button>
    </div>

    <el-table
      :data="workItems"
      v-loading="loading"
      border
      size="small"
      style="width: 100%"
      max-height="400"
      empty-text="该工作包下暂无工作项，点击「新增工作项」可添加"
      :row-class-name="rowClassName"
      :header-cell-style="{ background: '#f1f5f9', color: '#475569' }"
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
          <el-option v-for="o in levelDefs.difficulty" :key="o" :label="o" :value="o" />
          </el-select>
          <el-tag v-else size="small">{{ row.difficulty || '-' }}</el-tag>
      </template>
      </el-table-column>

      <el-table-column prop="importance" label="重要度" width="90" align="center">
        <template #default="{ row }">
          <el-select v-if="row.isEdit" v-model="row.importance" size="small">
            <el-option v-for="o in levelDefs.importance" :key="o" :label="o" :value="o" />
          </el-select>
          <el-tag v-else size="small">{{ row.importance || '-' }}</el-tag>
        </template>
      </el-table-column>

      <el-table-column prop="innovation" label="创新度" width="90" align="center">
        <template #default="{ row }">
          <el-select v-if="row.isEdit" v-model="row.innovation" size="small">
            <el-option v-for="o in levelDefs.innovation" :key="o" :label="o" :value="o" />
          </el-select>
          <span v-else>{{ row.innovation || '-' }}</span>
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
          <el-tag v-else-if="row.deadline" type="danger" effect="plain">{{ row.deadline }}</el-tag>
          <span v-else>-</span>
        </template>
      </el-table-column>

      <el-table-column prop="score" label="基础总分值" width="90" align="center">
        <template #default="{ row }">
          <el-input-number v-if="row.isEdit" v-model="row.score" :min="0" :step="0.5" size="small" style="width: 100%" controls-position="right" />
          <span v-else class="score-text">{{ row.score }}</span>
        </template>
      </el-table-column>

      <el-table-column label="剩余分值" width="90" align="center">
        <template #default="{ row }">
          <span class="score-text">{{ row.remaining_score }}</span>
        </template>
      </el-table-column>

      <el-table-column label="进度" width="130" align="center">
        <template #default="{ row }">
          <el-progress :percentage="row.progress || 0" :stroke-width="8" />
        </template>
      </el-table-column>

      <el-table-column prop="month_score" label="本月分值" width="90" align="center" fixed="right">
        <template #default="{ row }">
          <template v-if="row.isEditMonth">
            <el-input-number v-model="row.month_score" :min="0" :step="0.5" size="small" style="width: 100%" controls-position="right" />
            <div class="score-actions">
              <el-button type="success" link size="small" :loading="savingMonth" @click="saveMonthScore(row)">保存</el-button>
              <el-button type="info" link size="small" @click="row.isEditMonth = false">取消</el-button>
            </div>
          </template>
          <template v-else>
            <span class="score-text">{{ row.month_score ?? 0 }}</span>
            <el-button v-if="canManage && row.id " type="primary" link size="small" @click="row.isEditMonth = true">填写</el-button>
            <el-tag v-if="row.complete_status" size="small" type="success" effect="plain">已完成</el-tag>
          </template>
        </template>
      </el-table-column>

      <el-table-column prop="quality_score" label="质量分" width="90" align="center"  fixed="right">
        <template #default="{ row }">
          <template v-if="row.isEditQuality">
            <el-input-number v-model="row.quality_score" :min="-1000" :step="0.5" size="small" style="width: 100%" controls-position="right" />
            <div class="score-actions">
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

      <el-table-column v-if="canManage" label="操作" width="180" align="center" fixed="right">
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
            <el-button v-if="!row.complete_status && row.id" type="success" link size="small" :loading="confirming" @click="confirmComplete(row)">确认完成</el-button>
            <el-button v-if="row.complete_status" type="warning" link size="small" @click="cancelComplete(row)">取消完成</el-button>
            <el-button type="primary" link size="small" @click="row.isEdit = true">编辑</el-button>
            <el-popconfirm v-if="!row.complete_status" title="确定删除该工作项？" confirm-button-type="danger" @confirm="removeItem(row)">
              <template #reference>
                <el-button type="danger" link size="small">删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </template>
      </el-table-column>
    </el-table>

    <!-- 提交审核弹窗：一次提交所有已保存的修改 -->
    <el-dialog v-model="submitDialogVisible" title="提交审核" width="520px" draggable append-to-body>
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
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import {
  createSplitRequestApi,
  deleteWorkItemApi,
  getWorkItemsApi,
  saveMonthScoreApi,
  saveQualityScoreApi,
  confirmCompletionApi
} from '../api'
import { useUserStore } from '../stores/user'
import { useLevelDefs } from '../comosables/useLevelDefs'

const props = defineProps({
  workPackageId: { type: String, required: true }
})
const emit = defineEmits(['changed'])

const userStore = useUserStore()

const workPackage = ref(null)
const workItems = ref([])
const loading = ref(false)
const saving = ref(false)
const savingMonth = ref(false)
const savingQuality = ref(false)
const confirming = ref(false)
const levelDefs = useLevelDefs()

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

// 管理权限：管理员 / 领导 / 该工作包负责人 可以新增、编辑、删除工作项
const canManage = computed(() => {
  if (!userStore.isLoggedIn) return false
  if (userStore.isAdmin || userStore.isLEADER || userStore.isDEPARTMENT) return true
  return workPackage.value && String(workPackage.value.owner_id) === String(userStore.userInfo?.id)
})

// 只有领导可以编辑质量分
const canManageQuality = computed(() => userStore.isLEADER)

// 已完成工作项整行灰显
const rowClassName = ({ row }) => (row.complete_status ? 'completed-row' : '')

const notifyChanged = () => emit('changed')

const fetchData = async () => {
  loading.value = true
  try {
    const res = await getWorkItemsApi(props.workPackageId)
    if (res.data?.code === 200) {
      workPackage.value = res.data.data.work_package
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

// 工作项 ID 变化（展开不同工作包）时重新加载
watch(() => props.workPackageId, () => fetchData())

const handleAddWorkItem = () => {
  workItems.value.unshift({
    id: null,
    name: '',
    standard: '',
    difficulty: '',
    importance: '',
    innovation: '',
    deadline: '',
    score: 0,
    work_package_id: props.workPackageId,
    isEdit: true,
    isNew: true,
    isPending: false,
    isStaged: false,
    isEditMonth: false,
    isEditQuality: false
  })
}

// 行内「保存」：校验并暂存到本地（不提交审核，等待「提交」一起提交）
const handleSaveLocal = (row) => {
  if (!row.name || !row.name.trim()) return ElMessage.warning('请输入工作项名称')
  row.isEdit = false
  row.isStaged = true
  row._original = {
    name: row.name,
    standard: row.standard,
    difficulty: row.difficulty,
    importance: row.importance,
    innovation: row.innovation,
    deadline: row.deadline,
    score: row.score
  }
  ElMessage.success('已保存，点击「提交」可一起提交审核')
}

// 头部「提交」：收集所有已暂存的修改
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

// 确认提交：提交审核，记录存入 WorkPackageSplitRequest 表
const confirmBatchSubmit = async () => {
  const rows = batchSubmitItems.value
  if (!rows.length) return
  const reason = (submitReason.value || '').trim()
  if (!reason) return ElMessage.warning('请填写具体修改内容')

  saving.value = true
  try {
    const res = await createSplitRequestApi({
      applicant_id: userStore.userInfo?.id,
      work_package_id: props.workPackageId,
      reason: '批量提交工作项：' + reason,
      split_items: rows.map(row => ({
        work_item_id: row.isNew ? null : row.id,
        name: row.name.trim(),
        standard: row.standard,
        difficulty: row.difficulty,
        importance: row.importance,
        innovation: row.innovation,
        deadline: row.deadline || '',
        score: row.score
      }))
    })
    if (res.data?.code === 200) {
      ElMessage.success(`已提交 ${rows.length} 个工作项审核，等待领导审批`)
      rows.forEach(row => {
        row.isPending = true
        row.isStaged = false
      })
      batchSubmitItems.value = []
      submitDialogVisible.value = false
      notifyChanged()
    }
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '提交审核失败')
  } finally {
    saving.value = false
  }
}

// 保存本月分值（员工直接填写、直接生效）
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
      await fetchData()
      notifyChanged()
    }
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '保存本月分值失败')
  } finally {
    savingMonth.value = false
  }
}

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
      const saved = Number(res.data?.data?.quality_score)
      row.quality_score = Number.isFinite(saved) ? saved : row.quality_score
      await fetchData()
      notifyChanged()
    }
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '保存质量分失败')
  } finally {
    savingQuality.value = false
  }
}

const cancelEdit = (row, index) => {
  if (row.isNew) {
    workItems.value.splice(index, 1)
  } else {
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
      notifyChanged()
    }
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '删除失败')
  }
}

// 确认完成（负责人手动标记，后端会记录完成时间）
const confirmComplete = async (row) => {
  if (!row.id) return
  confirming.value = true
  try {
    const res = await confirmCompletionApi({
      target_type: 'work_item',
      target_id: String(row.id),
      user_id: userStore.userInfo?.id,
      confirmed: true
    })
    if (res.data?.code === 200) {
      ElMessage.success('已确认完成')
      await fetchData()
      notifyChanged()
    }
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '确认完成失败')
  } finally {
    confirming.value = false
  }
}

// 取消完成（取消时后端清空完成时间）
const cancelComplete = async (row) => {
  try {
    const res = await confirmCompletionApi({
      target_type: 'work_item',
      target_id: row.id,
      user_id: userStore.userInfo?.id,
      confirmed: false
    })
    if (res.data?.code === 200) {
      ElMessage.success('已取消完成')
      await fetchData()
      notifyChanged()
    }
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '取消完成失败')
  }
}

onMounted(fetchData)
</script>

<style scoped>
.work-item-table {
  width: 100%;
}

.table-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
  margin-bottom: 8px;
}

.batch-badge {
  margin-left: 6px;
  vertical-align: middle;
}

.staged-tag {
  margin-right: 4px;
}

.score-actions {
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
</style>
