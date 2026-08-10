<template>
  <div class="project-overview">
    <el-card class="box-card" shadow="never">
      <template #header>
        <div class="card-header">
          <div class="header-title">
            <span>项目总览</span>
          </div>
          <div class="header-actions">
            <el-input
              v-model="searchKeyword"
              placeholder="输入项目名称搜索..."
              clearable
              class="search-input"
            >
              <template #prefix>
                <i class="el-icon-search"></i>
              </template>
            </el-input>
            <!-- 只保留新增项目在顶部，新增工作包移至每一行内 -->
            <el-button v-if="isAdmin" type="success" plain @click="handleAddProject">
              <i class="el-icon-folder-add"></i> 新增项目
            </el-button>
            <el-button type="primary" @click="fetchAllWorkPackages">
              <i class="el-icon-refresh"></i> 刷新
            </el-button>
          </div>
        </div>
      </template>

      <!-- 外层主表格：显示项目信息 -->
      <el-table
        ref="projectTableRef"
        :data="tableData"
        style="width: 100%"
        v-loading="loadingAllWorkPackages"
        height="calc(100vh - 220px)"
        empty-text="暂无项目数据"
        row-key="project_id"
        :row-class-name="tableRowClassName"
        :header-cell-style="{ background: '#f8fafc', color: '#334155', fontWeight: 'bold' }"
      >
        <!-- 内层嵌套表格：显示工作包信息 -->
        <el-table-column type="expand">
          <template #default="{ row: projectRow }">
            <div class="nested-table-container">
              <el-table
                :data="projectRow.work_packages"
                border
                size="small"
                style="width: 100%"
                :row-class-name="tableRowClassName"
                :header-cell-style="{ background: '#f1f5f9', color: '#475569' }"
                @row-dblclick="handleOpenWorkItems"
              >
                <el-table-column prop="id" label="编号" width="140" align="center">
                  <template #default="{ row: pkg }">
                    <el-input v-if="pkg.isEdit && pkg.isNew" v-model="pkg.id" size="small" placeholder="留空自动生成" />
                    <span v-else class="code-text">{{ pkg.id }}</span>
                  </template>
                </el-table-column>
                
                <el-table-column prop="category_name" label="类别" width="140" align="center">
                  <template #default="{ row: pkg }">
                    <el-select v-if="pkg.isEdit" v-model="pkg.category_name" size="small">
                      <el-option v-for="cat in categoryOptions" :key="cat" :label="cat" :value="cat" />
                    </el-select>
                    <el-tag v-else size="small" type="info">{{ pkg.category_name }}</el-tag>
                  </template>
                </el-table-column>
                
                <el-table-column prop="next_step_work" label="下阶段工作" min-width="180">
                  <template #default="{ row: pkg }">
                    <el-input v-if="pkg.isEdit" type="textarea" autosize v-model="pkg.next_step_work" size="small" placeholder="描述工作内容" />
                    <template v-else>
                      <span class="muted-text" v-if="!pkg.next_step_work">暂无设定</span>
                      <span v-else>{{ pkg.next_step_work }}</span>
                    </template>
                  </template>
                </el-table-column>
                
                <el-table-column prop="objective" label="目标" min-width="180">
                  <template #default="{ row: pkg }">
                    <el-input v-if="pkg.isEdit" type="textarea" autosize v-model="pkg.objective" size="small" placeholder="设定工作目标" />
                    <template v-else>
                      <span class="muted-text" v-if="!pkg.objective">暂无设定</span>
                      <span v-else>{{ pkg.objective }}</span>
                    </template>
                  </template>
                </el-table-column>

                <el-table-column label="责任人" min-width="150">
                  <template #default="{ row: pkg }">
                    <span v-if="pkg.owner_name || pkg.assignee_id" class="employee-text">
                      <i class="el-icon-user"></i> {{ pkg.owner_name || pkg.assignee_name || pkg.assignee_id }}
                    </span>
                    <span v-else class="tip-text">暂未指定</span>
                  </template>
                </el-table-column>

                <el-table-column v-if="isAdmin" label="操作" width="140" align="center" fixed="right">
                  <template #default="{ row: pkg, $index }">
                    <template v-if="pkg.isEdit">
                      <el-button type="success" link size="small" @click="handleSaveWorkPackage(pkg, projectRow)">保存</el-button>
                      <el-button type="info" link size="small" @click="cancelWpEdit(pkg, projectRow, $index)">取消</el-button>
                    </template>
                    <template v-else>
                      <el-button type="primary" link size="small" @click="pkg.isEdit = true">编辑</el-button>
                    </template>
                  </template>
                </el-table-column>
              </el-table>
            </div>
          </template>
        </el-table-column>

        <!-- 主表格列配置 -->
        <el-table-column prop="project_name" label="项目名称" min-width="200">
          <template #default="{ row }">
            <el-input v-if="row.isEdit" v-model="row.project_name" size="small" placeholder="请输入项目名称" />
            <span v-else class="project-title">{{ row.project_name }}</span>
          </template>
        </el-table-column>

        <el-table-column prop="category" label="项目类别" width="140" align="center">
          <template #default="{ row }">
            <el-input v-if="row.isEdit" v-model="row.category" size="small" placeholder="如:研发" />
            <template v-else>
              <el-tag v-if="row.category" type="info" effect="plain">{{ row.category }}</el-tag>
              <span v-else class="tip-text">-</span>
            </template>
          </template>
        </el-table-column>
        
        <el-table-column label="项目级别" width="120" align="center">
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

        <el-table-column label="负责人" width="160">
          <template #default="{ row }">
            <el-select v-if="row.isEdit" v-model="row.owner_id" clearable filterable placeholder="选择负责人" size="small" style="width: 100%">
              <el-option v-for="user in userOptions" :key="user.id" :label="`${user.username}（${user.id}）`" :value="user.id" />
            </el-select>
            <template v-else>
              <span class="owner-text" v-if="row.owner_name || row.owner_id">
                {{ row.owner_name ? `${row.owner_name}（${row.owner_id}）` : row.owner_id }}
              </span>
              <span v-else class="tip-text">暂未指定</span>
            </template>
          </template>
        </el-table-column>

        <el-table-column label="进度" width="120" align="center">
          <template #default="{ row }">
            <span v-if="row.project_completed" class="status-dot success">已完结</span>
            <span v-else class="status-dot primary">进行中</span>
          </template>
        </el-table-column>

        <el-table-column v-if="isAdmin" label="操作" width="200" align="center" fixed="right">
          <template #default="{ row, $index }">
            <template v-if="row.isEdit">
              <el-button type="success" link size="small" @click="handleSaveProject(row)">保存</el-button>
              <el-button type="info" link size="small" @click="cancelProjectEdit(row, $index)">取消</el-button>
            </template>
            <template v-else>
              <el-button type="primary" link size="small" @click="row.isEdit = true">编辑</el-button>
              <el-button type="warning" link size="small" @click="handleAddWorkPackage(row)">+ 工作包</el-button>
            </template>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import {
  createProjectApi,
  createWorkPackageApi,
  getAllProjectsApi,
  getAllUsersApi,
  getPublicWorkPackagesApi
} from '../api'
import { useUserStore } from '../stores/user'
import { useRouter } from 'vue-router'

