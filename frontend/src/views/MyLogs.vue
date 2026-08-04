<!-- xiangmu/frontend/src/views/MyLogs.vue -->
<template>
  <div class="my-logs-container">
    <!-- 顶部页面切换标签 -->
    <el-tabs v-model="activeTab" type="border-card" class="custom-tabs">
      <!-- ================= 页面一：工作填报区 ================= -->
      <el-tab-pane label="📝 任务处理与日志填报" name="filling">
        <el-row :gutter="20">
          
          <!-- 左侧：我的工作包 -->
          <el-col :span="14">
            <el-card shadow="hover" class="assigned-card">
              <template #header>
                <div class="card-header">
                  <span>📌 我的工作包（按节点排序）</span>
                  <el-button type="text" @click="fetchMyAssignedTasks">🔄 刷新任务</el-button>
                </div>
              </template>

              <el-table 
                v-if="assignedTasks.length > 0"
                :data="sortedMyAssignments" 
                border 
                stripe 
                style="width: 100%"
                height="500"
              >
                <el-table-column prop="project_name" label="项目" width="100" />
                <el-table-column prop="work_package_name" label="工作包" />
                <el-table-column prop="score" label="分值" width="80" align="center">
                  <template #default="{ row }">
                    <span class="score-text">🏆 {{ row.score }}</span>
                  </template>
                </el-table-column>
                <el-table-column label="节点要求" width="160">
                  <template #default="{ row }">
                    <el-tag type="danger" effect="plain" v-if="row.deadline">
                      ⏰ {{ row.deadline }}
                    </el-tag>
                    <span v-else class="tip-text">无</span>
                  </template>
                </el-table-column>
                <el-table-column label="操作" width="160" align="center" fixed="right">
                  <template #default="{ row }">
                    <el-button type="success" size="small" @click="selectAssignedTask(row)">
                      📝 填报此项
                    </el-button>
                    <el-button type="warning" size="small" plain @click="openTransferDialog(row)">📤 转办</el-button>
                  </template>
                </el-table-column>
              </el-table>
              
              <el-empty v-else description="暂无分配的任务，您可以在右侧手动选择" :image-size="70" />
            </el-card>
          </el-col>

          <!-- 右侧：填报工作日志申请 -->
          <el-col :span="10">
            <el-card shadow="hover">
              <template #header>
                <div class="card-header">
                  <span>📝 填报工作日志申请</span>
                </div>
              </template>

              <el-form :model="form" label-position="top">
                <el-form-item label="选择项目 / 工作类型 / 工作包" required>
                  <el-cascader
                    v-model="selectedPath"
                    :options="cascadeOptions"
                    placeholder="请选择或从左侧任务列表一键导入"
                    style="width: 100%"
                    @change="handleCascadeChange"
                    clearable
                  />
                </el-form-item>

                <el-form-item label="对应工作包分值">
                  <el-tag type="success" size="large" v-if="selectedWorkPackageInfo.score !== null">
                    🏆 {{ selectedWorkPackageInfo.score }} 分
                  </el-tag>
                  <span v-else class="tip-text">选择工作包后自动显示</span>
                </el-form-item>

                <el-form-item label="节点完成要求">
                  <el-alert
                    v-if="selectedWorkPackageInfo.deadline"
                    :title="selectedWorkPackageInfo.deadline"
                    type="info"
                    :closable="false"
                    show-icon
                  />
                  <span v-else class="tip-text">选择工作包后自动显示节点要求</span>
                </el-form-item>

                <el-form-item label="具体工作完成情况" required>
                  <el-input
                    v-model="form.content"
                    type="textarea"
                    :rows="5"
                    placeholder="参照节点要求，填写完成的具体工作进展..."
                  />
                </el-form-item>

                <el-button
                  type="primary"
                  style="width: 100%"
                  size="large"
                  :loading="submitting"
                  :disabled="!form.work_package_name"
                  @click="handleSubmit"
                >
                  🚀 提交审核给所属项目负责人
                </el-button>
              </el-form>
            </el-card>
          </el-col>
        </el-row>
      </el-tab-pane>

      <!-- ================= 页面二：审核记录区 ================= -->
      <el-tab-pane label="📋 我的日志提交与审核记录" name="records">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span>📋 历史提交与审核状态</span>
              <el-button type="primary" plain @click="fetchMyLogs">🔄 刷新记录</el-button>
            </div>
          </template>

          <el-table :data="logList" stripe style="width: 100%" v-loading="loadingLogs" height="600">
            <el-table-column prop="project_name" label="项目" width="120" />
            <el-table-column prop="work_package_name" label="工作包" show-overflow-tooltip />
            <el-table-column prop="score_earned" label="分值" width="90" align="center">
              <template #default="{ row }">
                <span class="score-text">+{{ row.score_earned }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="120" align="center">
              <template #default="{ row }">
                <el-tag v-if="row.status === 'PENDING'" type="warning" effect="dark">待审核</el-tag>
                <el-tag v-else-if="row.status === 'APPROVED'" type="success" effect="dark">已通过</el-tag>
                <el-tag v-else-if="row.status === 'REJECTED'" type="danger" effect="dark">被驳回</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="review_comment" label="反馈原因/意见" show-overflow-tooltip />
          </el-table>
        </el-card>
      </el-tab-pane>

       <!-- ================= 页面四：任务流转收件箱 ================= -->
      <el-tab-pane label="📫 任务流转收件箱" name="inbox">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span>📫 待处理的任务转办申请</span>
              <el-button type="primary" plain @click="fetchIncomingTransfers">🔄 刷新收件箱</el-button>
            </div>
          </template>

          <el-table :data="incomingTransfers" stripe border style="width: 100%" height="600">
            <el-table-column prop="task_name" label="工作包名称" min-width="180" />
            <el-table-column prop="from_user_id" label="发起人工号" width="120" align="center" />
            <el-table-column prop="created_at" label="申请时间" width="180" align="center" />
            <el-table-column label="操作" width="180" align="center" fixed="right">
              <template #default="{ row }">
                <el-button type="success" size="small" @click="handleTransfer(row.id, 'ACCEPT')">接受</el-button>
                <el-button type="danger" size="small" plain @click="handleTransfer(row.id, 'REJECT')">拒绝</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-tab-pane>

      <!-- ================= 页面三：所有工作包大厅 ================= -->
      <el-tab-pane label="📚 所有工作包大厅" name="all_work_packages">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span>📚 全局工作包总览 (可查阅所有项目和任务配置)</span>
              <el-button type="primary" plain @click="fetchAllWorkPackages">🔄 刷新库</el-button>
            </div>
          </template>

          <el-table :data="allWorkPackages" stripe border style="width: 100%" v-loading="loadingAllWorkPackages" height="600">
            <el-table-column prop="project_name" label="所属项目" width="120" />
            <el-table-column prop="category_name" label="工作类型" width="150" />
            <el-table-column prop="name" label="工作包名称" min-width="180" show-overflow-tooltip />
            <el-table-column prop="assignee_name" label="负责员工" width="150" align="center">
              <template #default="{ row }">
                <span v-if="row.assignee_id" style="color: #67c23a; font-weight: bold;">
                  {{ row.assignee_name || row.assignee_id }}（{{ row.assignee_id }}）
                </span>
                <span v-else class="tip-text">未指定</span>
              </template>
            </el-table-column>
            <el-table-column prop="score" label="预设分值" width="100" align="center">
              <template #default="{ row }">
                <span style="color: #67c23a; font-weight: bold;">🏆 {{ row.score }}</span>
              </template>
            </el-table-column>
            <el-table-column label="节点要求" width="200">
              <template #default="{ row }">
                <el-tag type="info" effect="plain" v-if="row.deadline">
                  ⏰ {{ row.deadline }}
                </el-tag>
                <span v-else class="tip-text">无节点要求</span>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-tab-pane>

          <!-- 转办选择接收人弹窗 -->
      <el-dialog v-model="transferDialogVisible" title="任务移交申请" width="400px">
        <el-form label-position="top">
          <el-form-item label="选择接收人" required>
            <el-select v-model="selectedTargetUser" filterable placeholder="请搜索并选择同事" style="width: 100%">
              <!-- employeeOptions 可以复用你之前写的获取所有用户的逻辑 -->
              <el-option v-for="user in employeeOptions" :key="user.id" :label="user.name" :value="user.id" />
            </el-select>
          </el-form-item>
        </el-form>
        <template #footer>
          <span class="dialog-footer">
            <el-button @click="transferDialogVisible = false">取消</el-button>
            <el-button type="primary" @click="confirmTransfer">发送申请</el-button>
          </span>
        </template>
      </el-dialog>

    </el-tabs>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { 
  getCascadeOptionsApi, 
  createLogApi, 
  getMyLogsApi, 
  getMyAssignedWorkPackagesApi, 
  getScoreBoardApi,
  getPublicWorkPackagesApi,
  initiateTransferApi,
  getIncomingTransfersApi,
  processTransferApi,
  getAllUsersApi
} from '../api'

const currentUser = ref(null)
const assignedTasks = ref([])
const cascadeOptions = ref([])
const selectedPath = ref([])
const logList = ref([])
const submitting = ref(false)
const loadingLogs = ref(false)

const scorePeriod = ref('month')
const scoreBoardData = reactive({
  total_score: 0,
  details: []
})

const selectedWorkPackageInfo = reactive({
  score: null,
  deadline: ''
})

const form = reactive({
  work_package_name: '',
  content: ''
})

onMounted(() => {
  const userInfoStr = localStorage.getItem('user_info')
  if (userInfoStr) {
    currentUser.value = JSON.parse(userInfoStr)
  }
  fetchCascadeOptions()
  if (currentUser.value && currentUser.value.id) {
    fetchMyAssignedTasks()
    fetchMyLogs()
    fetchScoreBoard()
    fetchIncomingTransfers()
    fetchAllWorkPackages()
  }
})

const fetchMyAssignedTasks = async () => {
  try {
    const res = await getMyAssignedWorkPackagesApi(String(currentUser.value.id))
    assignedTasks.value = res.data.data || []
  } catch (err) {
    console.error('获取指派任务失败:', err)
  }
}

const selectAssignedTask = (task) => {
  selectedPath.value = [task.project_name, task.category_name, task.work_package_name]
  form.work_package_name = task.work_package_name
  selectedWorkPackageInfo.score = task.score
  selectedWorkPackageInfo.deadline = task.deadline
  ElMessage.success(`已切换至：${task.work_package_name}`)
}

const fetchCascadeOptions = async () => {
  const userInfoStr = localStorage.getItem('user_info')
  const userInfo = userInfoStr ? JSON.parse(userInfoStr) : null
  
  if (!userInfo || !userInfo.id) return

  try {
    // 带上当前登录员工的 ID 请求可填报选项
    const res = await getCascadeOptionsApi(userInfo.id)
    if (res && res.data && res.data.code === 200) {
      cascadeOptions.value = res.data.data || []
    }
  } catch (err) {
    console.error('获取工作包级联选项失败:', err)
  }
}

const handleCascadeChange = (val) => {
  if (!val || val.length < 3) {
    form.work_package_name = ''
    selectedWorkPackageInfo.score = null
    selectedWorkPackageInfo.deadline = ''
    return
  }
  const [projectName, categoryName, workPackageName] = val
  form.work_package_name = workPackageName

  const project = cascadeOptions.value.find(item => item.value === projectName)
  const category = project?.children?.find(item => item.value === categoryName)
  const workPackage = category?.children?.find(item => item.value === workPackageName)

  if (workPackage) {
    selectedWorkPackageInfo.score = workPackage.score
    selectedWorkPackageInfo.deadline = workPackage.deadline
  }
}

const fetchScoreBoard = async () => {
  if (!currentUser.value || !currentUser.value.id) return
  try {
    const res = await getScoreBoardApi(String(currentUser.value.id), scorePeriod.value)
    scoreBoardData.total_score = res.data.data.total_score
    scoreBoardData.details = res.data.data.details || []
  } catch (err) {
    console.error('获取积分看板失败:', err)
  }
}

const fetchMyLogs = async () => {
  loadingLogs.value = true
  try {
    const res = await getMyLogsApi(String(currentUser.value.id))
    logList.value = res.data.data || []
  } catch (err) {
    console.error(err)
  } finally {
    loadingLogs.value = false
  }
}

const handleSubmit = async () => {
  if (!form.work_package_name) return ElMessage.warning('请选择关联的工作包！')
  if (!form.content.trim()) return ElMessage.warning('请填写具体工作内容！')

  submitting.value = true
  try {
    // 🔑 修正 1：必须用 const res 接收接口返回值！
    const res = await createLogApi({
      user_id: String(currentUser.value.id),
      work_package_name: String(form.work_package_name),
      content: form.content.trim(),
      score_earned: form.score_earned || 0  // 🔑 修正 2：把选中的积分分值传给后端
    })

    // 现在 res 变量存在了，判断逻辑可以正常运行
    if (res && res.data && res.data.code === 200) {
      ElMessage.success('工作日志已成功提交！')
      
      // 清空表单
      form.content = ''
      form.work_package_name = ''
      selectedPath.value = []
      selectedWorkPackageInfo.score = null
      selectedWorkPackageInfo.deadline = ''

      // 重新拉取日志列表 & 指派列表 & 级联选择器（已填报的任务会自动消失）
      if (typeof fetchMyLogs === 'function') fetchMyLogs()
      if (typeof fetchMyAssignedTasks === 'function') fetchMyAssignedTasks()
      if (typeof fetchCascadeOptions === 'function') fetchCascadeOptions()
    } else {
      ElMessage.error(res?.data?.message || '提交失败')
    }
  } catch (err) {
    console.error('提交日志失败:', err)
    ElMessage.error('提交失败，请检查网络或后端服务！')
  } finally {
    submitting.value = false
  }
}

/// 1. 更强大的日期提取工具（兼容 2026-08-05, 2026-8-5, 2026/08/15, 2026年8月15日 等各种格式）
const parseDateForSort = (dateStr) => {
  if (!dateStr) return Infinity // 如果没写时间，给一个无限大的值，排到最后面
  
  // 智能抓取连续的 年、月、日 数字
  const match = String(dateStr).match(/(\d{4})[-/年]?(\d{1,2})[-/月]?(\d{1,2})/)
  
  if (match) {
    // 强制拼接为标准的 YYYY/MM/DD 格式并转为真实的时间戳 (毫秒数)
    const standardDateStr = `${match[1]}/${match[2]}/${match[3]}`
    return new Date(standardDateStr).getTime()
  }
  
  return Infinity // 如果提取不到任何日期数字，排到最后
}

// 2. 核心排序：使用真实数学减法
const sortedMyAssignments = computed(() => {
  if (!assignedTasks.value || !Array.isArray(assignedTasks.value)) {
    return []
  }
  
  return [...assignedTasks.value].sort((a, b) => {
    const timeA = parseDateForSort(a?.deadline)
    const timeB = parseDateForSort(b?.deadline)
    
    // 真实的数学减法：时间戳小的（离现在越近的日期）排在前面
    return timeA - timeB 
  })
})
const selectedCascadePath = ref([])

// ====== 修改后的所有工作包拉取逻辑 ======
const allWorkPackages = ref([])
const loadingAllWorkPackages = ref(false)

const fetchAllWorkPackages = async () => {
  loadingAllWorkPackages.value = true
  try {
    // 🔑 使用公开接口拉取数据
    const res = await getPublicWorkPackagesApi()
    if (res.data && res.data.code === 200) {
      allWorkPackages.value = res.data.data || []
    }
  } catch (err) {
    console.error('获取所有工作包失败:', err)
  } finally {
    loadingAllWorkPackages.value = false
  }
}

// ======================== 任务转办功能逻辑 ========================
const transferDialogVisible = ref(false)
const selectedTargetUser = ref('')
const currentTransferTask = ref(null)
const employeeOptions = ref([])
const incomingTransfers = ref([])

// 获取员工列表供下拉选择 (已剔除自己)
const fetchAllUsers = async () => {
  try {
    const res = await getAllUsersApi()
    if (res.data && res.data.code === 200) {
      const users = res.data.data || []
      employeeOptions.value = users
        .filter(u => String(u.id) !== String(currentUser.value.id)) // 不能转给自己
        .map(u => ({ id: u.id, name: `${u.full_name || u.username} (${u.id})` }))
    }
  } catch (err) {
    console.error('获取员工列表失败:', err)
  }
}

// 打开转办弹窗
const openTransferDialog = async (row) => {
  currentTransferTask.value = row
  selectedTargetUser.value = ''
  transferDialogVisible.value = true
  if (employeeOptions.value.length === 0) {
    await fetchAllUsers() // 如果还没有加载名单，动态加载一次
  }
}

// 确认发送转办申请
const confirmTransfer = async () => {
  if (!selectedTargetUser.value) return ElMessage.warning('请选择接收人')
  try {
    const res = await initiateTransferApi({
      task_id: currentTransferTask.value.task_id,
      task_name: currentTransferTask.value.work_package_name,
      from_user_id: String(currentUser.value.id),
      to_user_id: selectedTargetUser.value
    })
    if (res.data.code === 200) {
      ElMessage.success('转办申请已发送，等待对方接受')
      transferDialogVisible.value = false
    }
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '发送失败')
  }
}

