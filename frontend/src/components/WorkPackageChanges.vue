<!--- 工作包增删改查组件 -->>
<template>
  <div>
    <div class="change-toolbar">
      <span>{{ isLeader ? '工作包增删改申请，仅支持通过或驳回' : '我提交的工作包增删改申请' }}</span>
      <el-select v-model="status" clearable placeholder="全部状态" style="width: 140px">
        <el-option v-for="(label, value) in statuses" :key="value" :label="label" :value="value" />
      </el-select>
      <el-button :loading="loading" @click="fetchRows">刷新</el-button>
    </div>
    <el-table :data="filtered" v-loading="loading" border max-height="600">
      <el-table-column prop="id" label="申请编号" width="90" />
      <el-table-column label="类型" width="80">
        <template #default="{ row }">{{ actions[row.action] }}</template>
      </el-table-column>
      <el-table-column label="工作包" min-width="180">
        <template #default="{ row }">
          {{ (row.after_data || row.before_data)?.code }} / {{ (row.after_data || row.before_data)?.name }}
        </template>
      </el-table-column>
      <el-table-column prop="project_name" label="项目" min-width="140" />
      <el-table-column prop="reason" label="申请原因" min-width="180" show-overflow-tooltip />
      <el-table-column prop="applicant_name" label="申请人" width="100" />
      <el-table-column label="状态" width="110">
        <template #default="{ row }">{{ statuses[row.status] }}</template>
      </el-table-column>
      <el-table-column prop="created_at" label="提交时间" min-width="180" />
      <el-table-column label="操作" width="100">
        <template #default="{ row }">
          <el-button link type="primary" @click="open(row)">查看详情</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-dialog v-model="visible" title="工作包变更申请" width="min(850px, 94vw)" draggable append-to-body>
      <template v-if="selected">
        <p>
          {{ actions[selected.action] }}申请 · {{ statuses[selected.status] }} · 申请人：{{ selected.applicant_name }}
        </p>
        <p class="application-reason">申请原因：{{ selected.reason || '历史申请未填写' }}</p>
        <el-table :data="comparison" border max-height="420">
          <el-table-column prop="label" label="字段" width="130" />
          <!-- 新增申请没有原工作包，不显示修改前内容。 -->
          <el-table-column v-if="selected.action !== 'create'" prop="before" label="修改前" min-width="200" />
          <el-table-column label="申请内容" min-width="200">
            <template #default="{ row }">
              <span :class="{ changed: row.before !== row.after }">{{ row.after }}</span>
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
        <el-button :disabled="saving" @click="visible = false">关闭</el-button>
        <template v-if="isLeader && selected?.status === 'PENDING'">
          <el-button type="danger" :disabled="saving" @click="decide('REJECT')">驳回</el-button>
          <el-button type="primary" :loading="saving" @click="decide('APPROVE')">通过</el-button>
        </template>
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
const comparison = computed(() => Object.entries(fields).map(([key, label]) => ({
  label, before: selected.value?.before_data?.[key] ?? '—', after: selected.value?.after_data?.[key] ?? '—',
})))
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
.changed { color: #409eff; font-weight: 600; white-space: pre-wrap; }
.application-reason { white-space: pre-wrap; overflow-wrap: anywhere; line-height: 1.7; }
.review-comment { margin-top: 16px; }
</style>
