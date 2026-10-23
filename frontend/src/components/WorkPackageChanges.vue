<!-- 工作包变更申请 -->
<template>
  <div>
    <div class="change-toolbar">
      <span>{{ isLeader ? '工作包增删改申请，仅支持通过或驳回' : '我提交的工作包增删改申请' }}</span>
      <el-select v-model="status" clearable placeholder="全部状态" style="width: 140px">
        <el-option v-for="(label, value) in statuses" :key="value" :label="label" :value="value" />
      </el-select>
      <el-button class="refresh-button" type="primary" plain size="default" :loading="loading" @click="fetchRows">刷新</el-button>
    </div>
    <el-table :data="filtered" v-loading="loading" border max-height="600">
      <el-table-column label="类型" width="80">
        <template #default="{ row }">{{ actions[row.action] }}</template>
      </el-table-column>
      <el-table-column label="工作包" min-width="180">
        <template #default="{ row }">
          {{ (row.after_data || row.before_data)?.code }} / {{ (row.after_data || row.before_data)?.name }}
        </template>
      </el-table-column>
      <el-table-column prop="project_name" label="项目" min-width="140" />
      <el-table-column prop="reason" label="申请原因" min-width="180" />
      <el-table-column prop="applicant_name" label="申请人" width="100" />
      <el-table-column label="状态" width="110" fixed="left">
        <template #default="{ row }">
          <span :class="['change-status', `change-status--${row.status.toLowerCase()}`]">
            {{ statuses[row.status] }}
          </span>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="提交时间" min-width="180" />
      <el-table-column label="操作" width="100">
        <template #default="{ row }">
          <el-button link type="primary" @click="open(row)">查看详情</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-dialog v-model="visible" title="工作包变更申请" width="min(1500px, 94vw)" draggable append-to-body>
      <template v-if="selected">
        <p>
          {{ actions[selected.action] }}申请 · {{ statuses[selected.status] }} · 申请人：{{ selected.applicant_name }}
        </p>
        <p class="application-reason">申请原因：<span class="applicant-reason-text">{{ selected.reason || '历史申请未填写' }}</span></p>
        <el-table :data="comparison" border class="package-comparison-table">
          <el-table-column prop="label" label="内容" width="110" fixed="left" />
          <el-table-column v-for="(label, key) in fields" :key="key" :label="label" :min-width="key === 'objective' ? 230 : ['tech_owner_id', 'owner_id'].includes(key) ? 190 : 160">
            <template #default="{ row }">
              <div class="detail-field-value" :class="{ 'is-changed': row.kind === 'after' && isChanged(key), 'is-deleted': row.kind === 'delete' }">
                <span v-if="row.kind === 'after' && isChanged(key)" class="detail-change-label">已修改</span>
                <span v-if="row.kind === 'delete'" class="detail-change-label">拟删除</span>
                <span>{{ displayValue(row.data, key) }}</span>
              </div>
            </template>
          </el-table-column>
        </el-table>
        <p v-if="selected.status !== 'PENDING'">
          审核人：{{ selected.reviewer_name }} · 审核时间：{{ selected.reviewed_at }}<br>审核意见：{{ selected.review_comment || '无' }}
        </p>
        <el-input 
          v-if="isLeader && selected.status === 'PENDING'" 
          v-model="comment" type="textarea" 
          :rows="3" 
          maxlength="2000" 
          placeholder="填写审核意见" 
          class="review-comment" />
      </template>
      <template #footer>
        <div class="detail-footer">
        <el-button :disabled="saving" @click="visible = false">关闭</el-button>
        <template v-if="isLeader && selected?.status === 'PENDING'">
          <el-button type="danger" :disabled="saving" @click="decide('REJECT')">驳回</el-button>
          <el-button type="primary" :loading="saving" @click="decide('APPROVE')">通过</el-button>
        </template>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getWorkPackageChangesApi, reviewWorkPackageChangeApi } from '../api'
