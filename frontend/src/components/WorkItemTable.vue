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

      <el-table-column label="负责人" width="120" align="center">
        <template #default="{ row }">
          <el-select v-if="row.isEdit" v-model="row.owner_id" filterable placeholder="选择负责人" size="small" style="width: 100%">
            <el-option v-for="u in userOptions" :key="u.id" :label="`${u.username}（${u.id}）`" :value="u.id" />
          </el-select>
          <span v-else class="employee-text">{{ row.owner_name || '-' }}</span>
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
            <el-button v-if="canManageRow(row) && row.id " type="primary" link size="small" @click="row.isEditMonth = true">填写</el-button>
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

      <el-table-column v-if="hasManage" label="操作" width="140" align="center" fixed="right">
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
            <el-button v-if="canManageRow(row) && !row.complete_status && row.id" type="success" link size="small" :loading="confirming" @click="confirmComplete(row)">确认完成</el-button>
            <el-button v-if="canManageRow(row) && row.complete_status" type="warning" link size="small" @click="cancelComplete(row)">取消完成</el-button>
            <el-button v-if="canManageRow(row)" type="primary" link size="small" @click="row.isEdit = true">编辑</el-button>
            <el-button v-if="isItemOwner(row) && row.id " type="warning" link size="small" @click="openTransfer(row)">转办</el-button>
            <el-popconfirm v-if="canManageRow(row) && !row.complete_status" title="确定删除该工作项？" confirm-button-type="danger" @confirm="removeItem(row)">
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

    <!-- 工作项转办弹窗：选择接收人 + 转出分数（不能超过剩余分值） -->
    <el-dialog v-model="transferDialogVisible" title="工作项转办" width="480px" draggable append-to-body>
      <el-form label-width="90px">
        <el-form-item label="工作项">
          <el-tag>{{ transferRow?.name }}</el-tag>
          <span style="margin-left: 8px; color: #909399;">剩余 {{ transferRow?.remaining_score }} 分</span>
        </el-form-item>
        <el-form-item label="接收人" required>
          <el-select v-model="transferTargetId" filterable placeholder="选择接收人" style="width: 100%">
            <el-option v-for="u in transferTargets" :key="u.id" :label="`${u.username}（${u.id}）`" :value="u.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="转出分数" required>
          <el-input-number
            v-model="transferScore"
            :min="0.01"
            :max="transferRow?.remaining_score || 0"
            :step="0.5"
            :precision="2"
            style="width: 100%"
            controls-position="right"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="transferDialogVisible = false">取消</el-button>
        <el-button type="warning" :loading="transferring" @click="confirmTransfer">发送转办</el-button>
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
  getAllUsersApi,
  initiateTransferApi,
  saveMonthScoreApi,
  saveQualityScoreApi,
  confirmCompletionApi
} from '../api'
import { useUserStore } from '../stores/user'
import { useLevelDefs } from '../comosables/useLevelDefs'

// 模块级缓存：展开行收起再展开时不重新请求后端（方案A），避免本地暂存/待审核行丢失
const workItemCache = new Map()

const props = defineProps({
  workPackageId: { type: String, required: true },
  // 父级「刷新」时递增该值，强制工作项表格拉取最新数据
  refreshKey: { type: Number, default: 0 }
})
const emit = defineEmits(['changed'])

const userStore = useUserStore()

const userOptions = ref([])   // 负责人下拉选项
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

const loadUsers = async () => {
  try {
    const res = await getAllUsersApi()
    userOptions.value = res.data?.data || []
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '获取用户列表失败')
  }
}

// 只有领导可以编辑质量分
const canManageQuality = computed(() => userStore.isLEADER)

// 当前用户是否是某个工作项的负责人（转办拆分后各自负责人不同）
const currentUserId = computed(() => String(userStore.userInfo?.id || ''))
const isItemOwner = (row) => {
  if (String(row.owner_id || '') === currentUserId.value ) return true
  if (userStore.isAdmin || userStore.isLEADER || userStore.isDEPARTMENT) return true
}
// 行级管理权限：包级权限（管理员/领导/科室/工作包负责人）或本人负责的工作项
const canManageRow = (row) => canManage.value || isItemOwner(row)
// 是否展示「操作」列：包级可管理，或存在本人负责的工作项
const hasManage = computed(() => canManage.value || workItems.value.some(isItemOwner))

// ---- 工作项转办 ----
const transferDialogVisible = ref(false)
const transferRow = ref(null)
const transferTargetId = ref('')
const transferScore = ref(0)
const transferTargets = ref([])
const transferring = ref(false)

const openTransfer = async (row) => {
  transferRow.value = row
  transferTargetId.value = ''
  transferScore.value = Number(row.remaining_score || 0)
  try {
    const res = await getAllUsersApi()
    transferTargets.value = (res.data?.data || []).filter(u => String(u.id) !== currentUserId.value)
  } catch (err) {
    return ElMessage.error('获取用户列表失败')
  }
  transferDialogVisible.value = true
}

const confirmTransfer = async () => {
  if (!transferTargetId.value) return ElMessage.warning('请选择接收人')
  if (!transferScore.value || transferScore.value <= 0) return ElMessage.warning('请填写转出分数')
  if (transferScore.value > (transferRow.value?.remaining_score || 0)) {
    return ElMessage.warning('转出分数不能超过剩余分值')
  }
  transferring.value = true
  try {
    const res = await initiateTransferApi({
      transfer_type: 'work_item',
      work_item_id: transferRow.value.id,
      transfer_score: transferScore.value,
      from_user_id: userStore.userInfo?.id,
      to_user_id: transferTargetId.value
    })
    if (res.data?.code === 200) {
      ElMessage.success('转办申请已发送，等待接收人处理')
      transferDialogVisible.value = false
      await fetchData()
      notifyChanged()
    }
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '发起转办失败')
  } finally {
    transferring.value = false
  }
}

