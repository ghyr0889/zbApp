<template>
  <div class="project-overview">
    <el-card class="box-card" shadow="never">
      <template #header>
        <div class="card-header">
          <div class="header-actions">
            <el-input
              v-model="searchKeyword"
              placeholder="可按照项目名称、编号以及机型主管进行搜索..."
              clearable
              class="search-input"
            >
              <template #prefix>
                <i class="el-icon-search"></i>
              </template>
            </el-input>
            <!-- 只保留新增项目在顶部，新增工作包移至每一行内 -->
            <el-button v-if="activeTab === 'all' && canAddProject" type="success" plain @click="handleAddProject">
              <i class="el-icon-folder-add"></i> 新增项目
            </el-button>
            <el-button type="primary" plain size="default" @click="refreshAll">
              <i class="el-icon-refresh"></i> 刷新
            </el-button>
          </div>
        </div>
      </template>

      <el-tabs v-model="activeTab">
        <el-tab-pane label="我的工作" name="mine">
          <!-- 外层主表格，展示工作包 -->
          <el-table
            v-if="activeTab === 'mine'"
            :data="myWorkPackages"
            border
            style="width: 100%"
            height="calc(100vh - 280px)"
            empty-text="您暂未负责任何工作包"
            row-key="id"
            :row-class-name="tableRowClassName"
            :header-cell-style="{background: '#ffffff', color: '#64748b', fontWeight: '600'}"
          >
            <!-- 展开列：展示该工作包下的工作项（可编辑/删除/填分值） -->
            <el-table-column type="expand">
              <template #default="{ row: pkg }">
                <div class="nested-table-container">
                  <WorkItemTable_improved :workPackageId="pkg.id" :refresh-key="refreshKey" @changed="refreshAll" />
                </div>
              </template>
            </el-table-column>            
            <el-table-column prop="id" label="工作包编号" min-width="120" align="center">
              <template #default="{ row: pkg }">
                <span>{{ pkg.code }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="category_name" label="工作包类别" min-width="120" align="center">
              <template #default="{ row: pkg }">
                <span v-if="pkg.category_name" size="small" type="info">{{ pkg.category_name }}</span>
                <span v-else class="tip-text">-</span>
              </template>
            </el-table-column>
            <el-table-column prop="objective" label="目标" min-width="120" align="center">
              <template #default="{ row: pkg }">
                <span v-if="pkg.objective">{{ pkg.objective }}</span>
                <span v-else class="tip-text">-</span>
              </template>
            </el-table-column>
            <el-table-column prop="name" label="名称" min-width="150" align="center">
              <template #default="{ row: pkg }">
                <span v-if="pkg.name">{{ pkg.name }}</span>
                <span v-else class="tip-text">-</span>
              </template>
            </el-table-column>
            <el-table-column prop="project_code" label="所属项目编号" min-width="110" show-overflow-tooltip />
            <el-table-column prop="package_owner_name" label="工作包负责人" min-width="110" align="center"/>
              
            <el-table-column prop="package_tech_owner_name" label="工作包技术负责人" min-width="130" align="center" >
              <template #default="{ row: pkg }">
                <span>{{ pkg.package_tech_owner_name || '-' }}</span>
              </template>
            </el-table-column>
            <el-table-column label="工作包进度" min-width="130" align="center" fixed="right">
              <template #default="{ row }">
                <div class="progress-wrapper">
                  <span class="progress-text">{{ row.package_progress || 0 }}%</span>
                  <el-progress 
                    type="circle" 
                    :percentage="row.package_progress || 0" 
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

            <el-table-column label="操作" min-width="150" align="center" fixed="right">
              <template #default="{ row: pkg }">
                <!-- 转办：按生效状态（已自动完成/手动完成均不可转办） -->
                <el-button v-if="isPkgOwner(pkg) && !pkg.complete_status && !pkg.closed_status && !pkg.project_closed" 
                type="warning" link size="small" @click="handleTransferWorkPackage(pkg)">转办
                </el-button>
                <!-- 完成/取消完成：按手动原始状态 -->
                <el-button v-if="canConfirmPkg(pkg) && !pkg.closed_status && !pkg.project_closed" type="success" link size="small" :loading="confirming" @click="confirmPkg(pkg)">
                  {{ pkg.manual_complete_status ? '取消完成' : '完成' }}
                </el-button>
              </template>
            </el-table-column>
          </el-table>
          <div class="pagination-bar">
            <el-pagination
              background
              layout="total, prev, pager, next"
              :total="myTotal"
              :current-page="myPage"
              :page-size="myPageSize"
              @current-change="fetchMyWorkPackages"
            />
          </div>
        </el-tab-pane>

      
        <el-tab-pane label="所有项目" name="all">
          <!-- 外层主表格：显示项目信息 -->
          <el-table
            v-if="activeTab === 'all'"
            ref="projectTableRef"
            :data="tableData"
            border
            style="width: 100%"
            v-loading="loadingAllWorkPackages"
            height="calc(100vh - 310px)"
            empty-text="暂无项目数据"
            row-key="project_id"
            :row-class-name="tableRowClassName"
            :header-cell-style="{ background: '#ffffff', color: '#64748b', fontWeight: '600' }"
            @row-dblclick="openProjectDetail"
          >

            <!-- 主表格列配置 -->
            <el-table-column label="序号" min-width="70" align="center">
              <template #default="{ row, $index }">
                <!-- 如果是刚点击“新增”尚未保存的行，显示 * 号 -->
                <span v-if="row.isNew" style="color: #f56c6c; font-weight: bold;">*</span>
                <!-- 已保存的正常数据，按公式：(当前页码 - 1) * 每页条数 + 当前行索引 + 1 -->
                <span v-else>
                  {{ (pagedPage - 1) * pagedPageSize + $index + (tableData[0]?.isNew ? 0 : 1) }}
                </span>
              </template>
            </el-table-column>

            <el-table-column prop="project_code" label="项目编号" min-width="100">
              <template #default="{ row }">
                <el-input v-if="row.isEdit" v-model="row.project_code" size="small" placeholder="请输入项目编号" />
                <span v-else>{{ row.project_code }}</span>
              </template>
            </el-table-column>

            <el-table-column prop="project_name" label="项目名称" min-width="140">
              <template #default="{ row }">
                <el-input v-if="row.isEdit" v-model="row.project_name" size="small" placeholder="请输入项目名称" />
                <span v-else>{{ row.project_name }}</span>
              </template>
            </el-table-column>

            <el-table-column prop="category" label="项目类别" min-width="100" align="center">
              <template #default="{ row }">
                <el-input v-if="row.isEdit" v-model="row.category" size="small" placeholder="请输入项目类别" />
                <template v-else>
                  <span v-if="row.category" type="info" effect="plain">{{ row.category }}</span>
                  <span v-else class="tip-text">-</span>
                </template>
              </template>
            </el-table-column>
            
            <el-table-column label="项目级别" min-width="100" align="center">
              <template #default="{ row }">
                <el-select v-if="row.isEdit" v-model="row.level" size="small">
                  <el-option label="A 级" value="A" />
                  <el-option label="B 级" value="B" />
                  <el-option label="C 级" value="C" />
                  <el-option label="D 级" value="D" />
                </el-select>
                <template v-else>
                  <el-tag v-if="row.level" :type="row.level === 'A' ? 'danger' : (row.level === 'B' ? 'warning' : 'primary')" effect="light" round>
                    {{ row.level }} 级
                  </el-tag>
                  <span v-else class="tip-text">-</span>
                </template>
              </template>
            </el-table-column>

            <el-table-column label="项目负责人" min-width="120">
              <template #default="{ row }">
                <el-select v-if="row.isEdit" v-model="row.owner_id" clearable filterable placeholder="选择负责人" size="small" style="width: 100%">
                  <el-option v-for="user in userOptions" :key="user.id" :label="`${user.username}（${user.id}）`" :value="user.id" />
                </el-select>
                <template v-else>
                  <span v-if="row.owner_name || row.owner_id">
                    {{ row.owner_name ? `${row.owner_name}` : row.owner_id }}
                  </span>
                  <span v-else class="tip-text">暂未指定</span>
                </template>
              </template>
            </el-table-column>

            <el-table-column label="机型主管/责任人" min-width="130">
              <template #default="{ row }">
                <el-select v-if="row.isEdit" v-model="row.tech_owner_id" clearable filterable placeholder="选择负责人" size="small" style="width: 100%">
                  <el-option v-for="user in userOptions" :key="user.id" :label="`${user.username}（${user.id}）`" :value="user.id" />
                </el-select>
                <template v-else>
                  <span v-if="row.tech_owner_id || row.tech_owner_name">
                    {{ row.tech_owner_name ? `${row.tech_owner_name}` : row.tech_owner_id }}
                  </span>
                  <span v-else class="tip-text">暂未指定</span>
                </template>
              </template>
            </el-table-column>

            <el-table-column label="进度" min-width="100" align="center" fixed="right">
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
              <template #default="{ row }">
                <div class="status-cell">
                  <div class="status-dot-wrapper">
                    <span class="status-dot" :style="{ backgroundColor: getStatusConfig(row).color }" ></span>
                    <span class="status-text" :style="{ color: getStatusConfig(row).color }">{{ getStatusConfig(row).label }}</span>
                  </div>
                </div>
              </template>
            </el-table-column>

            <el-table-column v-if="canManageProject" label="操作" min-width="200" align="center" fixed="right">
              <template #default="{ row, $index }">
                <template v-if="canManageProject(row)">
                  <template v-if="row.isEdit">
                    <el-button type="success" link size="small" @click="handleSaveProject(row)">保存</el-button>
                    <el-button type="info" link size="small" @click="cancelProjectEdit(row, $index)">取消</el-button>
                  </template>
                  <template v-else>
                    <el-button type="primary" link size="small" :disabled="row.closed_status" @click="row.isEdit = true">编辑</el-button>
                  </template>
                   <el-dropdown trigger="click" :disabled="!hasMoreOptions(row)" @command="(command) => handleMoreCommand(command, row)">
                    <el-button type="info" link size="small">更多
                      <el-icon class="el-icon--right"><ArrowDown /></el-icon>
                    </el-button>
                    <template #dropdown>
                      <el-dropdown-menu>
                        <!-- 删除：仅未完成且未关闭（合成口径：进度达成也不可删） -->
                        <el-dropdown-item
                          v-if="!row.complete_status && !row.closed_status" command="delete" divided >
                          <span class="danger-menu-item">删除</span>
                        </el-dropdown-item>

                        <!-- 完成 / 取消完成：按手动原始状态互斥 -->
                        <el-dropdown-item
                          v-if="!row.manual_complete_status && !row.closed_status" command="confirmComplete" divided> 确认完成
                        </el-dropdown-item>

                        <el-dropdown-item
                          v-if="row.manual_complete_status && !row.closed_status" command="cancelComplete" >取消完成
                        </el-dropdown-item>

                        <!-- 确认关闭：仅未关闭，领导/管理员 -->
                        <el-dropdown-item
                          v-if="canClosed && !row.closed_status" command="confirmClosed" divided >
                          <span class="danger-menu-item">确认关闭</span>
                        </el-dropdown-item>

                        <!-- 取消关闭：仅已关闭且管理员 -->
                        <el-dropdown-item
                          v-if="row.closed_status && isAdmin" command="cancelClosed" > 取消关闭
                        </el-dropdown-item>

                      </el-dropdown-menu>
                    </template>
                  </el-dropdown>
                </template>
              </template>
            </el-table-column>
          </el-table>
          <div class="pagination-bar">
            <el-pagination
              background
              layout="total, prev, pager, next, sizes"
              :total="pagedTotal"
              :current-page="pagedPage"
              :page-size="pagedPageSize"
              :page-sizes="[10, 20, 50]"
              @current-change="fetchProjects"
              @size-change="(s) => { pagedPageSize = s; fetchProjects(1) }"
            />
          </div>
        </el-tab-pane>
      </el-tabs>

      <el-dialog v-model="transferDialogVisible" title="发起工作转办" width="460px" draggable>
        <el-form label-width="70px">
          <el-form-item label="工作包">
            <el-tag>{{ transferPkg?.code }}</el-tag>
            <span style="margin-left:8px">{{ transferPkg?.project_name }}</span>
          </el-form-item>
          <el-form-item label="接收人" required>
            <el-select v-model="transferTargetId" filterable placeholder="选择接收人" style="width:100%">
              <el-option v-for="u in transferTargets" :key="u.id"
                :label="`${u.username}（${u.id}）`" :value="u.id" />
            </el-select>
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="transferDialogVisible = false">取消</el-button>
          <el-button type="warning" :loading="transferring" @click="confirmTransfer">发送转办</el-button>
        </template>
      </el-dialog>
    </el-card>

  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  createProjectApi,
  deleteProjectApi,
  getAllProjectsApi,
  getAllUsersApi,
  getPagedProjectsApi,
  getMyWorkPackagesPagedApi,
  initiateTransferApi,
  confirmCompletionApi,
  confirmClosedApi
} from '../../api'
import { useUserStore } from '../../stores/user'
import { useRouter } from 'vue-router'
import { confirmClose, confirmCancelClose } from '../../components/confirm'
import WorkItemTable_improved from '../../components/WorkItemTable_improved.vue'
import { ArrowDown, Loading, CircleCheck, CircleClose, Lock } from '@element-plus/icons-vue'