const userStore = useUserStore()
const router = useRouter()
const isAdmin = computed(() => userStore.isAdmin)

const projectTableRef = ref(null) // 用于触发表格展开
const allWorkPackages = ref([])
const tableData = ref([]) // 控制行内编辑的可变表格数据源
const loadingAllWorkPackages = ref(false)
const saving = ref(false)
const searchKeyword = ref('')
const projectOptions = ref([])
const userOptions = ref([])
const categoryOptions = ['类型1', '类型2', '类型3', '类型4']

// 获取配置项
const fetchAdminOptions = async () => {
  if (!isAdmin.value) return
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

// 拉取列表并组装数据
const fetchAllWorkPackages = async () => {
  loadingAllWorkPackages.value = true
  try {
    const res = await getPublicWorkPackagesApi()
    if (res.data && res.data.code === 200) {
      allWorkPackages.value = res.data.data || []
    }
  } catch (err) {
    console.error('获取所有工作包失败:', err)
    ElMessage.error(err.response?.data?.detail || '获取所有工作包失败')
  } finally {
    loadingAllWorkPackages.value = false
  }
}

const tableRowClassName = ({ row }) => {
  if (row.pkg_completed || row.project_completed) return 'completed-row'
  return ''
}

// 双击工作包行 → 跳转到该工作包的工作项管理页面
const handleOpenWorkItems = (pkg) => {
  if (pkg.isEdit || pkg.isNew) return // 编辑/新增状态下不触发跳转
  if (!pkg.id) {
    ElMessage.warning('该工作包尚未保存，无法查看工作项')
    return
  }
  router.push({
    path: `/work-package/${pkg.id}/work-items`,
    query: { name: pkg.next_step_work || pkg.id, project: pkg.project_name }
  })
}

// 核心数据处理：保证父子层级的字段正确映射
const groupedProjects = computed(() => {
  const map = {}
  allWorkPackages.value.forEach(pkg => {
    const projectKey = pkg.project_id || pkg.project_name
    if (!map[projectKey]) {
      map[projectKey] = {
        project_id: projectKey,
        project_name: pkg.project_name,
        category: pkg.project_category || pkg.category,
        level: pkg.project_level || pkg.level,
        owner_name: pkg.project_owner_name || pkg.owner_name,
        owner_id: pkg.project_owner_id || pkg.owner_id,
        project_completed: pkg.project_completed || false,
        work_packages: [],
        isEdit: false,
        isNew: false
      }
    }
    map[projectKey].work_packages.push({
      ...pkg,
      next_step_work: pkg.next_step_work,
      isEdit: false,
      isNew: false
    })
  })
  return Object.values(map)
})

const filterProjects = computed(() => {
  const keyword = searchKeyword.value.trim()
  if (!keyword) return groupedProjects.value
  return groupedProjects.value.filter(project => {
    return String(project.project_name || '').includes(keyword)
  })
})

// 监听计算后的属性，同步至本地 ref 供行内编辑使用
watch(filterProjects, (newVal) => {
  // 如果当前表格中有任何行处于编辑状态，则暂停覆盖更新，防止用户输入丢失
  const hasEditing = tableData.value.some(p => p.isEdit || (p.work_packages && p.work_packages.some(w => w.isEdit)))
  if (!hasEditing) {
    tableData.value = JSON.parse(JSON.stringify(newVal))
  }
}, { deep: true, immediate: true })

/* =============== 行内编辑相关方法 =============== */

// 1. 新增与操作项目 (主表)
const handleAddProject = () => {
  tableData.value.unshift({
    project_id: '',
    project_name: '',
    category: '',
    level: 'C',
    owner_id: '',
    project_completed: false,
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
      name: row.project_name.trim(),
      category: row.category,
      level: row.level,
      owner_id: row.owner_id || null
    })
    if (res.data?.code === 200) {
      ElMessage.success('项目保存成功')
      row.isEdit = false
      row.isNew = false
      await fetchAllWorkPackages()
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
    // 恢复历史原始数据
    const original = filterProjects.value.find(p => p.project_id === row.project_id)
    if (original) {
      Object.assign(row, JSON.parse(JSON.stringify(original)))
    }
    row.isEdit = false
  }
}

// 2. 新增与操作工作包 (子表)
const handleAddWorkPackage = (projectRow) => {
  // 展开当前项目行
  if (projectTableRef.value) {
    projectTableRef.value.toggleRowExpansion(projectRow, true)
  }
  // 在子表顶部推入一条空记录
  projectRow.work_packages.unshift({
    id: '',
    project_id: projectRow.project_id,
    project_name: projectRow.project_name,
    category_name: '类型1',
    next_step_work: '',
    objective: '',
    isEdit: true,
    isNew: true
  })
}

const handleSaveWorkPackage = async (pkg, parentProject) => {
  if (!pkg.next_step_work || !pkg.next_step_work.trim()) {
    return ElMessage.warning('请填写下阶段工作')
  }
  saving.value = true
  try {
    const res = await createWorkPackageApi({
      work_package_id: pkg.id,
      project_id: Number(parentProject.project_id),
      project_name: parentProject.project_name,
      category_name: pkg.category_name,
      next_step_work: pkg.next_step_work.trim(),
      objective: pkg.objective ? pkg.objective.trim() : ''
    })
    if (res.data?.code === 200) {
      ElMessage.success('工作包保存成功')
      pkg.isEdit = false
      pkg.isNew = false
      await fetchAllWorkPackages()
    }
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '工作包保存失败')
  } finally {
    saving.value = false
  }
}

