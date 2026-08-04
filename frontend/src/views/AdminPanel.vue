<!-- xiangmu/frontend/src/views/AdminPanel.vue -->
<template>
  <div class="admin-panel-container">
    <el-card shadow="hover">
      <template #header>
        <div class="card-header">
          <span>⚙️ 系统基础数据与任务分配管理后台</span>
          <el-button type="primary" size="small" @click="fetchAllData" icon="Refresh">刷新数据</el-button>
        </div>
      </template>

      <el-tabs v-model="activeTab" type="border-card">
        
        <!-- 👥 1. 人员列表与新增 -->
        <el-tab-pane label="👥 人员管理" name="users">
          <el-row :gutter="20">
            <!-- 左侧：新增表单 -->
            <el-col :span="8">
              <el-card header="➕ 新增人员" shadow="never">
                <el-form :model="userForm" label-width="80px" size="default">
                  <el-form-item label="工号" required>
                    <el-input v-model="userForm.id" placeholder="如: 1003" />
                  </el-form-item>
                  <el-form-item label="姓名" required>
                    <el-input v-model="userForm.username" placeholder="如: 张三" />
                  </el-form-item>
                  <el-form-item label="密码" required>
                    <el-input v-model="userForm.password" type="password" show-password placeholder="默认 123" />
                  </el-form-item>
                  <el-form-item label="角色" required>
                    <el-select v-model="userForm.role" style="width: 100%">
                      <el-option label="普通员工 (EMPLOYEE)" value="EMPLOYEE" />
                      <el-option label="项目负责人 (OWNER)" value="OWNER" />
                      <el-option label="系统管理员 (ADMIN)" value="ADMIN" />
                    </el-select>
                  </el-form-item>
                  <el-form-item>
                    <el-button type="primary" style="width: 100%" @click="handleCreateUser">确认添加人员</el-button>
                  </el-form-item>
                </el-form>
              </el-card>
            </el-col>

            <!-- 右侧：现有人员表格 -->
            <el-col :span="16">
              <el-card header="📋 现有人员名册" shadow="never">
                <el-table :data="allUsers" border stripe style="width: 100%">
                  <el-table-column prop="id" label="工号 (ID)" width="120" sortable />
                  <el-table-column prop="username" label="姓名" width="150" />
                  <el-table-column label="系统角色">
                    <template #default="{ row }">
                      <el-tag v-if="String(row.role).toUpperCase() === 'ADMIN'" type="danger">
                        管理员 (ADMIN)
                      </el-tag>
                      <el-tag v-else-if="String(row.role).toUpperCase() === 'OWNER' || String(row.role).toUpperCase() === 'LEADER'" type="warning">
                        项目负责人 (OWNER)
                      </el-tag>
                      <el-tag v-else type="info">
                        普通员工 (EMPLOYEE)
                      </el-tag>
                    </template>
                  </el-table-column>
                </el-table>
              </el-card>
            </el-col>
          </el-row>
        </el-tab-pane>

          <!-- ================= ✈️ 项目管理 (行内编辑版) ================= -->
        <el-tab-pane label="✈️ 项目管理">
          <div style="margin-bottom: 15px;">
            <el-button type="primary" icon="Plus" @click="handleAddProjectRow">
             ➕ 在表格中新增一行项目
           </el-button>
          </div>
        
          <el-table :data="projectList" border stripe style="width: 100%">
            <!-- <el-table-column prop="id" label="ID" width="80" align="center" /> -->
            
            <el-table-column label="项目名称" min-width="150">
              <template #default="{ row }">
                <el-input v-if="row.isEdit" v-model="row.name" placeholder="请输入项目名称" size="small" />
                <span v-else>{{ row.name }}</span>
              </template>
            </el-table-column>
            
            <el-table-column label="负责人ID/工号" min-width="150">
              <template #default="{ row }">
                <el-input v-if="row.isEdit" v-model="row.owner_id" placeholder="选填，可输入负责人ID" size="small" />
                <span v-else>{{ row.owner_id || '未绑定' }}</span>
              </template>
            </el-table-column>
            
            <el-table-column label="操作" width="180" align="center">
              <template #default="{ row, $index }">
                <div v-if="row.isEdit">
                  <el-button type="success" size="small" @click="handleSaveProject(row)">💾 保存</el-button>
                  <el-button type="info" size="small" plain @click="handleCancelProject(row, $index)">取消</el-button>
                </div>
                <div v-else>
                  <el-button type="primary" size="small" plain @click="row.isEdit = true">✏️ 编辑</el-button>
                  </div>
                </template>
              </el-table-column>
            </el-table>
        </el-tab-pane>

        <!-- ================= 📦 工作包管理 (行内编辑版) ================= -->
        <el-tab-pane label="📦 工作包管理">
          <div style="margin-bottom: 15px;">
            <el-button type="primary" icon="Plus" @click="handleAddWorkPackageRow">
              ➕ 在表格中新增一行工作包
            </el-button>
          </div>
          
          <el-table :data="workPackageList" border stripe style="width: 100%" height="600">
            <el-table-column label="所属项目" width="140">
              <template #default="{ row }">
                <el-select v-if="row.isEdit" v-model="row.project_name" size="small" placeholder="选项目">
                  <el-option v-for="ac in projectList" :key="ac.name" :label="ac.name" :value="ac.name" />
                </el-select>
                <span v-else>{{ row.project_name }}</span>
              </template>
            </el-table-column>
            
            <el-table-column label="工作类型" width="140">
              <template #default="{ row }">
                <el-select 
                  v-if="row.isEdit" 
                  v-model="row.category_name" 
                  size="small" 
                  placeholder="请选择类型"
                >
                  <el-option 
                    v-for="type in categoryOptions" 
                    :key="type" 
                    :label="type" 
                    :value="type" 
                  />
                </el-select>
                <span v-else>
                  <el-tag size="small" type="info">{{ row.category_name }}</el-tag>
                </span>
              </template>
            </el-table-column>

            <el-table-column label="工作包名称" min-width="180">
              <template #default="{ row }">
                <el-input v-if="row.isEdit" v-model="row.name" size="small" placeholder="工作包名称" />
                <span v-else>{{ row.name }}</span>
              </template>
            </el-table-column>

            <el-table-column label="基础积分" width="100" align="center">
              <template #default="{ row }">
                <el-input-number v-if="row.isEdit" v-model="row.score" :min="0" :step="0.5" size="small" style="width: 80px;" controls-position="right" />
                <span v-else style="color: #67c23a; font-weight: bold;">{{ row.score }}</span>
              </template>
            </el-table-column>

            <el-table-column label="负责员工" width="170">
              <template #default="{ row }">
                <el-select
                  v-if="row.isEdit"
                  v-model="row.assignee_id"
                  size="small"
                  placeholder="请选择员工"
                  filterable
                  default-first-option
                  style="width: 100%"
                >
                  <el-option
                    v-for="employee in employeeOptions"
                    :key="employee.id"
                    :label="employee.label"
                    :value="employee.id"
                  />
                </el-select>
                <span v-else>{{ row.assignee_name || row.assignee_id || '未指定' }}</span>
            </template>
          </el-table-column>

            <el-table-column label="时间节点要求" min-width="160">
              <template #default="{ row }">
                <el-input v-if="row.isEdit" v-model="row.node_requirement" size="small" placeholder="如: 2026-08-15" />
                <el-tag v-else-if="row.node_requirement" type="danger" effect="plain">⏰ {{ row.node_requirement }}</el-tag>
                <span v-else style="color: #909399; font-size: 13px;">无</span>
              </template>
            </el-table-column>

            <el-table-column label="操作" width="160" align="center" fixed="right">
              <template #default="{ row, $index }">
                <div v-if="row.isEdit">
                  <el-button type="success" size="small" @click="handleSaveWorkPackage(row)">💾 保存</el-button>
                  <el-button type="info" size="small" plain style="margin-left: 5px;" @click="handleCancelWorkPackage(row, $index)">取消</el-button>
                </div>
                <div v-else>
                  <el-button type="primary" size="small" plain @click="row.isEdit = true">✏️ 编辑</el-button>
                </div>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

      </el-tabs>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { 
  getAllUsersApi, 
  getAllProjectsApi, 
  getWorkPackagesOverviewApi,
  createUserApi, 
  createProjectApi, 
  createWorkPackageApi
} from '../api'

