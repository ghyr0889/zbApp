<!-- xiangmu/frontend/src/views/CompleteReview.vue -->
<template>
  <div class="complete-review-page">
    <el-card class="box-card" shadow="never">
      <div class="page-header">
        <div class="header-left">
          <span class="page-title">工作项完成审核</span>
          <span class="page-desc">
            工作项分值填满后不会自动提交；需手动申请完成，由该工作项的技术负责人审核，通过后才记录完成时间。
          </span>
        </div>
        <div class="header-right">
          <el-select v-model="statusFilter" size="default" style="width: 140px">
            <el-option label="全部" value="" />
            <el-option label="待审核" value="PENDING" />
            <el-option label="已通过" value="APPROVED" />
            <el-option label="已驳回" value="REJECTED" />
          </el-select>
          <el-button type="primary" plain size="default" :loading="loading" @click="fetchRequests">刷新</el-button>
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
            <el-button type="primary" link @click="openDetails(row)">查看详情</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="detailsVisible" title="工作项完成申请" width="min(1500px, 94vw)" draggable append-to-body
      :close-on-click-modal="false" :close-on-press-escape="!reviewing" :show-close="!reviewing">
      <template v-if="selected">
        <p>{{ statusLabel(selected.status) }} · 申请人：{{ selected.applicant_name }} · 提交时间：{{ selected.created_at }}</p>
        <p>所属项目：{{ selected.project_name }} · 工作包：{{ selected.work_package_code }} / {{ selected.work_package_name }}</p>
        <p class="completion-detail-reason">完成说明：{{ selected.reason || '历史申请未填写' }}</p>
        <el-table :data="selected.complete_item ? [selected.complete_item] : []" border empty-text="未取得工作项信息，请刷新列表" class="completion-detail-table">
          <el-table-column label="内容" width="110" fixed="left"><template #default>工作项内容</template></el-table-column>
          <el-table-column v-for="field in detailFields" :key="field.key" :label="field.label" :min-width="field.width || 160">
            <template #default="{ row }"><span class="completion-detail-value">{{ detailValue(row, field.key) }}</span></template>
          </el-table-column>
        </el-table>
        <p class="muted-text">表格展示工作项当前信息；完成说明为申请人提交的内容。</p>
        <p v-if="selected.status !== 'PENDING'" class="completion-detail-reason">
          审核人（工号）：{{ selected.reviewer_id || '—' }} · 审核时间：{{ selected.reviewed_at || '—' }}<br>
          审核意见：{{ selected.review_comment || '无' }}
        </p>
      </template>
      <template #footer>
        <div class="completion-detail-footer">
          <el-button :disabled="reviewing" @click="detailsVisible = false">关闭</el-button>
          <template v-if="selected?.complete_item && canReview(selected)">
            <el-button type="danger" :disabled="reviewing" @click="openReject(selected)">驳回</el-button>
            <el-button type="primary" :disabled="reviewing" @click="handleApprove(selected)">通过</el-button>
          </template>
        </div>
      </template>
    </el-dialog>

    <el-dialog v-model="qualityVisible" title="完成审批与质量评定" width="min(600px, 94vw)" draggable append-to-body :close-on-click-modal="false" :close-on-press-escape="!reviewing" :show-close="!reviewing">
      <p>工作项：{{ qualityTarget?.complete_item?.name }}</p>
      <p>基础总分：{{ qualityTarget?.complete_item?.score ?? 0 }} 分</p>
      <el-form label-position="top">
        <el-form-item label="质量系数（必填）" required>
          <el-input v-model="qualityPercent" :disabled="reviewing" placeholder="例如90表示90%，允许超过100" aria-label="质量系数百分比"><template #append>%</template></el-input>
        </el-form-item>
      </el-form>
      <p>质量分：<strong>{{ qualityPreview }}</strong> 分</p>
      <p>质量分 = 基础总分 ×（质量系数 ÷ 100 − 1）。计入审批当月，其他月份质量分清零。</p>
      <template #footer>
        <el-button :disabled="reviewing" @click="qualityVisible = false">取消</el-button>
        <el-button type="primary" :loading="reviewing" :disabled="!validQualityPercent" @click="submitQuality">通过并保存质量分</el-button>
      </template>
    </el-dialog>

    <!-- 驳回对话框：必须填写原因 -->
    <el-dialog v-model="rejectVisible" title="驳回完成申请" width="440px" draggable append-to-body :close-on-click-modal="false" :close-on-press-escape="!reviewing" :show-close="!reviewing">
      <div class="reject-target" v-if="rejectTarget">
        工作项：{{ rejectTarget.complete_item?.name || '-' }}
      </div>
      <el-input v-model="rejectComment" type="textarea" :rows="3" placeholder="请填写驳回原因（必填）" />
      <template #footer>
        <el-button :disabled="reviewing" @click="rejectVisible = false">取消</el-button>
        <el-button type="danger" :loading="reviewing" @click="submitReject">确认驳回</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getCompleteRequestsApi, reviewCompleteRequestApi } from '../../api'
