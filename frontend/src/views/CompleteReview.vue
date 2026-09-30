<!-- xiangmu/frontend/src/views/CompleteReview.vue -->
<template>
  <div class="complete-review-page">
    <el-card class="box-card" shadow="never">
      <div class="page-header">
        <div class="header-left">
          <span class="page-title">工作项完成审核</span>
          <span class="page-desc">
            工作项进度满或负责人提交后，由该工作项的技术负责人审核；审核通过才记录完成时间。
          </span>
        </div>
        <div class="header-right">
          <el-select v-model="statusFilter" size="default" style="width: 140px">
            <el-option label="全部" value="" />
            <el-option label="待审核" value="PENDING" />
            <el-option label="已通过" value="APPROVED" />
            <el-option label="已驳回" value="REJECTED" />
          </el-select>
          <el-button type="primary" plain :loading="loading" @click="fetchRequests">刷新</el-button>
        </div>
      </div>

      <el-table
        :data="filteredRequests"
        v-loading="loading"
        border
        style="width: 100%"
        height="calc(100vh - 400px)"
        empty-text="暂无完成申请"
        :header-cell-style="{ background: '#f8fafc', color: '#334155' }">
        <el-table-column label="状态" width="100" align="center" fixed="left">
          <template #default="{ row }">
            <el-tag :type="statusTagType(row.status)" effect="light" size="small">{{ statusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>

        <el-table-column label="工作项" min-width="200">
          <template #default="{ row }">
            <div class="item-cell">
              <span class="item-name">{{ row.complete_item?.name || '-' }}</span>
              <span class="item-progress">进度 {{ row.complete_item?.progress ?? 0 }}%</span>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="所属工作包" min-width="170">
          <template #default="{ row }">
            {{ row.work_package_name || '-' }}
            <span class="muted-text">（{{ row.work_package_code || '-' }}）</span>
          </template>
        </el-table-column>

        <el-table-column label="所属项目" min-width="140">
          <template #default="{ row }">{{ row.project_name || '-' }}</template>
        </el-table-column>

        <el-table-column label="申请人" width="110" align="center">
          <template #default="{ row }">{{ row.applicant_name || '-' }}</template>
        </el-table-column>

        <el-table-column label="技术负责人" width="120" align="center">
          <template #default="{ row }">
            <span :class="isMyReview(row) ? 'my-review-text' : ''">
              {{ row.complete_item?.tech_owner_name || '未指定' }}
            </span>
          </template>
        </el-table-column>

        <el-table-column label="提交说明" min-width="150">
          <template #default="{ row }">{{ row.reason || '-' }}</template>
        </el-table-column>

        <el-table-column prop="created_at" label="提交时间" width="150" align="center" />
        <el-table-column prop="reviewed_at" label="审核时间" width="150" align="center" />

        <!-- 只有已驳回的才显示原因：判断必须放在作用域插槽里，不能写在 el-table-column 的 v-if 上 -->
        <el-table-column label="驳回原因" min-width="150" >
          <template #default="{ row }">
            <span v-if="row.status === 'REJECTED'">{{ row.review_comment || '-' }}</span>
            <span v-else class="muted-text">-</span>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="150" align="center" fixed="right">
          <template #default="{ row }">
            <template v-if="canReview(row)">
              <el-button type="success" link size="small" :loading="reviewing" @click="handleApprove(row)">通过</el-button>
              <el-button type="danger" link size="small" :loading="reviewing" @click="openReject(row)">驳回</el-button>
            </template>
            <span v-else class="muted-text">-</span>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 驳回对话框：必须填写原因 -->
    <el-dialog v-model="rejectVisible" title="驳回完成申请" width="440px">
      <div class="reject-target" v-if="rejectTarget">
        工作项：{{ rejectTarget.complete_item?.name || '-' }}
      </div>
      <el-input v-model="rejectComment" type="textarea" :rows="3" placeholder="请填写驳回原因（必填）" />
      <template #footer>
        <el-button @click="rejectVisible = false">取消</el-button>
        <el-button type="danger" :loading="reviewing" @click="submitReject">确认驳回</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getCompleteRequestsApi, reviewCompleteRequestApi } from '../api'
import { useUserStore } from '../stores/user'

const userStore = useUserStore()
const currentUser = computed(() => userStore.userInfo)
const role = computed(() => String(currentUser.value?.role || '').toUpperCase())

const requests = ref([])
const loading = ref(false)
const reviewing = ref(false)
const statusFilter = ref('')
const rejectVisible = ref(false)
const rejectComment = ref('')
const rejectTarget = ref(null)

const statusLabel = (s) => ({ PENDING: '待审核', APPROVED: '已通过', REJECTED: '已驳回' }[s] || s)
const statusTagType = (s) => ({ PENDING: 'warning', APPROVED: 'success', REJECTED: 'danger' }[s] || 'info')

const filteredRequests = computed(() =>
  statusFilter.value ? requests.value.filter(r => r.status === statusFilter.value) : requests.value
)

// 是否轮到我审核：我就是该工作项的技术负责人
const isMyReview = (row) => {
  const techOwnerId = row.complete_item?.tech_owner_id || ''
  return !!techOwnerId && String(techOwnerId) === String(currentUser.value?.id || '')
}

// 可审核：待审核状态 + （我本人是技术负责人 或 未指定技术负责人时由领导/管理员兜底）
const canReview = (row) => {
  if (row.status !== 'PENDING') return false
  if (isMyReview(row)) return true
  if (!row.complete_item?.tech_owner_id && ['LEADER', 'ADMIN'].includes(role.value)) return true
  return false
}

const fetchRequests = async () => {
  if (!currentUser.value) return
  loading.value = true
  try {
    const res = await getCompleteRequestsApi(currentUser.value.id)
    if (res.data?.code === 200) requests.value = res.data.data || []
    // 列表变化后同步全局待办计数（菜单红点 / 完成申请角标）
    userStore.refreshPendingCount()
  } catch (err) {
    console.error(err)
    ElMessage.error(err.response?.data?.detail || '获取完成申请失败')
  } finally {
    loading.value = false
  }
}

const submitReview = async (row, action, comment) => {
  reviewing.value = true
  try {
    const res = await reviewCompleteRequestApi(row.id, {
      reviewer_id: currentUser.value.id,
      action,
      comment
    })
    if (res.data?.code === 200) {
      ElMessage.success(res.data.message || '操作成功')
      // fetchRequests 内部会同步全局待办计数
      await fetchRequests()
      return true
    }
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '审核失败')
  } finally {
    reviewing.value = false
  }
  return false
}

