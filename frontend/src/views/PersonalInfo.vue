<template>
  <div class="personal-info-page">
    <el-card shadow="hover">
      <template #header>
        <div class="card-header">
          <span>个人信息</span>
          <el-button type="danger" plain @click="logout">退出登录</el-button>
        </div>
      </template>

      <el-descriptions v-if="userInfo" :column="1" border>
        <el-descriptions-item label="姓名">
          {{ userInfo.username || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="工号">
          {{ userInfo.id || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="角色">
          <el-tag :type="roleTagType" effect="dark">{{ roleDisplayName }}</el-tag>
        </el-descriptions-item>
      </el-descriptions>

      <el-empty v-else description="暂无登录信息" />
    </el-card>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useUserStore } from '../stores/user'

const router = useRouter()
const userStore = useUserStore()
const userInfo = computed(() => userStore.userInfo)

const roleDisplayName = computed(() => {
  if (!userInfo.value) return ''
  const role = String(userInfo.value.role).toUpperCase()
  if (role === 'ADMIN') return '管理员'
  if (role === 'OWNER' || role === 'LEADER') return '项目负责人'
  return '普通员工'
})

const roleTagType = computed(() => {
  if (!userInfo.value) return 'info'
  const role = String(userInfo.value.role).toUpperCase()
  if (role === 'ADMIN') return 'danger'
  if (role === 'OWNER' || role === 'LEADER') return 'warning'
  return 'info'
})

const logout = () => {
  userStore.clearUser()
  ElMessage.success('已安全退出登录')
  router.push('/login')
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