const userStore = useUserStore()
const router = useRouter()
const isAdmin = computed(() => userStore.isAdmin)
const isLeader = computed(() => userStore.isLEADER)
const isDepartment = computed(() => userStore.isDEPARTMENT)
const currentUserId = computed(() => String(userStore.userInfo?.id || ''))
const activeTab = ref('mine')   // 默认显示“所有项目”

const tableRowClassName = ({ row }) => {
  if (row.closed_status) return 'closed-row'      // 返回深灰类名
  if (row.complete_status) return 'completed-row' // 返回浅灰类名
  return ''
}

//是否有权新增项目
const canAddProject = computed(() => isAdmin.value || isLeader.value || isDepartment.value)

// 是否有权管理某个项目：系统管理员 / 领导 / 该项目负责人
const canManageProject = (projectRow) => {
  if (isAdmin.value || isLeader.value || isDepartment.value) return true
  return String(projectRow?.owner_id || '') === currentUserId.value
}


const tableData = ref([]) // 控制行内编辑的可变表格数据源
const loadingAllWorkPackages = ref(false)
const refreshKey = ref(0) // 传给工作项表格：点「刷新」时强制拉取最新数据
const saving = ref(false)
const searchKeyword = ref('')
const projectOptions = ref([])
const userOptions = ref([])

