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
            <el-button v-if="canRequestPackageChange" type="success" plain :disabled="projectInfo?.closed_status" @click="handleAddWorkPackage">申请新增工作包</el-button>
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
        <el-descriptions-item label="关闭状态">
          <el-tag v-if="projectInfo.closed_status" type="danger">已关闭</el-tag>
          <el-tag v-else type="info" effect="plain">开启</el-tag>
        </el-descriptions-item>
      </el-descriptions>

      <!-- 工作包表格 -->
      <el-table
        :data="workPackages"
        v-loading="loading"
        row-key="id"
        style="width: 100%"
        height="calc(100vh - 360px)"
        empty-text="该项目下暂无工作包"
        :row-class-name="rowClassName"
      >
        <el-table-column type="expand">
          <template #default="{ row: pkg }">
            <div class="nested-table-container">
              <WorkItemTable_improved :workPackageId="pkg.id" :refresh-key="refreshKey" @changed="refreshAll" />
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="code" label="工作包编号" width="120" align="center">
          <template #default="{ row: pkg }">
            <el-input v-if="pkg.isEdit" v-model="pkg.code" size="small"/>
            <span v-else>{{ pkg.code }}</span>
          </template>
        </el-table-column>

        <el-table-column prop="category_name" label="类别" width="100" align="center">
          <template #default="{ row: pkg }">
            <el-select v-if="pkg.isEdit" v-model="pkg.category_name" size="small">
              <el-option v-for="cat in categoryOptions" :key="cat" :label="cat" :value="cat" />
            </el-select>
            <span v-else size="small" type="info">{{ pkg.category_name }}</span>
          </template>
        </el-table-column>

        <el-table-column prop="name" label="名称" min-width="160">
          <template #default="{ row: pkg }">
            <el-input v-if="pkg.isEdit" type="textarea" autosize v-model="pkg.name" size="small" placeholder="填写名称" />
            <span v-else-if="!pkg.name" class="muted-text">暂无设定</span>
            <span v-else>{{ pkg.name }}</span>
            <el-tag v-if="pkg.closed_status || pkg.project_closed" size="small" type="danger" effect="plain" style="margin-left: 6px">已关闭</el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="objective" label="目标" min-width="160">
          <template #default="{ row: pkg }">
            <el-input v-if="pkg.isEdit" type="textarea" autosize v-model="pkg.objective" size="small" placeholder="设定工作目标" />
            <span v-else-if="!pkg.objective" class="muted-text">暂无设定</span>
            <span v-else>{{ pkg.objective }}</span>
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

        <el-table-column prop="decomposition_status" label="分解状态" width="110" align="center">
          <template #default="{ row }">
            <span v-if="row.isNew">—</span>
            <el-tag v-else :type="row.is_decomposed ? 'success' : 'info'" effect="light">
              {{ row.decomposition_status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="进度" width="150" align="center">
          <template #default="{ row }">
          <div class="progress-wrapper">
            <span class="progress-text">{{ row.progress || 0 }}%</span>
            <el-progress 
              type="circle" 
              :percentage="row.progress || 0" 
              :width="20" 
              :stroke-width="4"
              :show-text="false"
            />
          </div>
        </template>
        </el-table-column>

        <el-table-column label="状态" min-width="100" align="center" fixed="right">
          <template #default="{ row: pkg }">
            <div class="status-cell">
            <div class="status-dot-wrapper">
              <span class="status-dot" :style="{ backgroundColor: getStatusConfig(pkg).color }" ></span>
              <span class="status-text" :style="{ color: getStatusConfig(pkg).color }">{{ getStatusConfig(pkg).label }}</span>
            </div>
          </div>
          </template>
        </el-table-column>

        <el-table-column v-if="canManage" label="操作" min-width="140" align="center" fixed="right">
          <template #default="{ row: pkg, $index }">
            <template v-if="pkg.isEdit">
              <el-button type="success" link size="small" :loading="saving" @click="handleSaveWorkPackage(pkg)">{{ pkg.isNew ? '提交申请' : '确认修改' }}</el-button>
              <el-button type="info" link size="small" :disabled="saving" @click="cancelWpEdit(pkg, $index)">取消</el-button>
            </template>
            <template v-else>
              <el-button v-if="canRequestPackageChange && !pkg.closed_status && !projectInfo?.closed_status" type="primary" link size="small" @click="startPackageEdit(pkg)">申请修改</el-button>
            </template>
            <el-dropdown trigger="click" @command="(command) => handleMoreCommand(command, pkg)">
              <el-button type="info" link size="small">更多
                <el-icon class="el-icon--right"><ArrowDown /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item
                    v-if="canRequestPackageChange && !pkg.closed_status && !projectInfo?.closed_status" command="delete" divided >
                    <span class="danger-menu-item">申请删除</span>
                  </el-dropdown-item>

                  <!-- 完成/取消完成：按手动原始状态 -->
                  <el-dropdown-item
                    v-if="canConfirmPkg(pkg) && !pkg.closed_status && !projectInfo.closed_status && !pkg.manual_complete_status" command="confirmComplete" divided> 确认完成
                  </el-dropdown-item>

                  <el-dropdown-item
                    v-if="canConfirmPkg(pkg) && !pkg.closed_status && !projectInfo.closed_status && pkg.manual_complete_status" command="cancelComplete" >取消完成
                  </el-dropdown-item>

                  <!-- 确认关闭 -->
                  <el-dropdown-item
                    v-if="canConfirmClosed(pkg) && !pkg.closed_status" command="confirmClosed" divided >
                    <span class="danger-menu-item">确认关闭</span>
                  </el-dropdown-item>

                  <!-- 取消关闭 -->
                  <el-dropdown-item
                    v-if=" pkg.closed_status && isAdmin " command="cancelClosed" > 取消关闭
                  </el-dropdown-item>

                </el-dropdown-menu>
              </template>
            </el-dropdown>
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
  confirmCompletionApi,
  confirmClosedApi,
  getWorkCategoriesApi
} from '../../api'
import WorkItemTable_improved from '../../components/WorkItemTable_improved.vue'
import { useUserStore } from '../../stores/user'
import { confirmClose, confirmCancelClose } from '../../components/confirm'
import { ArrowDown, Loading, CircleCheck, CircleClose, Lock } from '@element-plus/icons-vue'

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
const canRequestPackageChange = computed(() => isAdmin.value || isDepartment.value)
const canManage = computed(() => {
  if (isAdmin.value || isLeader.value || isDepartment.value) return true
  return String(projectInfo.value?.owner_id || '') === currentUserId.value
})

// 工作包/所属项目是否已整体关闭（禁止其下所有工作项的编辑/填分）
const projClosed = computed(() => !!projectInfo.value?.closed_status)
const isLocked = (row) => projClosed.value || !!row.closed_status
// 已完成/已关闭行灰显
const rowClassName = ({ row }) => (row.complete_status || row.closed_status ? 'completed-row' : '')

const statusConfig = {
  '进行中': {
    icon: Loading,
    color: '#409EFF',
    tagType: 'primary',
    label: '进行中'
  },
  '已完成': {
    icon: CircleCheck,
    color: '#67C23A',
    tagType: 'success',
    label: '已完成'
  },
  '已关闭': {
    icon: CircleClose,
    color: '#F56C6C',
    tagType: 'danger',
    label: '已关闭'
  },
  '所属已关闭': {
    icon: Lock,
    color: '#909399',
    tagType: 'info',
    label: '所属已关闭'
  }
}
// ============ 获取状态配置 ============
const getStatusConfig = (row) => {
  if (row.closed_status) return statusConfig['已关闭']
  if (isLocked(row)) return statusConfig['所属已关闭']
  if (row.complete_status) return statusConfig['已完成']
  return statusConfig['进行中']
}

const handleMoreCommand = async (command, row) => {
  switch (command) {
    case 'delete':
      try {
        await ElMessageBox.confirm(
          '确定申请删除该工作包？提交原因后，由领导审核通过才会删除。',
          '工作包删除申请',
          {
            confirmButtonText: '继续填写原因',
            cancelButtonText: '取消',
            type: 'warning'
          }
        )
        await removeWorkPackage(row)
      } catch (err) {
        // 用户点击取消时不提示
        if (err !== 'cancel' && err !== 'close') {
          console.error(err)
        }
      }
      break
    case 'confirmComplete':
      await confirmPkg(row)
      break

    case 'cancelComplete':
      await confirmPkg(row)
      break

    case 'confirmClosed':
      await handleClosedConfirm(row)
      break

    case 'cancelClosed':
      await handleCancelClosedConfirm(row)
      break
  }
}

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
const confirmPkg = (pkg) => doConfirm('work_package', pkg.id, !pkg.manual_complete_status)
const confirmProject = () => doConfirm('project', projectId, !projectInfo.value?.manual_complete_status)

const handleClosedConfirm = (row) => {
  confirmClose('工作包', () => {
    confirmClosed(row)
  })
}

const handleCancelClosedConfirm = (row) => {
  confirmCancelClose('工作包', () => { confirmClosed(row) })
}


// —— 确认/取消关闭（只有领导/管理员，后端会校验）——
const canConfirmClosed = () => isAdmin.value || isLeader.value
const confirmClosed = async (pkg) => {
  confirming.value = true
  try {
    const res = await confirmClosedApi({
      target_type: 'work_package',
      target_id: pkg.id,
      user_id: currentUserId.value,
      confirmed: !pkg.closed_status
    })
    if (res.data?.code === 200) {
      ElMessage.success(pkg.closed_status ? '已取消关闭' : '已确认关闭')
      await fetchWorkPackages(page.value)
      await fetchProjectInfo()
    }
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '操作失败')
  } finally {
    confirming.value = false
  }
}

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
        name: wp.name || '-',
        progress: wp.package_progress || 0,
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

