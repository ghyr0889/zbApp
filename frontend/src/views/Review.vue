<!-- xiangmu/frontend/src/views/Review.vue -->
<template>
  <div class="review-page">
    <el-card class="box-card" shadow="never">
      <template #header>
        <!-- 新增：搜索栏和控制按钮区域 -->
        <div class="action-bar">
          <div class="search-area">
            <el-input 
              v-model="searchKeyword" 
              placeholder="输入申请人进行搜索..." 
              clearable 
              prefix-icon="Search"
              style="width: 180px;" 
            />
            <el-select 
              v-model="searchStatus" 
              placeholder="根据状态进行筛选..." 
              clearable 
              style="width: 160px;"
            >
              <el-option label="待科室审核" value="PENDING" />
              <el-option label="待领导审核" value="SUBMITTED" />
              <el-option label="已通过" value="APPROVED" />
              <el-option label="已驳回" value="REJECTED" />
            </el-select>
          </div>
          <el-button type="primary" plain size="default" @click="handleRefresh">
            刷新
          </el-button>
        </div>
      </template>

      <!-- 标签页：审批查阅 / 工作包转办 -->
      <el-tabs v-model="activeTab" class="custom-tabs">
      <el-tab-pane label="审批查阅" name="review">

        <div class="table-container">
          <el-table 
            ref="tableRef"
            :data="filteredRequests" 
            v-loading="loading"
            shadow="never" 
            border
            row-key="id"
            style="width: 100%" 
            height="calc(100vh - 300px)"
            empty-text="当前没有需要处理的申请"
            :header-cell-style="{ background: '#f8fafc', color: '#1e293b', fontWeight: '600', height: '48px' }"
            :row-style="{ height: '56px' }"
          >
          
          <!-- 1. 内层表格：美化展开行 -->
          <el-table-column type="expand">
            <template #default="{ row }">
              <div class="expand-wrapper">
                <div class="expand-header">
                  <span class="expand-title">具体工作项明细</span>
                  <el-tag size="small" type="info" class="count-tag">共 {{ row.split_items?.length || 0 }} 项</el-tag>
                </div>
                
                <el-table 
                  :data="row.split_items" 
                  border 
                  size="small" 
                  style="width: 100%; margin-bottom: 20px;"
                >
                <el-table-column prop="name" label="工作项名称" min-width="150">
                  <template #default="{ row: itemRow }">
                    <el-input v-if="canEditRequest(row) && row.isEditing" v-model="itemRow.name" size="small" />
                    <span v-else>{{ itemRow.name || '-' }}</span>
                  </template>
                </el-table-column>

                <el-table-column prop="standard" label="完成标准" min-width="180">
                  <template #default="{ row: itemRow }">
                    <el-input v-if="canEditRequest(row) && row.isEditing" v-model="itemRow.standard" size="small" />
                    <span v-else class="standard-text">{{ itemRow.standard || '-' }}</span>
                  </template>
                </el-table-column>

                <el-table-column prop="difficulty" label="难度" min-width="90" align="center">
                  <template #default="{ row: itemRow }">
                    <el-select v-if="canEditRequest(row) && row.isEditing" v-model="itemRow.difficulty" size="small">
                      <el-option v-for="o in levelDefs.difficulty" :key="o" :label="o" :value="o" />
                    </el-select>
                    <el-tag v-else size="small">{{ itemRow.difficulty || '-' }}</el-tag>
                  </template>
                </el-table-column>

                <el-table-column prop="importance" label="重要度" min-width="90" align="center">
                  <template #default="{ row: itemRow }">
                    <el-select v-if="canEditRequest(row) && row.isEditing" v-model="itemRow.importance" size="small">
                      <el-option v-for="o in levelDefs.importance" :key="o" :label="o" :value="o" />
                    </el-select>
                    <el-tag v-else size="small">{{ itemRow.importance || '-' }}</el-tag>
                  </template>
                </el-table-column>

                <el-table-column prop="innovation" label="创新度" min-width="90" align="center">
                  <template #default="{ row: itemRow }">
                    <el-select v-if="canEditRequest(row) && row.isEditing" v-model="itemRow.innovation" size="small">
                      <el-option v-for="o in levelDefs.innovation" :key="o" :label="o" :value="o" />
                    </el-select>
                    <span v-else>{{ itemRow.innovation || '-' }}</span>
                  </template>
                </el-table-column>

                <el-table-column label="负责人" min-width="120" align="center">
                  <template #default="{ row: itemRow }">
                    <el-select v-if="canEditRequest(row) && row.isEditing" v-model="itemRow.owner_id" filterable placeholder="选择负责人" size="small" style="width: 100%">
                      <el-option v-for="u in userOptions" :key="u.id" :label="`${u.username}（${u.id}）`" :value="u.id" />
                    </el-select>
                    <span v-else class="employee-text">{{ ownerName(itemRow.owner_id) || '-' }}</span>
                  </template>
                </el-table-column>

                <el-table-column prop="deadline" label="截止时间" min-width="130" align="center">
                  <template #default="{ row: itemRow }">
                    <el-date-picker
                      v-if="canEditRequest(row) && row.isEditing"
                      v-model="itemRow.deadline"
                      type="date"
                      value-format="YYYY-MM-DD"
                      size="small"
                      style="width: 100%"
                      placeholder="选择日期"
                    />
                    <el-tag v-else-if="itemRow.deadline" type="danger" effect="plain">{{ itemRow.deadline }}</el-tag>
                    <span v-else>-</span>
                  </template>
                </el-table-column>

                <el-table-column prop="score" label="基础总分值" min-width="90" align="center">
                  <template #default="{ row: itemRow }">
                    <el-input-number v-if="canEditRequest(row) && row.isEditing" v-model="itemRow.score" :min="0" :step="0.5" size="small" style="width: 100%" controls-position="right" />
                    <span v-else class="score-text">{{ itemRow.score }}</span>
                  </template>
                </el-table-column>

                <el-table-column prop="notes" label="备注" min-width="150">
                  <template #default="{ row: itemRow }">
                    <el-input v-if="canEditRequest(row) && row.isEditing" v-model="itemRow.notes" size="small" />
                    <span v-else>{{ itemRow.notes || '暂无备注' }}</span>
                  </template>
                </el-table-column>

                </el-table>
                
                <!-- 最下面一行：高亮修改说明 -->
                <div class="modification-reason">
                  <div class="reason-label">修改说明：</div>
                  <el-input v-if="canEditRequest(row) && row.isEditing" v-model="row.reason" type="textarea" :rows="2" size="small" placeholder="填写修改说明" style="margin-top: 8px" />
                  <div v-else class="reason-content">{{ row.reason || '申请人未填写说明信息' }}</div>
                </div>

                <!-- 编辑模式下的保存/取消 -->
                <div v-if="canEditRequest(row) && row.isEditing" class="edit-actions">
                  <el-button type="success" size="small" :loading="savingEdit" @click="handleSaveEdit(row)">保存修改</el-button>
                  <el-button type="info" size="small" @click="row.isEditing = false">取消</el-button>
                </div>
              </div>
            </template>
          </el-table-column>

          <!-- 2. 外层表格列 -->
          <el-table-column prop="project_name" label="项目名称" min-width="160" show-overflow-tooltip />
          <el-table-column label="工作包编号" min-width="100">
            <template #default="{ row }">
              <span>{{ row.work_package_code }}</span>
            </template>
          </el-table-column>
          <el-table-column label="工作包名称" min-width="100">
            <template #default="{ row }">
              <span>{{ row.work_package_name }}</span>
            </template>
          </el-table-column>
          <el-table-column label="工作包目标" min-width="100">
            <template #default="{ row }">
              <span>{{ row.work_package_objective }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="project_owner_name" label="项目负责人" min-width="100" />
          <el-table-column prop="applicant_name" label="申请人" min-width="100" />        
          <el-table-column prop="created_at" label="提交时间" min-width="160" align="center">
            <template #default="{ row }">
              <span class="date-text">{{ row.created_at }}</span>
            </template>
          </el-table-column>
          <el-table-column label="状态" min-width="110" align="center" fixed="right">
            <template #default="{ row }">
              <el-tag :type="statusTagType(row.status)" effect="light" round>
                {{ statusLabel(row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" min-width="280" align="center" fixed="right">
            <template #default="{ row }">
              <!-- 员工：被驳回的申请可以修改并重新提交 -->
              <template v-if="isEmployee && row.status === 'REJECTED' && isApplicant(row)">
                <el-button v-if="!row.isEditing" type="warning" size="small" plain @click="startEdit(row)">修改</el-button>
                <span v-else class="muted-text">编辑中</span>
              </template>
              <template v-else-if="canReview">
                <template v-if="row.status === 'PENDING'">
                  <template v-if="pendingIsEdit">
                    <el-button v-if="!row.isEditing" type="warning" size="small" plain @click="startEdit(row)">修改</el-button>
                    <el-button type="info" size="small" plain @click="handleSubmit(row)">提交</el-button>
                    <el-button type="success" size="small" plain @click="handlePass(row)">通过</el-button>
                    <el-button type="danger" size="small" plain @click="openRejectDialog(row)">驳回</el-button>
                  </template>
                </template>
                <template v-else-if="row.status === 'SUBMITTED'">
                  <template v-if="submittedIsEdit">
                    <el-button v-if="!row.isEditing" type="warning" size="small" plain @click="startEdit(row)">修改</el-button>
                    <el-button type="success" size="small" plain @click="handlePass(row)">通过</el-button>
                    <el-button type="danger" size="small" plain @click="openRejectDialog(row)">驳回</el-button>
                  </template>
                </template>
                <span v-else class="muted-text">已处理完毕</span>
              </template>
              <span v-else class="muted-text">-</span>
            </template>
          </el-table-column>
        </el-table>
      </div>
      </el-tab-pane>

        <!-- 工作包转办标签页：收件箱（接收/拒绝）+ 发件箱（状态） -->
        <el-tab-pane label="工作包转办" name="transfers">
          <div class="transfers-container">
            <!-- 收到的转办申请 -->
            <div class="transfer-section">
              <div class="section-title">收到给我的转办申请</div>
              <el-table :data="incomingTransfers" 
              v-loading="loadingIncoming" 
              border 
              style="width: 100%" 
              empty-text="暂无待处理的转办申请" 
              :header-cell-style="{ background: '#f8fafc', color: '#1e293b', fontWeight: '600' }"
              >
                <el-table-column label="类型" width="90" align="center">
                  <template #default="{ row }">
                    <el-tag size="small" :type="row.transfer_type === 'work_package' ? 'warning' : 'primary'" effect="plain">{{ transferTypeLabel(row.transfer_type) }}</el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="work_package_code" label="工作包编号" width="120" align="center" />
                <el-table-column prop="work_item_name" label="工作项" min-width="130" show-overflow-tooltip>
                  <template #default="{ row }">
                    <span v-if="row.transfer_type === 'work_item'">{{ row.work_item_name || '-' }}</span>
                    <span v-else class="muted-text">-</span>
                  </template>
                </el-table-column>
                <el-table-column label="转出分数" width="90" align="center">
                  <template #default="{ row }">
                    <span v-if="row.transfer_type === 'work_item'" class="score-text">{{ row.transfer_score }}</span>
                    <span v-else class="muted-text">-</span>
                  </template>
                </el-table-column>
                <el-table-column prop="from_username" label="发起人" width="100" align="center" />
                <el-table-column prop="project_name" label="所属项目" min-width="140" show-overflow-tooltip />
                <el-table-column prop="created_at" label="发起时间" width="160" align="center" />
                <el-table-column label="操作" width="150" align="center" fixed="right">
                  <template #default="{ row }">
                    <el-button type="success" size="small" plain @click="handleAcceptTransfer(row)">接受</el-button>
                    <el-button type="danger" size="small" plain @click="handleRejectTransfer(row)">拒绝</el-button>
                  </template>
                </el-table-column>
              </el-table>
            </div>

            <!-- 我发起的转办申请 -->
            <div class="transfer-section">
              <div class="section-title">我发起的转办申请</div>
              <el-table :data="outgoingTransfers" v-loading="loadingOutgoing" border style="width: 100%" empty-text="暂无发起的转办申请" :header-cell-style="{ background: '#f8fafc', color: '#1e293b', fontWeight: '600' }">
                <el-table-column label="类型" width="90" align="center">
                  <template #default="{ row }">
                    <el-tag size="small" :type="row.transfer_type === 'work_package' ? 'warning' : 'primary'" effect="plain">{{ transferTypeLabel(row.transfer_type) }}</el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="work_package_code" label="工作包编号" width="120" align="center" />
                <el-table-column prop="work_item_name" label="工作项" min-width="130" show-overflow-tooltip>
                  <template #default="{ row }">
                    <span v-if="row.transfer_type === 'work_item'">{{ row.work_item_name || '-' }}</span>
                    <span v-else class="muted-text">-</span>
                  </template>
                </el-table-column>
                <el-table-column label="转出分数" width="90" align="center">
                  <template #default="{ row }">
                    <span v-if="row.transfer_type === 'work_item'" class="score-text">{{ row.transfer_score }}</span>
                    <span v-else class="muted-text">-</span>
                  </template>
                </el-table-column>
                <el-table-column prop="to_username" label="接收人" width="100" align="center" />
                <el-table-column prop="project_name" label="所属项目" min-width="140" show-overflow-tooltip />
                <el-table-column label="状态" width="110" align="center">
                  <template #default="{ row }">
                    <el-tag :type="transferStatusTagType(row.status)" effect="light" round>{{ transferStatusLabel(row.status) }}</el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="created_at" label="发起时间" width="160" align="center" />
              </el-table>
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <!-- ============ 驳回原因弹窗 ============ -->
    <el-dialog v-model="rejectDialogVisible" title="填写驳回原因" width="460px" custom-class="custom-dialog" draggable>
      <el-form label-position="top">
        <el-form-item label="请详细说明驳回原因（必填）：" required>
          <el-input 
            v-model="rejectComment" 
            type="textarea" 
            :rows="4" 
            placeholder="例如：验收标准不够清晰，工作项分值分配不合理..." 
            resize="none"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="rejectDialogVisible = false">取消</el-button>
          <el-button type="danger" :loading="submitting" @click="confirmReject">确认驳回</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getIncomingTransfersApi, getMyOutgoingTransfersApi, getSplitRequestsApi, processTransferApi, reviewSplitRequestApi, editSplitRequestApi, getLevelDefsApi, getAllUsersApi } from '../api'

const activeTab = ref('review')
const searchKeyword = ref('')
const searchStatus = ref('')
const requests = ref([])
const loading = ref(false)
const incomingTransfers = ref([])
const outgoingTransfers = ref([])
const loadingIncoming = ref(false)
const loadingOutgoing = ref(false)
const submitting = ref(false)
const rejectDialogVisible = ref(false)
const rejectComment = ref('')
const currentRejectId = ref(null)
const userOptions = ref([])   // 负责人下拉选项
const ownerName = (id) => {
  const u = userOptions.value.find(x => String(x.id) === String(id))
  return u ? u.username : ''
}

const currentUser = ref(JSON.parse(localStorage.getItem('user_info') || '{}'))
const role = computed(() => String(currentUser.value.role || '').toUpperCase())

const isEmployee = computed(() => role.value === 'EMPLOYEE')
const isDepartment = computed(() => role.value === 'DEPARTMENT')
const isLeader = computed(() => role.value === 'LEADER')
const isAdmin = computed(() => role.value === 'ADMIN')
const canReview = computed(() => isLeader.value || isAdmin.value || isDepartment.value)

// 当前用户可操作的申请状态：科室审 PENDING（同意/提交/驳回），领导/管理员审 SUBMITTED（通过/驳回）
const pendingIsEdit = computed(() => isDepartment.value)
const submittedIsEdit = computed(() => isLeader.value || isAdmin.value)

const statusLabel = (s) => ({ PENDING: '待科室审核', SUBMITTED: '待领导审核', APPROVED: '已通过', REJECTED: '已驳回' }[s] || s)
const statusTagType = (s) => ({ PENDING: 'warning', SUBMITTED: 'primary', APPROVED: 'success', REJECTED: 'danger' }[s] || 'info')

// ============ 申请内容编辑（按角色×状态可改） ============
const tableRef = ref(null)
const savingEdit = ref(false)
// 工作项档位选项（编辑时下拉用）
const levelDefs = ref({ difficulty: [], importance: [], innovation: [] })

// 是否为申请人本人
const isApplicant = (row) => String(row.applicant_id || '') === String(currentUser.value.id || '')

// 当前用户能否编辑该申请：员工改被驳回的；领导/管理员改 SUBMITTED；科室改 PENDING
const canEditRequest = (row) => {
  if (row.status === 'REJECTED' && isEmployee.value && isApplicant(row)) return true
  if (row.status === 'SUBMITTED' && (isLeader.value || isAdmin.value)) return true
  if (row.status === 'PENDING' && isDepartment.value) return true
  return false
}

// 进入编辑模式（并展开该行）
const startEdit = (row) => {
  row.isEditing = true
  nextTick(() => {
    tableRef.value?.toggleRowExpansion(row, true)
  })
}

// 保存修改后的申请内容
const handleSaveEdit = async (row) => {
  for (const it of row.split_items || []) {
    if (!it.name || !it.name.trim()) return ElMessage.warning('请填写工作项名称')
    if (!it.difficulty) return ElMessage.warning('请选择难度')
    if (!it.importance) return ElMessage.warning('请选择重要度')
    if (!it.innovation) return ElMessage.warning('请选择创新度')
    if (!it.deadline) return ElMessage.warning('请选择截止时间')
  }
  if (!row.split_items || !row.split_items.some(it => (it.name || '').trim())) {
    return ElMessage.warning('请至少保留一个有名的工作项')
  }
  if (!(row.reason || '').trim()) {
    return ElMessage.warning('请填写修改说明')
  }
  savingEdit.value = true
  try {
    const res = await editSplitRequestApi(row.id, {
      editor_id: currentUser.value.id,
      reason: row.reason,
      split_items: row.split_items
    })
    if (res.data?.code === 200) {
      ElMessage.success(res.data.message || '已保存')
      row.isEditing = false
      await fetchRequests()
    }
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '保存失败')
  } finally {
    savingEdit.value = false
  }
}
const loadUsers = async () => {
  try {
    const res = await getAllUsersApi()
    userOptions.value = res.data?.data || []
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '获取用户列表失败')
  }
}

// 加载工作项档位选项
const fetchLevelDefs = async () => {
  try {
    const res = await getLevelDefsApi()
    if (res.data?.code === 200) {
      levelDefs.value = {
        difficulty: res.data.data.difficulty || [],
        importance: res.data.data.importance || [],
        innovation: res.data.data.innovation || []
      }
    }
  } catch { /* 档位加载失败不影响主流程 */ }
}

const fetchRequests = async () => {
  loading.value = true
  try {
    const res = await getSplitRequestsApi(currentUser.value.id)
    if (res.data?.code === 200) {
      requests.value = res.data.data || []
    }
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '获取申请列表失败')
  } finally {
    loading.value = false
  }
}