// —— 所有项目：服务端分页状态 ——
const pagedTotal = ref(0)
const pagedPage = ref(1)
const pagedPageSize = ref(20)

// —— 我的工作：服务端分页状态 ——
const myWorkPackages = ref([])
const myTotal = ref(0)
const myPage = ref(1)
const myPageSize = ref(20)

//工作包转交状态
const transferDialogVisible = ref(false) // 弹窗开关
const transferPkg = ref(null)            // 当前要转办的工作包
const transferTargetId = ref('')         // 选中的接收人
const transferTargets = ref([])          // 可选的接收人（排除自己）
const transferring = ref(false)          // 提交中 loading


// 获取配置项
const fetchAdminOptions = async () => {
  if (!isAdmin.value && !isLeader.value && !isDepartment) return
  try {
    const [projectsRes, usersRes] = await Promise.all([
      getAllProjectsApi(),
      getAllUsersApi()
    ])
    projectOptions.value = projectsRes.data?.data || []
    userOptions.value = usersRes.data?.data || []
  } catch (err) {
    console.error('获取管理员配置选项失败:', err)
  }
}

// —— 所有项目：服务端分页拉取并组装 ——
const fetchProjects = async (page = 1) => {
  loadingAllWorkPackages.value = true
  pagedPage.value = page
  try {
    const params = { page, page_size: pagedPageSize.value }
    const kw = searchKeyword.value.trim()
    if (kw) params.keyword = kw
    const res = await getPagedProjectsApi(params)
    if (res.data?.code === 200) {
      const data = res.data.data || {}
      pagedTotal.value = data.total || 0
      tableData.value = (data.items || []).map(p => ({
        project_id: p.id,
        project_name: p.name,
        project_code: p.code,
        category: p.category,
        level: p.level,
        owner_name: p.owner_name,
        owner_id: p.owner_id === '-' ? '' : p.owner_id,
        tech_owner_id: p.tech_owner_id === '-' ? '' : p.tech_owner_id,
        tech_owner_name: p.tech_owner_name === '未指定机型主管' ? '' : p.tech_owner_name,
        progress: p.project_progress || 0,
        complete_status: p.complete_status,
        manual_complete_status: p.manual_complete_status,
        closed_status: p.closed_status || false,
        work_package_count: p.work_package_count || 0,
        work_packages: [],
        isEdit: false,
        isNew: false,
        _original: null
      }))
      // 记录原始快照，供取消编辑回退
      tableData.value.forEach(r => { r._original = JSON.parse(JSON.stringify(r)) })
    }
  } catch (err) {
    console.error('获取项目列表失败:', err)
    ElMessage.error(err.response?.data?.detail || '获取项目列表失败')
  } finally {
    loadingAllWorkPackages.value = false
  }
}


