<!-- xiangmu/frontend/src/views/Login.vue -->
<template>
  <div class="login-container">
    <el-card class="login-card" shadow="always">
      <div class="login-header">
        <h2>综保工作管理系统</h2>
      </div>

      <!-- 1. 新增：登录身份切换卡片 -->
      <el-tabs v-model="activeTab" stretch>
        <el-tab-pane label="员工登录" name="employee"></el-tab-pane>
        <el-tab-pane label="管理员登录" name="admin"></el-tab-pane>
      </el-tabs>

      <!-- 表单区域稍微加一点上边距 -->
      <el-form :model="form" @keyup.enter="handleLogin" style="margin-top: 15px;">
        <el-form-item prop="user_id" required>
          <el-input
            v-model="form.user_id" autocomplete="username" aria-label="工号"
            placeholder="请输入您的工号 ID"
            clearable
          />
        </el-form-item>

        <el-form-item prop="password" required>
          <el-input
            v-model="form.password" autocomplete="current-password" aria-label="密码"
            type="password"
            placeholder="请输入密码"
            show-password
          />
        </el-form-item>

        <!-- 按钮文字根据当前选择的 Tab 动态改变 -->
        <el-button
          type="primary"
          class="login-btn"
          :loading="loading"
          @click="handleLogin"
        >
          {{ activeTab === 'employee' ? '员工登录' : '管理员登录' }}
        </el-button>
      </el-form>
      <div v-if="$route.path === '/login'" class="login-footer">
        默认密码为123456
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useUserStore } from '../stores/user'

// 注意：你需要确保 api.js 中导出了 userLoginApi 和 adminLoginApi。
// 如果你没有在 api.js 中定义它们，请参考下方说明进行添加。
import { userLoginApi, adminLoginApi } from '../api' 

const router = useRouter()
const loading = ref(false)
const userStore = useUserStore()

//2. 新增：记录当前选中的登录身份，默认为员工（employee）
const activeTab = ref('employee')

const form = reactive({
  user_id: '',
  password: ''
})

const handleLogin = async () => {
  if (!form.user_id || !form.user_id.trim() || !form.password || !form.password.trim()) {
    return ElMessage.warning('请输入工号和密码！')
  }

  loading.value = true
  try {
    const payload = {
      user_id: form.user_id.trim(),
      password: form.password.trim()
    }

    let res;
    // 3. 新增：根据当前选中的角色，调用不同的后端接口
    if (activeTab.value === 'employee') {
      res = await userLoginApi(payload) // 调用员工登录接口
    } else {
      res = await adminLoginApi(payload) // 调用管理员登录接口
    }

    if (res.data.code === 200) {
      if (!res.data.access_token) throw new Error('登录接口未返回凭证，请确认后端已更新')
      ElMessage.success(`${activeTab.value === 'employee' ? '员工' : '管理员'}登录成功`)
      const user = res.data.data
      // 先保存令牌，再更新用户；后续待办等请求才能携带本次登录凭证。
      userStore.setUser(user, res.data.access_token)
      router.replace('/home')
    }
  } catch (error) {
    console.error('登录异常:', error)
    // 后端会在权限校验不通过时返回 403 "当前账号没有权限登录该入口"，这里会被捕捉并提示给用户
    const errorMsg = error.response?.data?.detail || error.message || '登录失败，请检查工号、密码及登录身份'
    ElMessage.error(errorMsg)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background-color: #f0f2f5;
}
.login-card {
  width: 400px;
  border-radius: 8px;
}
.login-header {
  text-align: center;
  margin-bottom: 20px;
}
.login-header h2 {
  margin: 0;
  color: #303133;
}
.subtitle {
  color: #909399;
  font-size: 13px;
  margin-top: 8px;
}
.login-btn {
  width: 100%;
  margin-top: 10px;
}
.login-footer {
  margin-top: 14px;
  text-align: left;
  font-size: 13px;
  color: #858586;
}
.test-account-box {
  margin-top: 25px;
  padding: 12px;
  background-color: #f4f4f5;
  border-radius: 6px;
  font-size: 12px;
  color: #606266;
}
.tip-title {
  font-weight: bold;
  margin: 0 0 6px 0;
}
.test-account-box p {
  margin: 4px 0;
}
code {
  background-color: #e9e9eb;
  padding: 2px 4px;
  border-radius: 3px;
  color: #409eff;
}
</style>
