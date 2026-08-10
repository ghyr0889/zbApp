
<template>
  <div class="review">
    <el-card shadow="hover">
      <template #header>
        <div class="card-header">
          <span>👑 审批查阅（待审核请求列表）</span>
          <div>
            <span class="user-badge" v-if="currentOwner">当前负责人: {{ currentOwner.username || currentOwner.id }} (ID: {{ currentOwner.id }})</span>
            <el-button type="primary" size="small" @click="fetchPendingLogs">🔄 刷新待办列表</el-button>
          </div>
        </div>
      </template>

      <!-- 待审核请求表格 -->
      <el-table :data="pendingList" v-loading="loading" stripe style="width: 100%" empty-text="暂无待审核数据">
        <el-table-column prop="id" label="申请编号" width="100" />
        <el-table-column prop="applicant_name" label="申请员工" width="110" />
        <el-table-column prop="project_name" label="所属项目" width="110" />
        <el-table-column prop="category_name" label="工作类型" width="120" />
        <el-table-column prop="work_package_name" label="工作包名称" show-overflow-tooltip />
        <el-table-column prop="node_requirement" label="节点要求" show-overflow-tooltip />
        <el-table-column prop="base_score" label="基础分值" width="90" align="center">
          <template #default="scope">
            <el-tag type="success">+{{ scope.row.base_score }} 分</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="提交时间" width="150" align="center" />
        <el-table-column label="操作" width="160" align="center" fixed="right">
          <template #default="scope">
            <el-button type="success" size="small" @click="handlePass(scope.row)">通过</el-button>
            <el-button type="danger" size="small" @click="openRejectDialog(scope.row)">驳回</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 驳回原因弹窗 -->
    <el-dialog v-model="dialogVisible" title="填写审核不通过/驳回原因" width="450px">
      <el-form :model="rejectForm">
        <el-form-item label="驳回反馈意见" required>
          <el-input
            v-model="rejectForm.review_comment"
            type="textarea"
            :rows="3"
            placeholder="请说明驳回原因..."
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="danger" :loading="submitting" @click="confirmReject">确认驳回</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getPendingLogsApi, reviewLogApi, approveReviewApi } from '../api'

const currentOwner = ref(null)
const pendingList = ref([])
const loading = ref(false)
const submitting = ref(false)
const dialogVisible = ref(false)
const currentUser = ref({ id: '' }) 

const rejectForm = reactive({
  log_id: '',
  review_comment: ''
})

// 页面加载自动触发
onMounted(() => {
  const userInfoStr = localStorage.getItem('user_info')
  if (userInfoStr) {
    currentUser.value = JSON.parse(userInfoStr)
    currentOwner.value = currentUser.value
    // 3. 只有成功拿到当前登录人的信息后，再去拉取审批列表！
    fetchPendingLogs()
  }
})

const fetchPendingLogs = async () => {
  try{
    const res = await getPendingLogsApi(currentUser.value.id)
    if (res.data.code === 200){
      pendingList.value = res.data.data || []
    }
  }catch(err){
      console.error('获取审批列表失败',err)
      ElMessage.error(err.response?.data?.detail || '获取审批列表失败')
  }
}

// 审核通过
const handlePass = (row) => {
  ElMessageBox.prompt(
    '请输入本次审核的权重系数（例如：1.0 表示不加权，1.2 表示增加 20% 积分，0.8 表示扣减 20% 积分）：', '确认通过审核',
    {
      confirmButtonText: '确定通过',
      cancelButtonText: '取消',
      inputValue: '1.0', // 默认文本框里填好 1.0
      inputPattern: /^\d+(\.\d+)?$/, // 正则校验：只能输入数字或小数
      inputErrorMessage: '权重必须是有效的数字（如 1.0, 1.5, 0.8）'
    }).then(async ({value}) => {
    try {
      const weight = parseFloat(value)
      const ownerId = currentOwner.value?.id
      await reviewLogApi(row.id, {
        decision: "pass", // 注意：如果后端这里需要布尔值，请改成 true 
        reviewer_id: String(ownerId),
        approved: true, // 如果后端不再需要 approved，可以删除这行
        remark: '审核通过',
        weight: weight
    })

    ElMessage.success('审核通过！')
    fetchPendingLogs()
    } catch (err) {
      ElMessage.error(err.response?.data?.detail || '操作失败')
    }
  }).catch(() => {})
}

// 打开驳回弹窗
const openRejectDialog = (row) => {
  rejectForm.log_id = row.id
  rejectForm.review_comment = ''
  dialogVisible.value = true
}

// 确认驳回
const confirmReject = async () => {
  if (!rejectForm.review_comment.trim()) {
    return ElMessage.warning('请填写驳回原因！')
  }
  submitting.value = true
  try {
    const ownerId = currentOwner.value?.id
    await reviewLogApi(rejectForm.log_id, {
      reviewer_id: String(ownerId),
      approved: false,
      remark: rejectForm.review_comment.trim()
    })
    ElMessage.success('已驳回该申请！')
    dialogVisible.value = false
    fetchPendingLogs()
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '驳回失败')
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.review { padding: 20px; }
.card-header { display: flex; justify-content: space-between; align-items: center; font-weight: bold; }
.user-badge { margin-right: 15px; font-size: 13px; color: #409eff; }
</style>