const filteredRequests = computed(() => {
  return requests.value.filter(req => {
    // 匹配申请人（如果输入框为空则全匹配，否则进行模糊包含匹配）
    const matchKeyowrd = !searchKeyword.value || 
      (req.applicant_name && req.applicant_name.includes(searchKeyword.value.trim()));
      
    // 匹配状态（如果下拉框为空则全匹配，否则进行精确匹配）
    const matchStatus = !searchStatus.value || req.status === searchStatus.value;
    
    return matchKeyowrd && matchStatus;
  });
})

const handleSubmit = (row) => {
  ElMessageBox.confirm('确认将该申请提交给领导审核？提交后由上级最终审批。', '提交审核', {
    confirmButtonText: '确认提交',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      const res = await reviewSplitRequestApi(row.id, {
        reviewer_id: currentUser.value.id,
        action: 'SUBMIT',
        comment: ''
      })
      if (res.data?.code === 200) {
        ElMessage.success(res.data.message || '已提交，等待审核')
        await fetchRequests()
      }
    } catch (err) {
      ElMessage.error(err.response?.data?.detail || '提交失败')
    }
  }).catch(() => {})
}

const handlePass = (row) => {
  ElMessageBox.confirm('确认通过该申请？通过后将为该工作包生成/更新工作项。', '确认通过', {
    confirmButtonText: '确定通过',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      const res = await reviewSplitRequestApi(row.id, {
        reviewer_id: currentUser.value.id,
        action: 'APPROVE',
        comment: '审核通过'
      })
      if (res.data?.code === 200) {
        ElMessage.success(res.data.message || '已通过并生成工作项')
        await fetchRequests()
      }
    } catch (err) {
      ElMessage.error(err.response?.data?.detail || '操作失败')
    }
  }).catch(() => {})
}