// 拉取发给我的待办申请
const fetchIncomingTransfers = async () => {
  if (!currentUser.value || !currentUser.value.id) return
  try {
    const res = await getIncomingTransfersApi(String(currentUser.value.id))
    if (res.data.code === 200) {
      incomingTransfers.value = res.data.data || []
    }
  } catch (err) {
    console.error('获取流转收件箱失败', err)
  }
}

// 处理（接受/拒绝）转办申请
const handleTransfer = async (transferId, action) => {
  try {
    const res = await processTransferApi(transferId, action)
    if (res.data.code === 200) {
      ElMessage.success(action === 'ACCEPT' ? '已接受该任务包！' : '已拒绝该任务包')
      fetchIncomingTransfers() // 刷新收件箱
      if (action === 'ACCEPT') {
        fetchMyAssignedTasks() // 刷新我的工作包列表，接受的任务会出现在左侧
      }
    }
  } catch (err) {
    ElMessage.error('操作失败')
  }
}

const activeTab = ref('filling')
</script>

<style scoped>
.my-logs-container { padding: 20px; }
.card-header { display: flex; justify-content: space-between; align-items: center; font-weight: bold; }
.assigned-card { border-left: 5px solid #409eff; }
.scoreboard-card { border-left: 5px solid #67c23a; }
.task-item-card { background-color: #f8fafc; border-radius: 6px; }
.task-title { margin-bottom: 10px; font-size: 14px; }
.task-detail p { margin: 4px 0; font-size: 13px; color: #606266; }
.score-text { color: #67c23a; font-weight: bold; }
.time-req { background: #eef5fe; padding: 6px; border-radius: 4px; font-size: 12px !important; color: #409eff !important; }
.apply-btn { width: 100%; margin-top: 10px; }
.tip-text { color: #909399; font-size: 13px; }
.score-summary { text-align: center; padding: 10px 0; }
</style> 

