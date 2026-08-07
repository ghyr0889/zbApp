<!-- xiangmu/frontend/src/views/Login.vue -->
<template>
  <div class="login-container">
    <el-card class="login-card" shadow="always">
      <div class="login-header">
        <h2>工作内容统计系统</h2>
        <p class="subtitle">请使用工号 ID 及密码登录</p >
      </div>

      <el-form :model="form" @keyup.enter="handleLogin">
        <el-form-item label="工号 / 用户 ID" prop="user_id" required>
          <el-input
            v-model="form.user_id"
            placeholder="请输入您的工号 ID"
            clearable
          />
        </el-form-item>

        <el-form-item label="密码" prop="password" required>
          <el-input
            v-model="form.password"
            type="password"
            placeholder="请输入密码"
            show-password
          />
        </el-form-item>

        <el-button
          type="primary"
          class="login-btn"
          :loading="loading"
          @click="handleLogin"
        >
          登录
        </el-button>
      </el-form>

    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { loginApi } from '../api'
import axios from 'axios'
import { useUserStore } from '../stores/user'

const router = useRouter()
const loading = ref(false)
const userStore = useUserStore()

// 统一表单数据结构，统一使用 user_id
const form = reactive({
  user_id: '',
  password: ''
})

const handleLogin = async () => {
  // 校验工号 ID 与密码是否填写
  if (!form.user_id || !form.user_id.trim() || !form.password || !form.password.trim()) {
    return ElMessage.warning('请输入工号和密码！')
  }

  loading.value = true
  try {
    const res = await loginApi({
      user_id: form.user_id.trim(),
      password: form.password.trim()
    })

    if (res.data.code === 200) {
      ElMessage.success('登录成功')
      // 将登录成功的用户凭证保存到本地
      const user = res.data.data
      userStore.setUser(user)
      axios.defaults.headers.common['Authorization'] = `Bearer ${user.id}`
      router.push('/my-logs')
    }
  } catch (error) {
    console.error('登录异常:', error)
    const errorMsg = error.response?.data?.detail || '登录失败，请检查工号和密码'
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
  margin-bottom: 25px;
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