// 三类申请统一收集原因；取消弹窗不会提交，纯空白不允许通过。
const askPackageReason = (title, message = '请填写本次工作包变更的申请原因') =>
  ElMessageBox.prompt(message, title, {
    draggable: true,
    inputType: 'textarea',
    inputPlaceholder: '请输入原因（最多2000字）',
    confirmButtonText: '提交申请',
    cancelButtonText: '取消',
    inputValidator: value => {
      const reason = (value || '').trim()
      return reason.length > 0 && reason.length <= 2000 || '原因不能为空且不能超过2000字'
    },
  })

// 删除只提交申请，原因与申请一同保存，领导审核后才生效。
const removeWorkPackage = async (row) => {
  if (saving.value) return
  saving.value = true
  try {
    const { value } = await askPackageReason('申请删除工作包', '请填写删除原因。领导通过后才会删除；有工作项或历史记录时请使用关闭功能。')
    const res = await deleteWorkPackageApi(row.id, value.trim())
    if (res.data?.code === 200) {
      ElMessage.success('删除申请已提交，等待领导审核')
      await fetchWorkPackages(page.value)
      await userStore.refreshPendingCount()
    }
  } catch (err) {
    if (err !== 'cancel' && err !== 'close') {
      ElMessage.error(err.response?.data?.detail || '删除申请提交失败')
    }
  } finally {
    saving.value = false
  }
}