// —— 我的工作：服务端分页 ——
const fetchMyWorkPackages = async (page = 1) => {
  myPage.value = page
  try {
    const res = await getMyWorkPackagesPagedApi(currentUserId.value, { page, page_size: myPageSize.value })
    if (res.data?.code === 200) {
      const data = res.data.data || {}
      myTotal.value = data.total || 0
      myWorkPackages.value = data.items || []
    }
  } catch (err) {
    console.error('获取我的工作失败:', err)
    ElMessage.error(err.response?.data?.detail || '获取我的工作失败')
  }
}


// 双击项目行 → 跳转到项目详情页
const openProjectDetail = (project) => {
  if (project.isEdit || project.isNew) return // 编辑/新增状态下不触发跳转
  if (!project.project_id) {
    ElMessage.warning('该项目尚未保存，无法查看工作包')
    return
  }
  router.push({
    path: `/project/${project.project_id}`,
    query: { name: project.project_name }
  })
}

// 搜索：防抖触发服务端查询
let searchTimer = null
watch(searchKeyword, () => {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => fetchProjects(1), 300)
})

// 顶部刷新：同时刷新所有项目与我的工作
const refreshAll = () => {
  refreshKey.value++ // 通知已展开的工作项表格强制拉取最新数据
  fetchProjects(pagedPage.value)
  fetchMyWorkPackages(myPage.value)
}

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
  if (row.project_closed) return statusConfig['所属已关闭']
  if (row.complete_status) return statusConfig['已完成']
  return statusConfig['进行中']
}