import { useUserStore } from '../../stores/user'

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

const detailsVisible = ref(false)
const selected = ref(null)
const openDetails = row => { selected.value = row; detailsVisible.value = true }
const detailFields = [
  { key: 'name', label: '工作项名称' },
  { key: 'standard', label: '完成标准', width: 230 },
  { key: 'difficulty', label: '难度', width: 100 },
  { key: 'importance', label: '重要度', width: 100 },
  { key: 'innovation', label: '创新度', width: 100 },
  { key: 'tech_owner_id', label: '技术负责人（工号）', width: 190 },
  { key: 'owner_id', label: '负责人（工号）', width: 190 },
  { key: 'deadline', label: '截止时间' },
  { key: 'score', label: '基础总分值', width: 120 },
  { key: 'progress', label: '进度', width: 100 },
  { key: 'notes', label: '备注', width: 230 }
]
const detailValue = (item, key) => {
  const value = item[key]
  if (value === null || value === undefined || value === '') return '—'
  if (key === 'tech_owner_id' || key === 'owner_id') {
    const name = item[key.replace('_id', '_name')]
    return name ? `${name}（${value}）` : value
  }
  return key === 'progress' ? `${value}%` : value
}

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

// 仅该工作项的技术负责人可以审核。
const canReview = (row) => {
  if (row.status !== 'PENDING') return false
  if (isMyReview(row)) return true
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

const submitReview = async (row, action, comment, qualityPercent = null) => {
  if (reviewing.value) return false
  reviewing.value = true
  try {
    const res = await reviewCompleteRequestApi(row.id, {
      reviewer_id: currentUser.value.id,
      action,
      quality_percent: qualityPercent,
      comment
    })
    if (res.data?.code === 200) {
      ElMessage.success(res.data.message || '操作成功')
      detailsVisible.value = false
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

const qualityVisible = ref(false), qualityTarget = ref(null), qualityPercent = ref('')
const validQualityPercent = computed(() => /^\d+(\.\d{1,2})?$/.test(qualityPercent.value.trim()) && Number.isFinite(Number(qualityPercent.value)))
const qualityPreview = computed(() => {
  if (!validQualityPercent.value) return '—'
  const value = Number(qualityTarget.value?.complete_item?.score || 0) * (Number(qualityPercent.value) / 100 - 1)
  return Number.isFinite(value) ? value.toFixed(2) : '—'
})
const handleApprove = row => {
  if (reviewing.value) return
  qualityTarget.value = row
  qualityPercent.value = ''
  qualityVisible.value = true
}
const submitQuality = async () => {
  if (!validQualityPercent.value || qualityPreview.value === '—') return ElMessage.warning('请填写有效的非负百分比，最多两位小数')
  if (await submitReview(qualityTarget.value, 'APPROVE', '', Number(qualityPercent.value))) qualityVisible.value = false
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
.completion-detail-reason { white-space: pre-wrap; overflow-wrap: anywhere; line-height: 1.7; margin: 24px 0; }
.completion-detail-value { display: block; padding: 8px; white-space: pre-wrap; overflow-wrap: anywhere; }
.completion-detail-table { margin: 24px 0 16px; }
.completion-detail-footer { display: flex; justify-content: flex-end; flex-wrap: wrap; gap: 8px; border-top: 1px solid #e4e7ed; padding-top: 16px; }
.completion-detail-footer .el-button + .el-button { margin-left: 0; }

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
  margin-left: auto;
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