const cancelWpEdit = (pkg, parentProject, index) => {
  if (pkg.isNew) {
    parentProject.work_packages.splice(index, 1)
  } else {
    // 恢复历史原始数据
    const originalProject = filterProjects.value.find(p => p.project_id === parentProject.project_id)
    if (originalProject) {
      const originalPkg = originalProject.work_packages.find(w => w.id === pkg.id)
      if (originalPkg) {
        Object.assign(pkg, JSON.parse(JSON.stringify(originalPkg)))
      }
    }
    pkg.isEdit = false
  }
}

onMounted(async () => {
  await fetchAllWorkPackages()
  await fetchAdminOptions()
})
</script>

<style scoped>
/* 延续美化风格的 CSS 样式 */
.project-overview {
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

.header-title {
  font-size: 18px;
  font-weight: 600;
  color: #1e293b;
  display: flex;
  align-items: center;
}

.header-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

.search-input {
  width: 240px;
}

/* 文本和列的颜色高亮 */
.project-title {
  font-weight: bold;
  color: #334155;
  font-size: 14px;
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
.owner-text {
  color: #475569;
  font-weight: 600;
}
.tip-text, .muted-text {
  color: #94a3b8;
  font-size: 13px;
}

/* 状态圆点设计 */
.status-dot {
  display: inline-flex;
  align-items: center;
  font-size: 13px;
  font-weight: 500;
}
.status-dot::before {
  content: '';
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-right: 6px;
}
.status-dot.success::before {
  background-color: #10b981;
  box-shadow: 0 0 0 2px #d1fae5;
}
.status-dot.primary::before {
  background-color: #3b82f6;
  box-shadow: 0 0 0 2px #dbeafe;
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

/* 完成行灰显处理 */
:deep(.el-table .completed-row) {
  --el-table-tr-bg-color: #f8fafc;
  color: #94a3b8;
}

:deep(.el-table .completed-row:hover > td) {
  background-color: #f1f5f9 !important;
}

:deep(.el-table .completed-row .el-tag),
:deep(.el-table .completed-row .status-dot) {
  opacity: 0.6;
  filter: grayscale(0.8);
}
</style>