// 已完成工作项整行灰显
const rowClassName = ({ row }) => (row.complete_status ? 'completed-row' : '')

const notifyChanged = () => emit('changed')

// 缓存 key：按登录用户 + 工作包隔离，避免跨用户串数据
const cacheKey = () => `work_item_cache_${userStore.userInfo?.id || 'anon'}_${props.workPackageId}`

// 从 sessionStorage 读取缓存（页面刷新 / Vite 热更新后仍可恢复）
const loadCacheFromStorage = () => {
  try {
    const raw = sessionStorage.getItem(cacheKey())
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

// 同步当前状态到缓存（本地暂存/新增/待审核行都会保留；模块 Map + sessionStorage 双写）
const syncCache = () => {
  const data = {
    workPackage: workPackage.value,
    workItems: workItems.value.map(w => ({ ...w }))
  }
  workItemCache.set(props.workPackageId, data)
  try {
    sessionStorage.setItem(cacheKey(), JSON.stringify(data))
  } catch {
    /* 存储失败不影响主流程 */
  }
}

// 强制刷新后，把本地暂存/待审核行合并回服务器列表，避免被覆盖丢失
const mergeLocalRows = (serverItems) => {
  const cached = loadCacheFromStorage()
  const local = (cached?.workItems || []).filter(w => w.isStaged || w.isPending || w.isNew)
  if (!local.length) return serverItems
  const serverIds = new Set(serverItems.map(i => String(i.id)))
  const merged = serverItems.map(i => ({ ...i }))
  local.forEach(l => {
    const row = { ...l }
    // 已暂存（未提交）→ 始终保留（服务器上还是旧数据）
    if (row.isStaged) { merged.unshift(row); return }
    // 待审核且服务器已存在同 id → 已生效，去掉本地记录
    if (row.id && serverIds.has(String(row.id))) return
    // 其余（新增未落库 / 待审核）→ 放回表格最前
    merged.unshift(row)
  })
  return merged
}

const fetchData = async (force = false) => {
  loading.value = true
  try {
    // 非强制：优先用模块缓存，其次 sessionStorage，命中即恢复，不请求后端（保留本地暂存/待审核状态）
    if (!force) {
      const cached = workItemCache.get(props.workPackageId) || loadCacheFromStorage()
      if (cached) {
        workPackage.value = cached.workPackage
        workItems.value = (cached.workItems || []).map(item => ({
          ...item,
          isEdit: false,
          isEditMonth: false,
          isEditQuality: false
        }))
        return
      }
    }

    const res = await getWorkItemsApi(props.workPackageId)
    if (res.data?.code === 200) {
      workPackage.value = res.data.data.work_package
      const serverItems = (res.data.data.work_items || []).map(item => ({
        ...item,
        isEdit: false,
        isNew: false,
        isPending: false,
        isStaged: false,
        isEditMonth: false,
        isEditQuality: false,
        _original: JSON.parse(JSON.stringify(item))
      }))
      // 强制刷新时合并回本地暂存/待审核行，避免被后端数据覆盖掉
      workItems.value = force ? mergeLocalRows(serverItems) : serverItems
      syncCache()
    }
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '获取工作项失败')
  } finally {
    loading.value = false
  }
}

// 工作项 ID 变化（展开不同工作包）时重新加载
watch(() => props.workPackageId, () => fetchData())
// 父级「刷新」时强制拉取最新数据
watch(() => props.refreshKey, () => fetchData(true))

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
    owner_id: workPackage.value?.owner_id || '',
    isEdit: true,
    isNew: true,
    isPending: false,
    isStaged: false,
    isEditMonth: false,
    isEditQuality: false
  })
  syncCache()
}

// 必填校验：名称 / 难度 / 重要度 / 创新度 / 截止时间 / 分值
const validateWorkItemFields = (row) => {
  if (!row.name || !row.name.trim()) return '请填写工作项名称'
  if (!row.difficulty) return '请选择难度'
  if (!row.importance) return '请选择重要度'
  if (!row.innovation) return '请选择创新度'
  if (!row.deadline) return '请选择截止时间'
  if (!row.score || Number(row.score) <= 0) return '请填写基础总分值（需大于 0）'
  return ''
}

// 行内「保存」：校验并暂存到本地（不提交审核，等待「提交」一起提交）
const handleSaveLocal = (row) => {
  const msg = validateWorkItemFields(row)
  if (msg) return ElMessage.warning(msg)
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
  syncCache()
  ElMessage.success('已保存，点击「提交」可一起提交审核')
}

// 头部「提交」：收集所有已暂存的修改
const handleOpenBatchSubmit = () => {
  const staged = workItems.value.filter(w => w.isStaged)
  if (!staged.length) return ElMessage.warning('暂无可提交的修改，请先保存')
  for (const w of staged) {
    const msg = validateWorkItemFields(w)
    if (msg) return ElMessage.warning(`「${w.name || '未命名'}」：${msg}，请先保存`)
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
        score: row.score,
        owner_id: row.owner_id,
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
      syncCache()
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
      await fetchData(true)
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
      await fetchData(true)
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
      await fetchData(true)
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
      await fetchData(true)
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
      await fetchData(true)
      notifyChanged()
    }
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '取消完成失败')
  }
}

onMounted(() => {
  fetchData()
  loadUsers()
})
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

.employee-text {
  color: #0f766e;
  font-weight: 500;
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