const openRejectDialog = (row) => {
  currentRejectId.value = row.id
  rejectComment.value = ''
  rejectDialogVisible.value = true
}

const confirmReject = async () => {
  if (!rejectComment.value.trim()) return ElMessage.warning('请填写驳回原因')
  submitting.value = true
  try {
    const res = await reviewSplitRequestApi(currentRejectId.value, {
      reviewer_id: currentUser.value.id,
      action: 'REJECT',
      comment: rejectComment.value.trim()
    })
    if (res.data?.code === 200) {
      ElMessage.success('已驳回该申请')
      rejectDialogVisible.value = false
      await fetchRequests()
    }
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '驳回失败')
  } finally {
    submitting.value = false
  }
}

// ============ 工作包转办 ============
const transferTypeLabel = (t) => (t === 'work_package' ? '工作包' : '工作项')
const transferStatusLabel = (s) => ({ PENDING: '待接收', ACCEPTED: '已被接受', REJECTED: '已被拒绝' }[s] || s)
const transferStatusTagType = (s) => ({ PENDING: 'warning', ACCEPTED: 'success', REJECTED: 'danger' }[s] || 'info')

const fetchIncomingTransfers = async () => {
  loadingIncoming.value = true
  try {
    const res = await getIncomingTransfersApi(currentUser.value.id)
    if (res.data?.code === 200) incomingTransfers.value = res.data.data || []
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '获取转办申请失败')
  } finally {
    loadingIncoming.value = false
  }
}

