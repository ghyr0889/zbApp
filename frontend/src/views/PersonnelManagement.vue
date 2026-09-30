<!-- xiangmu/frontend/src/views/PersonnelManagement.vue -->
<template>
  <div class="personnel-management-container">
        
        <!-- 1. 人员列表与新增 -->
        <el-row :gutter="32">
          <!-- 左侧：新增表单 -->
          <el-col :span="8">
            <el-card header="新增人员" shadow="never">
              <el-form :model="userForm" label-width="80px" size="default">
                <el-form-item label="工号" required>
                  <el-input v-model="userForm.id" placeholder="如: 1003" />
                </el-form-item>
                <el-form-item label="姓名" required>
                  <el-input v-model="userForm.username" placeholder="如: 张三" />
                </el-form-item>
                <el-form-item label="密码" required>
                  <el-input v-model="userForm.password" type="password" show-password placeholder="默认 123456" />
                </el-form-item>
                <el-form-item label="角色" required>
                  <el-select v-model="userForm.role" style="width: 100%">
                    <el-option label="普通员工 (EMPLOYEE)" value="EMPLOYEE" />
                    <el-option label="科室主任 (DEPARTMENT)" value="DEPARTMENT" />
                    <el-option label="领导（部门主管、项目负责人） (LEADER)" value="LEADER" />
                    <el-option label="系统管理员 (ADMIN)" value="ADMIN" />
                  </el-select>
                </el-form-item>
                <el-form-item label="职级" required>
                  <el-select v-model="userForm.job_grade" style="width: 100%">
                    <el-option 
                      v-for = "g in jobGradeOptions"
                      :key="g"
                      :label="g"
                      :value="g"
                    />
                  </el-select>
                </el-form-item>
                <el-form-item label="所属科室">
                  <el-select
                    v-model="userForm.department"
                    filterable
                    default-first-option
                    clearable
                    :reserve-keyword="false"
                    placeholder="请选择所属科室"
                    style="width: 100%"
                  >
                    <el-option v-for="d in departmentOptions" :key="d" :label="d" :value="d" />
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
            <el-card header="现有人员名册" shadow="never">
              <el-table :data="allUsers" border stripe style="width: 100%" height="calc(100vh - 340px)">
                <el-table-column prop="id" label="工号" min-width="90" sortable />
                <el-table-column prop="username" label="姓名" width="100">
                  <template #default="{ row }">
                    <el-input v-if="row.isEditing" v-model="row.username" size="small" />
                    <span v-else>{{ row.username }}</span>
                  </template>
                </el-table-column>
                <el-table-column prop="role" label="角色" min-width="140">
                  <template #default="{ row }">
                    <el-select v-if="row.isEditing" v-model="row.role" size="small" min-width="130">
                      <el-option v-for="r in roleOptions" :key="r.value" :label="r.label" :value="r.value" />
                    </el-select>
                    <span v-else>{{ roleLabel(row.role) }}</span>
                  </template>
                </el-table-column>
                <el-table-column prop="job_grade" label="职级" min-width="100">
                  <template #default="{ row }">
                    <el-select v-if="row.isEditing" v-model="row.job_grade" size="small" style="width: 40px">
                      <el-option v-for="g in jobGradeOptions" :key="g" :label="g" :value="g" />
                    </el-select>
                    <span v-else>{{ row.job_grade }}</span>
                  </template>
                </el-table-column>
                <el-table-column prop="department" label="所属科室" min-width="150">
                  <template #default="{ row }">
                    <el-select
                      v-if="row.isEditing"
                      v-model="row.department"
                      filterable
                      default-first-option
                      clearable
                      :reserve-keyword="false"
                      size="small"
                      placeholder="请选择所属科室"
                      style="width: 100%"
                    >
                      <el-option v-for="d in departmentOptions" :key="d" :label="d" :value="d" />
                    </el-select>
                    <span v-else>{{ row.department || '未分配' }}</span>
                  </template>
                </el-table-column>
                <el-table-column prop="password" label="密码" min-width="120" />
                <el-table-column label="操作" min-width="140" align="center" >
                  <template #default="{ row }">
                    <template v-if="!row.isEditing">
                      <el-button type="primary" link size="small" @click="startEditRow(row)">编辑</el-button>
                      <el-button type="danger" link size="small" @click="handleDeleteUser(row)">删除</el-button>
                    </template>
                    <template v-else>
                      <el-button type="success" link size="small" :loading="savingEdit" @click="saveEditRow(row)">保存</el-button>
                      <el-button type="info" link size="small" @click="cancelEditRow(row)">取消</el-button>
                    </template>
                  </template>
                </el-table-column>
              </el-table>
            </el-card>
          </el-col>

        </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { 
  getAllUsersApi, 
  createUserApi, 
  deleteUserApi,
  updateUserApi,
  getLevelDefsApi,
  getDepartmentOptionsApi
} from '../api'

const activeTab = ref('users')

// 数据源
const allUsers = ref([])

// 表单响应式绑定
const userForm = reactive({ id: '', username: '', password: '123456', job_grade: '', role: 'EMPLOYEE', department: '' })
const employeeOptions = ref([])
const jobGradeOptions = ref([])
// 两处表单共用“信息管理”中的科室字典，尚未分配人员的新科室也可以选择。
const departmentOptions = ref([])

const currentUser = ref(JSON.parse(localStorage.getItem('user_info') || '{}'))

