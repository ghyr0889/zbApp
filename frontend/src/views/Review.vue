<!-- xiangmu/frontend/src/views/Review.vue -->
<template>
  <div class="review-page">
    <el-card class="box-card" shadow="never">
      <!-- 头部 -->
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <span class="header-title">审批查阅</span>
          </div>
          <div class="header-right">
            <el-button type="primary" plain size="default" @click="handleRefresh">
              🔄 刷新列表
            </el-button>
          </div>
        </div>
      </template>
      
      <!-- 标签页：审批查阅 / 工作包转办 -->
      <el-tabs v-model="activeTab" class="custom-tabs">
        <el-tab-pane label="审批查阅" name="review">
      <div class="table-container">
        <el-table 
          :data="requests" 
          v-loading="loading" 
          style="width: 100%" 
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
                  :header-cell-style="{ background: '#f1f5f9', color: '#475569', fontWeight: '500' }"
                >
                  <el-table-column prop="name" label="工作项名称" min-width="140" />
                  <el-table-column prop="standard" label="完成标准" min-width="180" show-overflow-tooltip>
                    <template #default="{ row }">
                      <span class="standard-text">{{ row.standard || '-' }}</span>
                    </template>
                  </el-table-column>
                  <el-table-column prop="difficulty" label="难度" width="80" align="center">
                    <template #default="{ row }">{{ row.difficulty || '-' }}</template>
                  </el-table-column>
                  <el-table-column prop="importance" label="重要度" width="80" align="center">
                    <template #default="{ row }">{{ row.importance || '-' }}</template>
                  </el-table-column>
                  <el-table-column prop="innovation" label="创新度" width="80" align="center">
                    <template #default="{ row }">{{ row.innovation || '-' }}</template>
                  </el-table-column>
                  <el-table-column prop="category" label="工作类型" width="80" align="center">
                    <template #default="{ row }">{{ row.category || '-' }}</template>
                  </el-table-column>
                  <el-table-column prop="deadline" label="截止日期" width="120" align="center">
                    <template #default="{ row }">
                      <span class="date-text">{{ row.deadline || '-' }}</span>
                    </template>
                  </el-table-column>
                  <el-table-column prop="score" label="分值" width="90" align="center">
                    <template #default="{ row }">
                      <span class="score-text">{{ row.score ?? 0 }}</span>
                    </template>
                  </el-table-column>
                </el-table>
                
                <!-- 最下面一行：高亮修改说明 -->
                <div class="modification-reason">
                  <div class="reason-label">修改说明：</div>
                  <div class="reason-content">{{ row.reason || '申请人未填写说明信息' }}</div>
                </div>
              </div>
            </template>
          </el-table-column>

          <!-- 2. 外层表格列 -->
          <el-table-column prop="project_name" label="项目名称" min-width="160" show-overflow-tooltip />
          <el-table-column label="工作包编号" min-width="120">
            <template #default="{ row }">
              <span>{{ row.work_package_code }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="project_owner_name" label="项目负责人" min-width="100" />
          <el-table-column prop="applicant_name" label="申请人" width="100" />        
          <el-table-column prop="created_at" label="提交时间" width="160" align="center">
            <template #default="{ row }">
              <span class="date-text">{{ row.created_at }}</span>
            </template>
          </el-table-column>
          <el-table-column label="状态" width="110" align="center">
            <template #default="{ row }">
              <el-tag :type="statusTagType(row.status)" effect="light" round>
                {{ statusLabel(row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column v-if="canReview" label="操作" width="200" align="center" fixed="right">
            <template #default="{ row }">
              <template v-if="row.status === 'PENDING'">
                <template v-if="pendingIsEdit">
                  <el-button type="info" size="small" plain @click="handleSubmit(row)">提交</el-button>
                  <el-button type="success" size="small" plain @click="handlePass(row)">通过</el-button>
                  <el-button type="danger" size="small" plain @click="openRejectDialog(row)">驳回</el-button>
                </template>
              </template>
              <template v-else-if="row.status === 'SUBMITTED'">
                <template v-if="submittedIsEdit">
                  <el-button type="success" size="small" plain @click="handlePass(row)">通过</el-button>
                  <el-button type="danger" size="small" plain @click="openRejectDialog(row)">驳回</el-button>
                </template>
              </template>
              <span v-else class="muted-text">已处理完毕</span>
            </template>
          </el-table-column>
        </el-table>
      </div>
        </el-tab-pane>

        <!-- 工作包转办标签页 -->
        <!-- <el-tab-pane label="工作包转办" name="transfers">
          <div class="transfers-container"> -->
            <!-- 收到的转办申请 -->
            <!-- <div class="transfer-section">
              <div class="section-title">收到给我的转办申请</div>
              <el-table :data="incomingTransfers" v-loading="loadingIncoming" border style="width: 100%" empty-text="暂无待处理的转办申请" :header-cell-style="{ background: '#f8fafc', color: '#1e293b', fontWeight: '600' }">
                <el-table-column prop="from_username" label="发起人" width="110" align="center" />
                <el-table-column prop="work_package_id" label="工作包编号" width="130" align="center" />
                <el-table-column prop="project_code" label="所属项目" min-width="140" show-overflow-tooltip />
                <el-table-column prop="created_at" label="发起时间" width="160" align="center" />
                <el-table-column label="操作" width="160" align="center" fixed="right">
                  <template #default="{ row }">
                    <el-button type="success" size="small" plain @click="handleAcceptTransfer(row)">接受</el-button>
                    <el-button type="danger" size="small" plain @click="handleRejectTransfer(row)">拒绝</el-button>
                  </template>
                </el-table-column>
              </el-table>
            </div> -->

            <!-- 我发起的转办申请 -->
            <!-- <div class="transfer-section">
              <div class="section-title">我发起的转办申请</div>
              <el-table :data="outgoingTransfers" v-loading="loadingOutgoing" border style="width: 100%" empty-text="暂无发起的转办申请" :header-cell-style="{ background: '#f8fafc', color: '#1e293b', fontWeight: '600' }">
                <el-table-column prop="to_username" label="接收人" width="110" align="center" />
                <el-table-column prop="work_package_id" label="工作包编号" width="130" align="center" />
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
        </el-tab-pane> -->
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
import { computed, onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getIncomingTransfersApi, getMyOutgoingTransfersApi, getSplitRequestsApi, processTransferApi, reviewSplitRequestApi } from '../api'

const activeTab = ref('review')
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

const handleSubmit = (row) => {
  ElMessageBox.confirm('确认将该申请提交给领导审核？提交后由领导最终审批。', '提交领导审核', {
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
        ElMessage.success(res.data.message || '已提交，等待领导审核')
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
  ElMessageBox.confirm(`确认接受「${row.work_package_id}」的转办？接受后该工作包及全部工作项将归你负责。`, '接受转办', {
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
  ElMessageBox.confirm(`确认拒绝「${row.work_package_id}」的转办？`, '拒绝转办', {
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
})
</script>

<style scoped>
.review-page { 
  padding: 24px; 
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
  gap: 6px;
  padding: 16px;
  background-color: #eff6ff; /* 淡蓝色背景 */
  border: 1px solid #bfdbfe;
  border-left: 4px solid #3b82f6; /* 强蓝色左侧边框 */
  border-radius: 6px;
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
</style>