const fetchOutgoingTransfers = async () => {
  loadingOutgoing.value = true
  try {
    const res = await getMyOutgoingTransfersApi(currentUser.value.id)
    if (res.data?.code === 200) outgoingTransfers.value = res.data.data || []
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '获取我发起的转办失败')
  } finally {
    loadingOutgoing.value = false
  }
}

const handleAcceptTransfer = (row) => {
  const desc = row.transfer_type === 'work_item'
    ? `工作项「${row.work_item_name}」${row.transfer_score} 分`
    : `工作包「${row.work_package_code}」`
  ElMessageBox.confirm(`确认接受${desc}的转办？接受后该工作项将归你负责。`, '接受转办', {
    confirmButtonText: '确认接受',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      const res = await processTransferApi(row.id, 'ACCEPT')
      if (res.data?.code === 200) {
        ElMessage.success(res.data.message || '已接受转办')
        await fetchIncomingTransfers()
        await fetchOutgoingTransfers()
      }
    } catch (err) {
      ElMessage.error(err.response?.data?.detail || '操作失败')
    }
  }).catch(() => {})
}

const handleRejectTransfer = (row) => {
  const desc = row.transfer_type === 'work_item'
    ? `工作项「${row.work_item_name}」${row.transfer_score} 分`
    : `工作包「${row.work_package_code}」`
  ElMessageBox.confirm(`确认拒绝${desc}的转办？`, '拒绝转办', {
    confirmButtonText: '确认拒绝',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      const res = await processTransferApi(row.id, 'REJECT')
      if (res.data?.code === 200) {
        ElMessage.success('已拒绝该转办申请')
        await fetchIncomingTransfers()
        await fetchOutgoingTransfers()
      }
    } catch (err) {
      ElMessage.error(err.response?.data?.detail || '操作失败')
    }
  }).catch(() => {})
}

