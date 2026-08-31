<template>
  <div class="project-detail-page">
    <el-card class="box-card" shadow="never">
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <el-button link @click="goBack">← 返回</el-button>
            <span class="page-title">项目详情</span>
          </div>
          <div class="header-actions">
            <el-button v-if="canManage" type="success" plain @click="handleAddWorkPackage">新增工作包</el-button>
            <el-button type="primary" @click="refreshAll"><i class="el-icon-refresh"></i> 刷新</el-button>
          </div>
        </div>
      </template>

      <!-- 项目信息卡 -->
      <el-descriptions v-if="projectInfo" :column="4" border class="project-info">
        <el-descriptions-item label="项目编号">{{ projectInfo.code }}</el-descriptions-item>
        <el-descriptions-item label="项目名称">{{ projectInfo.name }}</el-descriptions-item>
        <el-descriptions-item label="项目负责人">{{ projectInfo.owner_name }}</el-descriptions-item>
        <el-descriptions-item label="机型主管/责任人">{{ projectInfo.tech_owner_name || '-'}}</el-descriptions-item>
        <el-descriptions-item label="项目级别">
          <el-tag v-if="projectInfo.level" :type="projectInfo.level === 'A' ? 'danger' : (projectInfo.level === 'B' ? 'warning' : 'primary')" size="small">
            {{ projectInfo.level }} 级
          </el-tag>
          <span v-else>-</span>
        </el-descriptions-item>
        <el-descriptions-item label="项目类别">{{ projectInfo.category || '-' }}</el-descriptions-item>
        <el-descriptions-item label="工作包数">{{ projectInfo.work_package_count }}（已完成 {{ projectInfo.done_count }}）</el-descriptions-item>
        <el-descriptions-item label="项目进度">
          <el-progress :percentage="projectInfo.project_progress || 0" :stroke-width="10" style="width: 140px" />
        </el-descriptions-item>
        <el-descriptions-item label="完成状态">
          <el-tag v-if="projectInfo.complete_status" type="success">已完成</el-tag>
          <el-tag v-else type="info" effect="plain">进行中</el-tag>
        </el-descriptions-item>
      </el-descriptions>

      <!-- 工作包表格 -->
      <el-table
        :data="workPackages"
        v-loading="loading"
        border
        stripe
        row-key="id"
        style="width: 100%"
        height="calc(100vh - 360px)"
        empty-text="该项目下暂无工作包"
        :row-class-name="rowClassName"
        :header-cell-style="{ background: '#f8fafc', color: '#334155', fontWeight: 'bold' }"
      >
        <el-table-column type="expand">
          <template #default="{ row: pkg }">
            <div class="nested-table-container">
              <WorkItemTable :workPackageId="pkg.id" :refresh-key="refreshKey" @changed="refreshAll" />
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="code" label="工作包编号" width="120" align="center">
          <template #default="{ row: pkg }">
            <el-input v-if="pkg.isEdit" v-model="pkg.code" size="small"/>
            <span v-else class="code-text">{{ pkg.code }}</span>
          </template>
        </el-table-column>

        <el-table-column prop="category_name" label="类别" width="100" align="center">
          <template #default="{ row: pkg }">
            <el-select v-if="pkg.isEdit" v-model="pkg.category_name" size="small">
              <el-option v-for="cat in categoryOptions" :key="cat" :label="cat" :value="cat" />
            </el-select>
            <el-tag v-else size="small" type="info">{{ pkg.category_name }}</el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="objective" label="目标" min-width="160">
          <template #default="{ row: pkg }">
            <el-input v-if="pkg.isEdit" type="textarea" autosize v-model="pkg.objective" size="small" placeholder="设定工作目标" />
            <span v-else-if="!pkg.objective" class="muted-text">暂无设定</span>
            <span v-else>{{ pkg.objective }}</span>
          </template>
        </el-table-column>

        <el-table-column prop="notes" label="备注" min-width="160">
          <template #default="{ row: pkg }">
            <el-input v-if="pkg.isEdit" type="textarea" autosize v-model="pkg.notes" size="small" placeholder="填写备注" />
            <span v-else-if="!pkg.notes" class="muted-text">暂无设定</span>
            <span v-else>{{ pkg.notes }}</span>
          </template>
        </el-table-column>
        
        <el-table-column label="责任人" width="100">
          <template #default="{ row: pkg }">
            <el-select v-if="pkg.isEdit" v-model="pkg.owner_id" clearable filterable placeholder="选择责任人" size="small" style="width: 100%">
              <el-option v-for="u in userOptions" :key="u.id" :label="`${u.username}（${u.id}）`" :value="u.id" />
            </el-select>
            <span v-else-if="pkg.package_owner_name || pkg.package_owner_id" class="employee-text">
              {{ pkg.package_owner_name }}
            </span>
            <span v-else class="tip-text">暂未指定</span>
          </template>
        </el-table-column>

        <el-table-column label="技术负责人" width="100">
          <template #default="{ row: pkg }">
            <el-select v-if="pkg.isEdit" v-model="pkg.tech_owner_id" clearable filterable placeholder="选择技术负责人" size="small" style="width: 100%">
              <el-option v-for="u in userOptions" :key="u.id" :label="`${u.username}（${u.id}）`" :value="u.id" />
            </el-select>
            <span v-else-if="pkg.package_tech_owner_name || pkg.package_tech_owner_id" class="employee-text">
              {{ pkg.package_tech_owner_name }}
            </span>
            <span v-else class="tip-text">暂未指定</span>
          </template>
        </el-table-column>

        <el-table-column label="进度" width="150" align="center">
          <template #default="{ row: pkg }">
            <el-progress :percentage="pkg.package_progress || 0" :stroke-width="10" />
          </template>
        </el-table-column>

        <el-table-column v-if="canManage" label="操作" width="180" align="center" fixed="right">
          <template #default="{ row: pkg, $index }">
            <template v-if="pkg.isEdit">
              <el-button type="success" link size="small" :loading="saving" @click="handleSaveWorkPackage(pkg)">保存</el-button>
              <el-button type="info" link size="small" @click="cancelWpEdit(pkg, $index)">取消</el-button>
            </template>
            <template v-else>
              <el-button type="primary" link size="small" @click="removeWorkPackage(pkg)">删除</el-button>
              <el-button type="primary" link size="small" @click="pkg.isEdit = true">编辑</el-button>
              <!-- <el-button type="warning" link size="small" @click="handleTransferWorkPackage(pkg)">转办</el-button> -->
              <el-button v-if="canConfirmPkg(pkg)" type="success" link size="small" :loading="confirming" @click="confirmPkg(pkg)">
                {{ pkg.complete_status ? '取消完成' : '确认完成' }}
              </el-button>
            </template>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-bar">
        <el-pagination
          background
          layout="total, prev, pager, next, sizes"
          :total="total"
          :current-page="page"
          :page-size="pageSize"
          :page-sizes="[10, 20, 50]"
          @current-change="(p) => fetchWorkPackages(p)"
          @size-change="(s) => { pageSize = s; fetchWorkPackages(1) }"
        />
      </div>

    </el-card>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  getProjectDetailApi,
  getPagedProjectWorkPackagesApi,
  getAllUsersApi,
  createWorkPackageApi,
  deleteWorkPackageApi,
  initiateTransferApi,
  confirmCompletionApi,
  getWorkCategoriesApi
} from '../api'
import WorkItemTable from '../components/WorkItemTable.vue'
import { useUserStore } from '../stores/user'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const projectId = Number(route.params.id)

