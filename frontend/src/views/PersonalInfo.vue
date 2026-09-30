<template>
  <div class="personal-info-page">
    <el-card shadow="hover">
      <template #header>
        <div class="card-header">
          <span>个人信息</span>
          <div>
            <el-button type="primary" plain @click="openChangePwd">修改密码</el-button>
            <el-button type="danger" plain @click="logout">退出登录</el-button>
          </div>
        </div>
      </template>

      <el-descriptions v-if="userInfo" :column="1" border>
        <el-descriptions-item label="姓名">
          {{ userInfo.username || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="工号">
          {{ userInfo.id || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="职级">
          {{ userInfo.job_grade || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="角色">
          {{ roleDisplayName }}
        </el-descriptions-item>
        <el-descriptions-item label="所属科室">
          {{ userInfo.department || '未分配' }}
        </el-descriptions-item>
      </el-descriptions>

      <el-empty v-else description="暂无登录信息" />
    </el-card>

    <!-- 修改密码弹窗 -->
    <el-dialog v-model="pwdDialogVisible" title="修改密码" width="420px" :close-on-click-modal="false">
      <el-form ref="pwdFormRef" :model="pwdForm" :rules="pwdRules" label-width="90px">
        <el-form-item label="旧密码" prop="oldPassword">
          <el-input v-model="pwdForm.oldPassword" type="password" show-password placeholder="请输入旧密码" />
        </el-form-item>
        <el-form-item label="新密码" prop="newPassword">
          <el-input v-model="pwdForm.newPassword" type="password" show-password placeholder="至少6位" />
        </el-form-item>
        <el-form-item label="确认新密码" prop="confirmPassword">
          <el-input v-model="pwdForm.confirmPassword" type="password" show-password placeholder="再次输入新密码" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="pwdDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="pwdLoading" @click="submitChangePwd">确认修改</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, reactive, ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useUserStore } from '../stores/user'
import { changePasswordApi, getCurrentUserApi } from '../api/index'

const router = useRouter()
const userStore = useUserStore()
const userInfo = computed(() => userStore.userInfo)

// ---- 修改密码 ----
const pwdDialogVisible = ref(false)
const pwdLoading = ref(false)
const pwdFormRef = ref()
const pwdForm = reactive({ oldPassword: '', newPassword: '', confirmPassword: '' })

const validateConfirm = (rule, value, callback) => {
  if (value !== pwdForm.newPassword) callback(new Error('两次输入的新密码不一致'))
  else callback()
}

const pwdRules = {
  oldPassword: [{ required: true, message: '请输入旧密码', trigger: 'blur' }],
  newPassword: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '新密码长度不能少于6位', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请再次输入新密码', trigger: 'blur' },
    { validator: validateConfirm, trigger: 'blur' }
  ]
}

const openChangePwd = () => {
  pwdForm.oldPassword = ''
  pwdForm.newPassword = ''
  pwdForm.confirmPassword = ''
  pwdFormRef.value?.clearValidate?.()
  pwdDialogVisible.value = true
}

const submitChangePwd = async () => {
  if (!pwdFormRef.value) return
  const valid = await pwdFormRef.value.validate().catch(() => false)
  if (!valid) return
  pwdLoading.value = true
  try {
    const res = await changePasswordApi({
      user_id: userInfo.value.id,
      old_password: pwdForm.oldPassword,
      new_password: pwdForm.newPassword
    })
    if (res.data?.code === 200) {
      ElMessage.success('密码修改成功，请重新登录')
      pwdDialogVisible.value = false
      logout()
    }
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '修改密码失败')
  } finally {
    pwdLoading.value = false
  }
}

const roleDisplayName = computed(() => {
  if (!userInfo.value) return ''
  const role = String(userInfo.value.role).toUpperCase()
  if (role === 'ADMIN') return '管理员'
  if (role === 'LEADER') return '领导（部门主管、项目负责人）'
  if (role === 'DEPARTMENT') return '科室主任'
  return '普通员工'
})

//实时拉取最新个人信息
const refreshProfile = async () => {
  const userId = userStore.userInfo?.id
  if (!userId) return

  try {
    const res = await getCurrentUserApi() // 通过登录令牌查询自己，不再传入用户 ID。
    if (res.data?.code === 200) {
      if (userStore.userInfo?.id !== userId) return
      userStore.setUser(res.data.data)
    }
  } catch (err) {
    ElMessage.error(
      err.response?.data?.detail || '获取最新个人信息失败'
    )
  }
}

onMounted(refreshProfile)

const logout = async () => {
  try {
    await userStore.logout()
    ElMessage.success('已安全退出登录')
    router.push('/login')
  } catch (error) {
    ElMessage.error('退出失败，请检查网络后重试')
  }
}
</script>

<style scoped>
.personal-info-page {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: bold;
}
</style>