const handleRefresh = () => {
  fetchRequests()
  fetchIncomingTransfers()
  fetchOutgoingTransfers()
}

onMounted(() => {
  fetchRequests()
  fetchIncomingTransfers()
  fetchOutgoingTransfers()
  fetchLevelDefs()
  loadUsers()
})
</script>

<style scoped>
.review-page { 
  padding: 20px; 
  animation: fadeIn 0.4s ease; 
  background-color: #f1f5f9;
  min-height: calc(100vh - 80px);
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

.box-card { 
  border-radius: 12px; 
  border: none; 
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.04); 
  background-color: #ffffff;
}

/* 头部样式 */
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
.header-icon {
  font-size: 20px;
}
.header-title {
  font-size: 18px;
  font-weight: 600;
  color: #0f172a;
}

/* 表格容器稍微增加一点内边距，使其与头部过渡更自然 */
.table-container {
  padding: 12px 0;
}

/* 展开行编辑操作按钮区 */
.edit-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 12px;
}

/* 表格固定高度内部滚动，不受全局 flex:1 拉伸影响 */
:deep(.el-table) { flex: none !important; }

/* 工作包转办标签页 */
.transfers-container {
  padding: 12px 0;
}
.transfer-section {
  margin-bottom: 28px;
}
.section-title {
  font-size: 15px;
  font-weight: 600;
  color: #0f172a;
  margin-bottom: 12px;
  padding-left: 8px;
  border-left: 4px solid #409EFF;
}

/* 展开行包裹区域样式 */
.expand-wrapper { 
  margin: 12px 32px;
  padding: 20px; 
  background-color: #f8fafc; 
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  box-shadow: inset 0 2px 4px rgba(0,0,0,0.02);
}

.expand-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}
.expand-title {
  font-size: 15px;
  font-weight: 600;
  color: #334155;
}

/* 修改说明模块（高亮 Callout 样式） */
.modification-reason {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 8px;
  border: 1px solid #b8b9b9;
  border-radius: 4px;
}
.reason-label {
  font-size: 14px;
  font-weight: 600;
  color: #1e3a8a;
}
.reason-content {
  font-size: 14px;
  color: #334155;
  line-height: 1.6;
  margin-left: 24px;
}

/* 表格内文本颜色辅助 */
.score-text {
  font-weight: 600;
  color: #10b981;
}
.date-text {
  color: #64748b;
  font-family: monospace;
  font-size: 13px;
}
.standard-text {
  color: #475569;
}
.muted-text { 
  color: #94a3b8; 
  font-size: 13px; 
}

/* 新增的搜索和操作栏样式 */
.action-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1px;
  padding: 0 4px;
}

.search-area {
  display: flex;
  gap: 16px; /* 两个输入框之间的间距 */
}
</style>