const roleOptions = [
  { label: '普通员工', value: 'EMPLOYEE' },
  { label: '科室主任', value: 'DEPARTMENT' },
  { label: '领导', value: 'LEADER' },
  { label: '系统管理员', value: 'ADMIN' }
]
const savingEdit = ref(false)


// 批量加载所有数据
const fetchAllData = async () => {
  try {
    const [resUsers, resDepartments] = await Promise.all([getAllUsersApi(), getDepartmentOptionsApi()])
    departmentOptions.value = resDepartments.data.data || []
    // 科室在信息管理中改名后，清除新增表单尚未保存的旧选项，避免再次提交旧名称。
    if (userForm.department && !departmentOptions.value.includes(userForm.department)) {
      userForm.department = ''
    }
    if (resUsers.data && resUsers.data.code === 200) {
      const users = resUsers.data.data || []
      allUsers.value = users.sort((a, b) => {
        return String(a.id).localeCompare(String(b.id), undefined, { numeric: true })
      })
    }
  } catch (err) {
    console.error('拉取后台数据失败:', err)
    ElMessage.error(err.response?.data?.detail || '人员或科室加载失败，请刷新重试')
  }
}
defineExpose({ fetchAllData })

const fetchJobGrades = async () => {
  try{
    const res = await getLevelDefsApi()
    if (res.data?.code == 200) {
      jobGradeOptions.value = res.data?.data?.job_grade || []
    }
  }catch (err) {
    console.error('获取职级失败', err)
  }
}

// 1. 新增人员
const handleCreateUser = async () => {
  if (!userForm.id.trim() || !userForm.username.trim()) return ElMessage.warning('请填写工号和姓名！')
  // 下拉框清空时仍提交空字符串，保持现有后端“未分配科室”的处理方式。
  const department = String(userForm.department || '').trim()
  if (department.length > 255) return ElMessage.warning('科室名称不能超过255个字符')
  try {
    const res = await createUserApi({ 
        id: userForm.id.trim(), 
        username: userForm.username.trim(),
        password: userForm.password.trim(),
        role: String(userForm.role).toUpperCase(),
        job_grade: String(userForm.job_grade).toUpperCase(),
        department })
    if (res.data.code === 200) {
      ElMessage.success('人员创建成功！')
      userForm.id = ''
      userForm.username = ''
      userForm.department = ''
      fetchAllData()
    }
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '创建失败')
  }
}

//删除人员
const handleDeleteUser = async(row) => {
    try {
      const res = await deleteUserApi(row.id, currentUser.value.id)
      
      if (res.data && res.data.code === 200) {
        ElMessage.success(`已成功删除员工 ${row.username}`)
        // 3. 删除成功后，重新拉取最新的人员列表刷新页面
        fetchAllData()
      }
    } catch (err) {
      console.error('删除员工失败', err)
      ElMessage.error(err.response?.data?.detail || '删除失败，该员工有负责未完成的工作')
    }
}


// 角色值 → 中文标签（纯同步函数，直接查 roleOptions）
const roleLabel = (role) => {
  const found = roleOptions.find(r => r.value === role)
  return found ? found.label : (role || '未知角色')
}

const startEditRow = (row) => {
  row._backup = { username: row.username, role: row.role, job_grade: row.job_grade, department: row.department }
  row.isEditing = true
}
const cancelEditRow = (row) => {
  Object.assign(row, row._backup)     // 还原备份
  row.isEditing = false
}
const saveEditRow = async (row) => {
  const department = String(row.department || '').trim()
  if (department.length > 255) return ElMessage.warning('科室名称不能超过255个字符')
  savingEdit.value = true
  try {
    const res = await updateUserApi(row.id, {
      updated_by_id: currentUser.value.id,
      username: row.username,
      role: row.role,
      job_grade: row.job_grade,
      department
    })
    if (res.data?.code === 200) {
      ElMessage.success('人员信息已更新')
      row.isEditing = false
      await fetchAllData()            // 刷新列表（会重置 isEditing）
    }
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '保存失败')
  } finally { savingEdit.value = false }
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

onMounted(() => {
  fetchAllData()
  fetchEmployees()
  fetchJobGrades()
})
</script>

<style scoped>
/* 整个组件占据 100% 高度并且内部使用 flex 进行限制 */
.personnel-management-container { 
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  padding-top: 8px;
  padding-bottom: 24px; /* 增加这行：给底部留出一定空间，表格不再死死贴边 */
}

.page-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding: 0 4px;
}

.section-title {
  font-size: 15px;
  font-weight: 600;
  color: #334155;
  border-left: 4px solid #409EFF;
  padding-left: 10px;
}

/* Row 铺满剩余高度 */
.full-height-row {
  flex: 1;
  display: flex;
  overflow: hidden;
  margin-bottom: 0 !important;
}

/* 左侧栏超出允许滚动 */
.left-col {
  height: 100%;
  display: flex;
  flex-direction: column;
  border-right: 1px dashed #e2e8f0;
}

.form-body {
  overflow-y: auto;
  padding-right: 20px;
}

/* 右侧栏完全使用弹性布局给表格让出空间 */
.right-col {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.panel-header {
  font-weight: 600;
  font-size: 14px;
  color: #475569;
  margin-bottom: 16px;
}

.panel-body {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.table-body {
  overflow: hidden;
  /* 移除原有的 padding-bottom，统一由外层 container 的 padding-bottom 控制留白 */
}
</style>

