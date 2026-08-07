<template>
  <div class="managed-projects-container">
    <el-card shadow="hover">
      <template #header>
        <div class="card-header">
          <span>👑 我负责的项目</span>
          <el-button type="primary" plain @click="fetchProjects" :loading="loading">
            🔄 刷新数据
          </el-button>
        </div>
      </template>

      <!-- 1. 外层表格：显示项目列表 -->
      <el-table 
        :data="managedProjects" 
        border 
        style="width: 100%" 
        v-loading="loading"
        row-key="project_id"
      >
        <!-- 展开行机制：展示该项目下的工作包 -->
        <el-table-column type="expand">
          <template #default="{ row: project }">
            <div class="nested-table-container">
              <h4 style="margin-top: 0; color: #409EFF;">📦 包含的工作包明细</h4>
              
              <!-- 内层表格：工作包详情 -->
              <el-table :data="project.work_packages" border size="small" style="width: 100%">
                <el-table-column prop="category_name" label="工作类型" width="120" />
                <el-table-column prop="name" label="工作包名称" min-width="180" />
                <el-table-column prop="score" label="基础分值" width="100" align="center">
                  <template #default="{ row: pkg }">
                    <span class="score-text">🏆 {{ pkg.score }}</span>
                  </template>
                </el-table-column>
                <el-table-column label="时间节点" width="140">
                  <template #default="{ row: pkg }">
                    <el-tag type="danger" effect="plain" v-if="pkg.deadline">
                      ⏰ {{ pkg.deadline }}
                    </el-tag>
                    <span v-else class="tip-text">无节点要求</span>
                  </template>
                </el-table-column>
                
                <!-- 负责人状态展示 -->
                <el-table-column label="当前执行人" width="150" align="center">
                  <template #default="{ row: pkg }">
                    <el-tag v-if="pkg.current_assignee_name" type="success" effect="dark">
                      {{ pkg.current_assignee_name }}
                    </el-tag>
                    <el-tag v-else type="info" effect="plain">暂未指派</el-tag>
                  </template>
                </el-table-column>
                
                <!-- 核心操作列 -->
                <el-table-column label="操作" width="120" align="center" fixed="right">
                  <template #default="{ row: pkg }">
                    <el-button type="primary" size="small" @click="openAssignDialog(pkg, project.project_name)">
                      🎯 指派员工
                    </el-button>
                  </template>
                </el-table-column>
              </el-table>
            </div>
          </template>
        </el-table-column>

        <!-- 外层项目的常规列 -->
        <el-table-column prop="project_name" label="项目名称" min-width="200" />
        <el-table-column label="包含任务数" width="150" align="center">
          <template #default="{ row }">
            <el-tag type="primary" round>{{ row.work_packages?.length || 0 }} 个工作包</el-tag>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 2. 指派员工弹窗 -->
    <el-dialog v-model="assignDialogVisible" title="指派工作包执行人" width="450px" destroy-on-close>
      <el-alert 
        :title="`当前操作工作包：${currentOperatingPkg?.name}`" 
        type="info" 
        :closable="false" 
        style="margin-bottom: 20px;"
      />
      
      <el-form label-position="top">
        <el-form-item label="选择负责员工 (包含自己)" required>
          <el-select 
            v-model="selectedEmployeeId" 
            filterable 
            placeholder="请搜索并选择员工名字或工号" 
            style="width: 100%"
          >
            <el-option 
              v-for="emp in employeeOptions" 
              :key="emp.id" 
              :label="`${emp.username} (${emp.id})`" 
              :value="emp.id" 
            />
          </el-select>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="assignDialogVisible = false">取消</el-button>
          <el-button type="primary" :loading="assigning" @click="submitAssignment">确认指派</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getMyProjectsApi, taskAssignmentApi, getAllUsersApi } from '../api' // 请替换为你真实的 api 路径

// --- 响应式数据 ---
const currentUser = ref(null)
const managedProjects = ref([])
const loading = ref(false)
const employeeOptions = ref([])

// 弹窗相关
const assignDialogVisible = ref(false)
const assigning = ref(false)
const currentOperatingPkg = ref(null)
const selectedEmployeeId = ref('')

// --- 初始化获取数据 ---
onMounted(() => {
  const userInfoStr = localStorage.getItem('user_info')
  if (userInfoStr) {
    currentUser.value = JSON.parse(userInfoStr)
    fetchProjects()
    fetchAllUsers()
  } else {
    ElMessage.error('未找到登录信息，请重新登录')
  }
})

// 拉取我负责的项目
const fetchProjects = async () => {
  if (!currentUser.value?.id) return
  
  loading.value = true
  try {
    const res = await getMyProjectsApi(String(currentUser.value.id))
    if (res.data && res.data.code === 200) {
      managedProjects.value = res.data.data || []
    }
  } catch (err) {
    console.error('获取项目失败:', err)
    ElMessage.error('获取项目数据失败')
  } finally {
    loading.value = false
  }
}

// 拉取全员名单供下拉框选择
const fetchAllUsers = async () => {
  try {
    const res = await getAllUsersApi()
    if (res.data && res.data.code === 200) {
      employeeOptions.value = res.data.data || []
    }
  } catch (err) {
    console.error('获取员工名单失败:', err)
  }
}

// --- 核心操作函数 ---

// 打开指派弹窗
const openAssignDialog = (pkg, projectName) => {
  currentOperatingPkg.value = pkg
  // 如果之前已经指派过人，自动回显选中状态
  selectedEmployeeId.value = pkg.current_assignee_id || '' 
  assignDialogVisible.value = true
}

// 提交指派请求
const submitAssignment = async () => {
  if (!selectedEmployeeId.value) {
    return ElMessage.warning('请先选择要指派的员工！')
  }

  assigning.value = true
  try {
    const res = await taskAssignmentApi({
      work_package_id: Number(currentOperatingPkg.value.id),
      assignee_id: String(selectedEmployeeId.value),
      assigner_id: String(currentUser.value.id) // 记录是谁指派的
    })

    if (res.data && res.data.code === 200) {
      ElMessage.success('工作包指派成功！')
      assignDialogVisible.value = false
      fetchProjects() // 静默刷新背后的表格，展现最新负责人状态
    } else {
      ElMessage.error(res.data?.detail || '指派失败')
    }
  } catch (err) {
    console.error('指派请求失败:', err)
    ElMessage.error(err.response?.data?.detail || '网络异常，指派失败')
  } finally {
    assigning.value = false
  }
}
</script>

<style scoped>
.managed-projects-container {
  padding: 20px;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: bold;
}
.nested-table-container {
  padding: 15px 30px;
  background-color: #f8f9fa; /* 浅灰色背景，区分层级 */
  border-radius: 6px;
  border: 1px solid #ebeef5;
}
.score-text {
  color: #67c23a;
  font-weight: bold;
}
.tip-text {
  color: #909399;
  font-size: 13px;
}
</style>