// 是否存在可用的“更多”操作：控制更多按钮禁用，避免点开空菜单
const hasMoreOptions = (row) => {
  if (!row || row.isEdit) return false
  if (row.closed_status) return !!isAdmin.value // 已关闭：仅管理员可“取消关闭”
  return true                                  // 未关闭：删除/完成/关闭等均可能
}

//更多操作菜单
const handleMoreCommand = async (command, row) => {
  switch (command) {
    case 'delete':
      try {
        await ElMessageBox.confirm(
          '确定删除该工作项？',
          '删除确认',
          {
            confirmButtonText: '确定删除',
            cancelButtonText: '取消',
            type: 'warning'
          }
        )
        await removeProject(row)
      } catch (err) {
        // 用户点击取消时不提示
        if (err !== 'cancel' && err !== 'close') {
          console.error(err)
        }
      }
      break
    case 'confirmComplete':
      await confirmProject(row)
      break

    case 'cancelComplete':
      await confirmProject(row)
      break

    case 'confirmClosed':
      await handleClosedConfirm(row)
      break

    case 'cancelClosed':
      await handleCancelClosedConfirm(row)
      break
  }
}

// —— 确认完成（项目/工作包，负责人或领导/管理员）——
const confirming = ref(false)
// 是否为工作包负责人本人（可发起工作包转办）
const isPkgOwner = (pkg) => String(pkg.package_owner_id || '') === currentUserId.value
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
      refreshAll()
    }
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '操作失败')
  } finally {
    confirming.value = false
  }
}
const confirmProject = (row) => doConfirm('project', row.project_id, !row.manual_complete_status)
const confirmPkg = (pkg) => doConfirm('work_package', pkg.id, !pkg.manual_complete_status)