const handleApprove = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确认通过「${row.complete_item?.name || '该工作项'}」的完成申请？通过后会记录完成时间。`,
      '审核通过',
      { confirmButtonText: '确认通过', cancelButtonText: '取消', type: 'warning' }
    )
  } catch {
    return   // 取消
  }
  await submitReview(row, 'APPROVE', '')
}



const openReject = (row) => {
  rejectTarget.value = row
  rejectComment.value = ''
  rejectVisible.value = true
}

const submitReject = async () => {
  const comment = rejectComment.value.trim()
  if (!comment) return ElMessage.warning('请填写驳回原因')
  const ok = await submitReview(rejectTarget.value, 'REJECT', comment)
  if (ok) rejectVisible.value = false
}

onMounted(fetchRequests)
</script>

<style scoped>
.complete-review-page {
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

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
  padding-bottom: 14px;
  border-bottom: 1px solid #e2e8f0;
  margin-bottom: 14px;
}

.header-left {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.page-title {
  font-size: 18px;
  font-weight: 600;
  color: #1e293b;
}

.page-desc {
  font-size: 13px;
  color: #94a3b8;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 10px;
}

.item-cell {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.item-name {
  color: #1e293b;
  font-weight: 500;
}

.item-progress {
  font-size: 12px;
  color: #94a3b8;
}

.my-review-text {
  color: #409eff;
  font-weight: 600;
}

.muted-text {
  color: #94a3b8;
}

.reject-target {
  margin-bottom: 10px;
  color: #475569;
  font-size: 14px;
}
</style>