import { useUserStore } from '../stores/user'
const store = useUserStore()
const isLeader = computed(() => String(store.userInfo?.role).toUpperCase() === 'LEADER')
const rows = ref([]), loading = ref(false), saving = ref(false), visible = ref(false)
const selected = ref(null), comment = ref(''), status = ref('')
const statuses = { PENDING: '待领导审核', APPROVED: '已通过', REJECTED: '已驳回' }
const actions = { create: '新增', update: '修改', delete: '删除' }
const fields = { 
  code: '工作包编号', 
  name: '名称', 
  project_id: '项目 ID', 
  category_name: '工作类型', 
  tech_owner_id: '技术负责人（工号）',
  owner_id: '负责人（工号）',
  objective: '工作目标' }
const filtered = computed(() => rows.value.filter(row => !status.value || row.status === status.value))
// 对比内容只读，领导不能在审核时改写申请方案。
const comparison = computed(() => {
  const entry = selected.value
  if (!entry) return []
  if (entry.action === 'create') return [{ kind: 'after', label: '申请内容', data: entry.after_data }]
  if (entry.action === 'delete') return [{ kind: 'delete', label: '删除内容', data: entry.before_data }]
  return [
    { kind: 'before', label: '修改前', data: entry.before_data },
    { kind: 'after', label: '申请内容', data: entry.after_data }
  ]
})
const displayValue = (data, key) => {
  const value = data?.[key]
  return value === null || value === undefined || value === '' ? '—' : value
}
const isChanged = (key) => {
  const entry = selected.value
  if (entry?.action !== 'update' || !entry.before_data || !entry.after_data) return false
  if (!Object.hasOwn(entry.before_data, key)) return false
  return String(entry.before_data[key] ?? '') !== String(entry.after_data[key] ?? '')
}
async function fetchRows() {
  loading.value = true
  try { rows.value = (await getWorkPackageChangesApi()).data.data || [] }
  catch (error) { ElMessage.error(error.response?.data?.detail || '获取申请失败') }
  finally { loading.value = false }
}
function open(row) { selected.value = row; comment.value = ''; visible.value = true }
async function decide(decision) {
  if (saving.value) return
  saving.value = true
  try {
    await ElMessageBox.confirm(
      decision === 'APPROVE' ? '确认通过？工作包变更将立即生效。' : '确认驳回该申请？', '审核确认')
    const res = await reviewWorkPackageChangeApi(selected.value.id, { decision, comment: comment.value })
    ElMessage.success(res.data.message)
    visible.value = false
    await Promise.all([fetchRows(), store.refreshPendingCount()])
  } catch (error) {
    if (error !== 'cancel' && error !== 'close') ElMessage.error(error.response?.data?.detail || '审核失败')
  } finally { saving.value = false }
}
onMounted(fetchRows)
defineExpose({ refresh: fetchRows })
</script>

<style scoped>
.change-toolbar { display: flex; gap: 12px; align-items: center; margin-bottom: 16px; flex-wrap: wrap; }
.change-toolbar > span { margin-right: auto; color: #64748b; }
.refresh-button { margin-left: auto; flex-shrink: 0; }
.detail-field-value { padding: 8px; white-space: pre-wrap; overflow-wrap: anywhere; }
.detail-field-value.is-changed { background: #fff4df; color: #875000; border-left: 3px solid #b86b00; border-radius: 4px; }
.detail-field-value.is-deleted { background: #fff0f0; color: #a13232; border-left: 3px solid #c45656; border-radius: 4px; }
.detail-change-label { display: block; font-size: 12px; font-weight: 600; margin-bottom: 6px; }
.package-comparison-table { margin-bottom: 16px; }
.detail-footer { display: flex; justify-content: flex-end; flex-wrap: wrap; gap: 8px; border-top: 1px solid #e4e7ed; padding-top: 16px; }
.detail-footer .el-button + .el-button { margin-left: 0; }
.applicant-reason-text { color: #1d5c91; font-weight: 600; background: #eef6ff; border-radius: 4px; padding: 2px 6px; box-decoration-break: clone; -webkit-box-decoration-break: clone; }
.application-reason { white-space: pre-wrap; overflow-wrap: anywhere; line-height: 1.7; }
.review-comment { margin-top: 16px; }
.change-status { font-weight: 600; }
.change-status--pending { color: #b45309; }   /* 待审核：琥珀色 */
.change-status--approved { color: #16794b; }  /* 已通过：绿色 */
.change-status--rejected { color: #c24141; }  /* 已驳回：红色 */
</style>