const handleClosedConfirm = (row) => {
  confirmClose('项目', () => {
    confirmClosed(row)
  })
}

const handleCancelClosedConfirm = (row) => {
  confirmCancelClose('项目', () => { confirmClosed(row) })
}

// —— 确认/取消关闭（工作包/项目，只有领导/管理员，后端会校验）——
const canClosed = computed(() => isAdmin.value || isLeader.value)
const confirmClosed = async (row) => {
  confirming.value = true
  try {
    const res = await confirmClosedApi({
      target_type: 'project',
      target_id: row.project_id,
      user_id: currentUserId.value,
      confirmed: !row.closed_status
    })
    if (res.data?.code === 200) {
      ElMessage.success(row.closed_status ? '已取消关闭' : '已确认关闭')
      refreshAll()
    }
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '操作失败')
  } finally {
    confirming.value = false
  }
}
/* =============== 行内编辑相关方法 =============== */
//删除项目
const removeProject = async (row) => {
  try {
    //弹出确认框
    await ElMessageBox.confirm(
      '确定要删除该项目吗？此操作会一并删除改项目下所有工作包和工作项以及拆包请求，且无法撤销。',
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    // 用户点击确定后，执行原有的删除逻辑
    const res = await deleteProjectApi(row.project_id, currentUserId.value)
    
    if (res.data?.code === 200) {
      ElMessage.success('项目已删除')
      await fetchProjects(pagedPage.value)
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


// 新增与操作项目 (主表)
const handleAddProject = () => {
  tableData.value.unshift({
    project_id: '',
    project_code:'',
    project_name: '',
    category: '',
    level: 'C',
    owner_id: '',
    tech_owner_id:'',
    work_packages: [],
    isEdit: true,
    isNew: true
  })
}

const handleSaveProject = async (row) => {
  if (!row.project_name || !row.project_name.trim()) {
    return ElMessage.warning('请输入项目名称')
  }
  saving.value = true
  try {
    const res = await createProjectApi({
      id: row.isNew ? null : row.project_id,
      code: row.project_code,
      name: row.project_name.trim(),
      category: row.category,
      level: row.level,
      owner_id: row.owner_id || null,
      tech_owner_id: row.tech_owner_id || null
    })
    if (res.data?.code === 200) {
      ElMessage.success('项目保存成功')
      row.isEdit = false
      row.isNew = false
      await fetchProjects(pagedPage.value)
      await fetchAdminOptions()
    }
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '项目保存失败')
  } finally {
    saving.value = false
  }
}

const cancelProjectEdit = (row, index) => {
  if (row.isNew) {
    tableData.value.splice(index, 1) // 新增行取消则直接移除
  } else {
    // 恢复原始快照
    if (row._original) {
      Object.assign(row, JSON.parse(JSON.stringify(row._original)))
    }
    row.isEdit = false
  }
}

const handleTransferWorkPackage = async(pkg) => {
  transferPkg.value = pkg
  transferTargetId.value = ''
  // 拉用户列表（排除自己）——注意不能依赖 fetchAdminOptions，那个只给管理员/领导拉
  try {
    const res = await getAllUsersApi()
    transferTargets.value = (res.data?.data || []).filter(u => String(u.id) !== currentUserId.value)
  } catch (err) {
    return ElMessage.error('获取用户列表失败')
  }
  transferDialogVisible.value = true 
}

const confirmTransfer = async () => { //确认发起函数
  if (!transferTargetId.value) return ElMessage.warning('请选择接收人')
  transferring.value = true
  try {
    const res = await initiateTransferApi({
      transfer_type: 'work_package',
      work_package_id: transferPkg.value.id, // pkg.id 就是工作包 ID
      from_user_id: currentUserId.value,
      to_user_id: transferTargetId.value
    })
    if (res.data?.code === 200) {
      ElMessage.success('转办申请已发送')
      transferDialogVisible.value = false
      await fetchProjects(pagedPage.value)
      await fetchMyWorkPackages(myPage.value)
    }
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '发起转办失败')
  } finally {
    transferring.value = false
  }
}

onMounted(async () => {
  await fetchProjects(1)
  await fetchMyWorkPackages(1)
  await fetchAdminOptions()
})

</script>
<style scoped>
/* 延续美化风格的 CSS 样式 */
.project-overview {
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


/* 完成/关闭行不再整行禁用点击；具体操作由按钮/菜单 v-if 控制，仅弱化文字颜色 */
.project-overview :deep(.completed-row .el-button--link),
.project-overview :deep(.closed-row .el-button--link) {
  color: #c0c4cc;
}

/* 表格固定高度内部滚动，不受全局 flex:1 拉伸影响 */
:deep(.el-table) {flex: none !important; }

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1px;
  padding: 0 4px;
}


.header-actions {
  display: flex;
  gap: 16px; /* 两个输入框之间的间距 */
}

.search-input {
  width: 240px;
}

.pagination-bar {
  display: flex;
  justify-content: flex-end;
  padding-top: 12px;
}

/* 文本和列的颜色高亮 */
.employee-text {
  color: #0f766e;
  font-weight: 500;
}
.owner-text {
  color: #475569;
  font-weight: 600;
}
.tip-text, .muted-text {
  color: #94a3b8;
  font-size: 13px;
}

/* 状态圆点设计 */
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

/* 嵌套表格容器的背景处理 */
.nested-table-container {
  padding: 16px;
  background-color: #f8fafc;
  border-radius: 8px;
  margin: 10px 20px;
  box-shadow: inset 0 2px 4px 0 rgba(0, 0, 0, 0.02);
}

:deep(.el-table__expanded-cell) {
  padding: 0 !important;
  background-color: #fbfbfc !important;
}

/* ==========================================
   现代简约商务风 表格统一样式改造（与项目详情一致）
========================================== */

/* 1. 表格全局变量替换：去线化、低饱和度 */
.project-overview :deep(.el-table) {
  --el-table-border-color: #f1f5f9; /* 极浅的分割线 */
  --el-table-header-bg-color: #ffffff; /* 表头纯白，靠底边框区分 */
  --el-table-header-text-color: #64748b; /* 表头文字使用 slate-500 灰色，不抢戏 */
  --el-table-row-hover-bg-color: #f8fafc; /* 极其微妙的悬浮高亮 */
  --el-table-text-color: #334155; /* 正文深灰，比纯黑更柔和 */
  background-color: transparent;
}

/* 2. 表头优化：去掉竖线，加粗底线，增加呼吸感 */
.project-overview :deep(.el-table__header th) {
  font-weight: 600;
  font-size: 13px;
  padding: 12px 0; /* 增加表头上下留白 */
  border-bottom: 2px solid #e2e8f0 !important; /* 加重表头底线，稳住视觉重心 */
}

/* 3. 单元格优化：增加行高，让数据不拥挤 */
.project-overview :deep(.el-table__row td.el-table__cell) {
  padding: 14px 0; /* 增加正文单元格上下留白 */
  font-size: 14px;
}

/* 4. 隐藏固定列的阴影线（让左右固定列更无缝衔接） */
.project-overview :deep(.el-table__fixed-right::before),
.project-overview :deep(.el-table__fixed::before) {
  display: none;
}

/* 5. 优化已完成/已关闭行的视觉呈现（更温和的灰显） */
.project-overview :deep(.completed-row td) {
  background-color: #f9fafb !important;
  color: #94a3b8;
}

.project-overview :deep(.closed-row td) {
  background-color: #f9fafb !important;
  color: #94a3b8;
}

.project-overview :deep(.completed-row ),
.project-overview :deep(.closed-row ) {
  background-color: #f1f5f9;
  color: #94a3b8;
  opacity: 0.7;
}

:deep(.completed-row .el-button--link) {
  color: #c0c4cc;
}

.project-overview :deep(.status-text) {
  color: #334155 !important;  /* 统一改为深灰色 */
  font-weight: 500;
}
/* 强制让 Tabs 标签页容器弹性撑满屏幕剩余高度 */
:deep(.el-tabs) {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

:deep(.el-tabs__content) {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

:deep(.el-tab-pane) {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
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

.danger-menu-item {
  color: var(--el-color-danger);
}

.el-dropdown {
  margin-left: 4px;
}
</style>