// 新增工作包（表格顶部插入一条编辑行）
const handleAddWorkPackage = () => {
  if (projectInfo.value?.closed_status) return ElMessage.warning('项目已关闭，不能新增工作包')
  workPackages.value.unshift({
    work_package_code:"",
    project_id: projectId,
    category_name: categoryOptions.value[0] || '',
    objective: '',
    owner_id: '',
    tech_owner_id:'',
    name:'',
    isEdit: true,
    isNew: true,
    _original: null
  })
}

const startPackageEdit = (pkg) => {
  pkg._original = JSON.parse(JSON.stringify({ ...pkg, _original: null }))
  pkg.isEdit = true
}
const handleSaveWorkPackage = async (pkg) => {
  if (saving.value) return
  if (!(pkg.code || '').trim()) {
    ElMessage.error('保存失败，工作包编号不能为空')
    return          // 直接不发请求
  }
  saving.value = true
  try {
    const { value } = await askPackageReason(pkg.isNew ? '申请新增工作包' : '填写修改说明', pkg.isNew ? '请填写新增原因' : '请说明本次修改的内容和原因，提交后由领导审核')
    const res = await createWorkPackageApi({
      reason: value.trim(),
      id: pkg.id,
      work_package_code: pkg.code,
      project_id: projectId,
      project_name: projectInfo.value?.name,
      category_name: pkg.category_name,
      objective: pkg.objective ? pkg.objective.trim() : '',
      owner_id: pkg.owner_id || null,
      tech_owner_id: pkg.tech_owner_id || null,
      name: pkg.name ? pkg.name.trim() : ''
    })
    if (res.data?.code === 200) {
      ElMessage.success('申请已提交，等待领导审核')
      pkg.isEdit = false
      pkg.isNew = false
      await fetchWorkPackages(page.value)
      await fetchProjectInfo()
      await userStore.refreshPendingCount()
    }
  } catch (err) {
    if (err !== 'cancel' && err !== 'close') ElMessage.error(err.response?.data?.detail || '工作包申请提交失败')
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
  if (canManage.value) {
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

/* 进度圆环样式 */
.progress-wrapper {
  display:flex;
  align-items: center;
  justify-content: center;
  gap: 8px; /* 圆环和文字之间的间距 */
}

.progress-text {
  font-size: 13px;
  color: #606266;
  font-weight: 500;
}

/* ==========================================
   现代简约商务风 表格统一样式改造
========================================== */

/* 1. 表格全局变量替换：去线化、低饱和度 */
:deep(.el-table) {
  --el-table-border-color: #f1f5f9; /* 极浅的分割线 */
  --el-table-header-bg-color: #ffffff; /* 表头纯白，靠底边框区分 */
  --el-table-header-text-color: #64748b; /* 表头文字使用 slate-500 灰色，不抢戏 */
  --el-table-row-hover-bg-color: #f8fafc; /* 极其微妙的悬浮高亮 */
  --el-table-text-color: #334155; /* 正文深灰，比纯黑更柔和 */
  background-color: transparent;
}

/* 2. 表头优化：去掉竖线，加粗底线，增加呼吸感 */
:deep(.el-table__header th) {
  font-weight: 600;
  font-size: 13px;
  padding: 12px 0; /* 增加表头上下留白 */
  border-bottom: 2px solid #e2e8f0 !important; /* 加重表头底线，稳住视觉重心 */
}

/* 3. 单元格优化：增加行高，让数据不拥挤 */
:deep(.el-table__row td.el-table__cell) {
  padding: 14px 0; /* 增加正文单元格上下留白 */
  font-size: 14px;
}

/* 4. 隐藏固定列的阴影线（让左右固定列更无缝衔接） */
:deep(.el-table__fixed-right::before),
:deep(.el-table__fixed::before) {
  display: none;
}

/* 5. 展开行（子表格）容器美化 */
.nested-table-container {
  padding: 16px 24px;
  background-color: #f8fafc; /* 浅灰底色，与主表格纯白形成层级对比 */
  border-radius: 8px;
  margin: 8px 16px 16px 16px;
  border: 1px solid #e2e8f0; /* 给子表格外层加一个极细的边框包裹 */
  box-shadow: none;
}

/* 6. 卡片整体阴影弱化（更高级的悬浮感） */
.box-card {
  border: 1px solid #e2e8f0;
  box-shadow: 0 1px 3px 0 rgba(15, 23, 42, 0.05), 0 1px 2px -1px rgba(15, 23, 42, 0.05) !important;
}

/* 7. 优化“已完成”行的视觉呈现（更温和的灰显） */
:deep(.completed-row td) {
  background-color: #f9fafb !important;
  color: #94a3b8;
}
:deep(.completed-row .code-text) {
  background-color: #f1f5f9;
  color: #94a3b8;
  opacity: 0.7;
}

.danger-menu-item {
  color: var(--el-color-danger);
}

.el-dropdown {
  margin-left: 4px;
}

.status-cell {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.status-dot-wrapper {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
  display: inline-block;
}

.status-text {
  font-size: 13px;
  font-weight: 500;
}

.project-detail-page :deep(.status-text) {
  color: #334155 !important;  /* 统一改为深灰色 */
  font-weight: 500;
}
</style>