const activeTab = ref('users')

// 数据源
const allUsers = ref([])
const allProjects = ref([])
const allWorkPackages = ref([])

// 表单响应式绑定
const userForm = reactive({ id: '', username: '', password: '123', role: 'EMPLOYEE' })
const projectList = ref([])
const workPackageList = ref([])
const categoryOptions = ref(['类型1', '类型2', '类型3', '类型4'])
const employeeOptions = ref([])

const currentUser = ref(JSON.parse(localStorage.getItem('user_info') || '{}'))

// 批量加载所有数据
const fetchAllData = async () => {
  try {
    const [resUsers, resProjects, resWorkPackages] = await Promise.all([
      getAllUsersApi(),
      getAllProjectsApi(),
      getWorkPackagesOverviewApi()
    ])
    if (resUsers.data.code === 200){
      const users = resUsers.data.data || []
      allUsers.value = users.sort((a,b) => {
        return String(a.id).localeCompare(String(b.id), undefined, {numeric:true})
      })
    }
    if (resProjects.data.code === 200) allProjects.value = resProjects.data.data || []
    if (resWorkPackages.data.code === 200) allWorkPackages.value = resWorkPackages.data.data || []
  } catch (err) {
    console.error('拉取后台数据失败:', err)
  }
}

// 1. 新增人员
const handleCreateUser = async () => {
  if (!userForm.id.trim() || !userForm.username.trim()) return ElMessage.warning('请填写工号和姓名！')
  try {
    const res = await createUserApi({ 
        id: userForm.id.trim(), 
        username: userForm.username.trim(),
        password: userForm.password.trim(),
        role: String(userForm.role).toUpperCase() })
    if (res.data.code === 200) {
      ElMessage.success('人员创建成功！')
      userForm.id = ''
      userForm.username = ''
      fetchAllData()
    }
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '创建失败')
  }
}