const projectInfo = ref(null)
const workPackages = ref([])
const loading = ref(false)
const refreshKey = ref(0) // 传给工作项表格：点「刷新」时强制拉取最新数据
const saving = ref(false)
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const userOptions = ref([])
const categoryOptions = ref([])   // 工作包类别：从数据库 work_project_categories 加载

const isAdmin = computed(() => userStore.isAdmin)
const isLeader = computed(() => userStore.isLEADER)
const isDepartment = computed(() => userStore.isDEPARTMENT)
const currentUserId = computed(() => String(userStore.userInfo?.id || ''))

// 管理权限：管理员 / 领导 / 科室主任 / 项目负责人
const canManage = computed(() => {
  if (isAdmin.value || isLeader.value || isDepartment.value) return true
  return String(projectInfo.value?.owner_id || '') === currentUserId.value
})

// 已完成行灰显
const rowClassName = ({ row }) => (row.complete_status ? 'completed-row' : '')

// —— 确认完成（工作包/项目，负责人或领导/管理员）——
const confirming = ref(false)
const canConfirmPkg = (pkg) => {
  if (isAdmin.value || isLeader.value || isDepartment.value) return true
  return String(pkg.package_owner_id || '') === currentUserId.value
}
const doConfirm = async (target_type, target_id, confirmed) => {
  confirming.value = true
  try {
    const res = await confirmCompletionApi({
      target_type,
      target_id: String(target_id),
      user_id: currentUserId.value,
      confirmed
    })
    if (res.data?.code === 200) {
      ElMessage.success(confirmed ? '已确认完成' : '已取消完成')
      await fetchWorkPackages(page.value)
      await fetchProjectInfo()
    }
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '操作失败')
  } finally {
    confirming.value = false
  }
}
const confirmPkg = (pkg) => doConfirm('work_package', pkg.id, !pkg.complete_status)
const confirmProject = () => doConfirm('project', projectId, !projectInfo.value?.complete_status)

const goBack = () => router.push('/project-overview')

const fetchProjectInfo = async () => {
  try {
    const res = await getProjectDetailApi(projectId)
    if (res.data?.code === 200) projectInfo.value = res.data.data
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '获取项目信息失败')
  }
}

const fetchWorkPackages = async (p = 1) => {
  page.value = p
  loading.value = true
  try {
    const res = await getPagedProjectWorkPackagesApi(projectId, { page: p, page_size: pageSize.value })
    if (res.data?.code === 200) {
      const data = res.data.data || {}
      total.value = data.total || 0
      workPackages.value = (data.items || []).map(wp => ({
        ...wp,
        id: wp.id,
        code: wp.code,
        owner_id: wp.package_owner_id || '',
        tech_owner_id: wp.package_tech_owner_id || '',
        isEdit: false,
        isNew: false,
        _original: null
      }))
      workPackages.value.forEach(w => { w._original = JSON.parse(JSON.stringify(w)) })
    }
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '获取工作包失败')
  } finally {
    loading.value = false
  }
}

//删除工作包
const removeWorkPackage = async (row) => {
  try {
    //弹出确认框
    await ElMessageBox.confirm(
      '确定要删除该工作包吗？此操作会一并删除改工作包下所有工作项以及拆包请求，且无法撤销。',
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    // 用户点击确定后，执行原有的删除逻辑
    const res = await deleteWorkPackageApi(row.id, currentUserId.value)
    
    if (res.data?.code === 200) {
      ElMessage.success('工作包已删除')
      await fetchWorkPackages(page.value)
      await fetchProjectInfo()
    }
  } catch (err) {
    //  区分是用户取消了弹窗，还是接口报错
    if (err === 'cancel') {
      ElMessage.info('已取消删除')
    } else {
      ElMessage.error(err.response?.data?.detail || '删除失败')
    }
  }
}

// 新增工作包（表格顶部插入一条编辑行）
const handleAddWorkPackage = () => {
  workPackages.value.unshift({
    work_package_code:"",
    project_id: projectId,
    category_name: categoryOptions.value[0] || '',
    objective: '',
    owner_id: '',
    tech_owner_id:'',
    notes:'',
    isEdit: true,
    isNew: true,
    _original: null
  })
}

const handleSaveWorkPackage = async (pkg) => {
  if (!(pkg.code || '').trim()) {
    ElMessage.error('保存失败，工作包编号不能为空')
    return          // 直接不发请求
  }
  saving.value = true
  try {
    const res = await createWorkPackageApi({
      id: pkg.id,
      work_package_code: pkg.code,
      project_id: projectId,
      project_name: projectInfo.value?.name,
      category_name: pkg.category_name,
      objective: pkg.objective ? pkg.objective.trim() : '',
      owner_id: pkg.owner_id || null,
      tech_owner_id: pkg.tech_owner_id || null,
      notes: pkg.notes ? pkg.notes.trim() : ''
    })
    if (res.data?.code === 200) {
      ElMessage.success('工作包保存成功')
      pkg.isEdit = false
      pkg.isNew = false
      await fetchWorkPackages(page.value)
      await fetchProjectInfo()
    }
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '工作包保存失败')
  } finally {
    saving.value = false
  }
}

const cancelWpEdit = (pkg, index) => {
  if (pkg.isNew) {
    workPackages.value.splice(index, 1)
  } else {
    if (pkg._original) Object.assign(pkg, JSON.parse(JSON.stringify(pkg._original)))
    pkg.isEdit = false
  }
}

const refreshAll = () => {
  refreshKey.value++ // 通知已展开的工作项表格强制拉取最新数据
  fetchProjectInfo()
  fetchWorkPackages(page.value)
}

onMounted(async () => {
  await fetchProjectInfo()
  await fetchWorkPackages(1)
  // 工作包类别下拉跟随数据库
  try {
    const res = await getWorkCategoriesApi()
    if (res.data?.code === 200) categoryOptions.value = res.data.data || []
  } catch {
    /* 类别加载失败不影响主流程 */
  }
  if (isAdmin.value || isLeader.value) {
    try {
      const res = await getAllUsersApi()
      userOptions.value = res.data?.data || []
    } catch {
      /* 用户选项加载失败不影响主流程 */
    }
  }
})
</script>

<style scoped>
.project-detail-page {
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
  padding: 4px 0;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.page-title {
  font-weight: bold;
  color: #334155;
  font-size: 15px;
}

.header-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

.project-info {
  margin-bottom: 16px;
}

.code-text {
  font-family: monospace;
  font-weight: bold;
  color: #64748b;
  background: #f1f5f9;
  padding: 2px 6px;
  border-radius: 4px;
}

.employee-text {
  color: #0f766e;
  font-weight: 500;
}

.tip-text, .muted-text {
  color: #94a3b8;
  font-size: 13px;
}

.nested-table-container {
  padding: 20px;
  background-color: #f8fafc;
  border-radius: 8px;
  margin: 10px 20px;
  box-shadow: inset 0 2px 4px 0 rgba(0, 0, 0, 0.02);
}

.pagination-bar {
  display: flex;
  justify-content: flex-end;
  padding-top: 12px;
}

:deep(.el-table) { flex: none !important; }

:deep(.el-table__expanded-cell) {
  padding: 0 !important;
  background-color: #fbfbfc !important;
}

:deep(.completed-row) {
  background: #f3f4f6 !important;
  color: #9ca3af;
}

:deep(.completed-row td) {
  background: #f3f4f6 !important;
}
</style>