// 2. 配置项目与负责人
const fetchProjects = async () => {
  try {
    const res = await getAllProjectsApi()
    // 🔑 核心：从后端获取数据后，给每一行都主动加上 isEdit: false 属性
    projectList.value = (res.data.data || []).map(item => ({
      ...item,
      isEdit: false 
    }))
  } catch (err) {
    console.error('获取项目失败', err)
  }
}

// ======================== 拉取员工名单 ========================
const fetchEmployees = async () => {
  try {
    const res = await getAllUsersApi()
    if (res.data && res.data.code === 200) {
      const users = res.data.data || []
      employeeOptions.value = users
      .filter(user => String(user.role).toUpperCase() === 'EMPLOYEE')
      .map(user => {
        const name = user.full_name || user.username
        return {
          id: String(user.id),
          label: `${name} (${user.id})`
        }
      })
    }
  } catch (err) {
    console.error('获取员工列表失败:', err)
  }
}

// ======================== 生命周期 ========================
// 🔑 修复 3：将两个 onMounted 合并为一个，并删除了不存在的 fetchAircrafts 和 fetchPackages
onMounted(() => {
  fetchAllData()
  fetchProjects()
  fetchWorkPackages()
  fetchEmployees()
})

const handleAddProjectRow = () => {
  // 在表格开头插入一个空的新行，并立即进入编辑状态
  projectList.value.unshift({
    id: null, 
    name: '',
    owner_id: '',
    isEdit: true
  })
}

const handleCancelProject = (row, index) => {
  if (row.id === null) {
    // 如果是还没有保存过的新行，直接从数组里删除
    projectList.value.splice(index, 1)
  } else {
    // 如果是旧数据取消编辑，直接把状态改回去，并重新拉取一次数据覆盖修改
    row.isEdit = false
    fetchProjects()
  }
}

const handleSaveProject = async (row) => {
  if (!row.name.trim()) return ElMessage.warning('项目名称不能为空！')
  try {
    // 调用你的后端保存接口（根据你的实际接口参数名调整）
    const res = await createProjectApi({
      id: row.id,
      name: row.name,
      owner_id: row.owner_id || null
    })
    if (res.data.code === 200) {
      ElMessage.success('项目保存成功！')
      row.isEdit = false
      fetchProjects() // 刷新获取最新生成的 ID
    }
  } catch (err) {
    ElMessage.error('保存失败，请检查数据')
  }
}

// 3. 创建工作包
const fetchWorkPackages = async () => {
  try {
    const res = await getWorkPackagesOverviewApi()
    // 同样注入 isEdit 状态
    workPackageList.value = (res.data.data || []).map(item => ({
      original_name: item.name, //  核心：记录下它最初的名字，作为编辑时的凭证
      name: item.name,
      project_name: item.project_name,
      category_name: item.category_name,
      score: item.score,
      assignee_id: item.assignee_id || '',
      assignee_name: item.assignee_name || '',
      node_requirement: item.deadline || item.node_requirement || '',
      isEdit: false
    }))
  } catch (err) {
    console.error('获取工作包失败', err)
  }
}

const handleAddWorkPackageRow = () => {
  workPackageList.value.unshift({
    original_name: null,
    project_name: '',
    category_name: '类型1',
    name: '',
    score: 0,
    node_requirement: '',
    assignee_id: '',
    assignee_name: '',
    isEdit: true
  })
}

const handleCancelWorkPackage = (row, index) => {
  if (!row.original_name) {
    workPackageList.value.splice(index, 1)
  } else {
    row.isEdit = false
    fetchWorkPackages()
  }
}

const handleSaveWorkPackage = async (row) => {
  if (!row.project_name || !row.category_name || !row.name) {
    return ElMessage.warning('项目、工作类型和工作包名称均为必填项！')
  }
  if (!row.assignee_id) {
    return ElMessage.warning('请选择负责员工！')
  }
  try {
    const payload = ({
      original_name: row.original_name,
      project_name: row.project_name,
      category_name: row.category_name,
      name: row.name,
      score: row.score,
      deadline: row.node_requirement || row.deadline || '',
      assignee_id: String(row.assignee_id),
      assigner_id: currentUser.value?.id ? String(currentUser.value.id) : String(row.assignee_id)
    })

    const res = await createWorkPackageApi(payload)
    if (res.data.code === 200) {
      ElMessage.success('工作包保存成功！')
      row.isEdit = false
      fetchWorkPackages()
    }
  } catch (err) {
    ElMessage.error('保存失败，请检查数据格式')
  }
}
</script>

<style scoped>
.admin-panel-container { padding: 20px; }
.card-header { display: flex; justify-content: space-between; align-items: center; font-weight: bold; font-size: 16px; }
</style>

