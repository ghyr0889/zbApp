<template>
  <div id="app">
    <!-- 顶部导航栏容器：使用 flex 布局强行左右分栏 -->
    <div class="header-layout" v-if="$route.path !== '/login'">
      
      <!-- 左侧：功能菜单 (加入 :ellipsis="false" 彻底禁用三个点折叠) -->
      <el-menu 
        class="left-menu"
        mode="horizontal" 
        router 
        :default-active="$route.path"
        :ellipsis="false" 
      >
        <el-menu-item index="/my-logs">📝 员工填报</el-menu-item>
        <el-menu-item index="/score-board">📊 积分统计看板</el-menu-item>
        <el-menu-item v-if="isOwner" index="/review">👑 审批工作台</el-menu-item>
        <el-menu-item v-if="isAdmin" index="/admin">⚙️ 管理后台</el-menu-item>
      </el-menu>

      <!-- 右侧：永远常显的个人信息与下拉退出 -->
      <div class="right-profile" v-if="userInfo">
        <el-dropdown @command="handleUserCommand" trigger="click">
          
          <!-- 常显触发区：直接展示头像、姓名、工号、角色 -->
          <div class="user-info-trigger">
            <el-avatar size="small" style="margin-right: 8px; background-color: #409EFF;">
              {{ userInfo.username ? userInfo.username.charAt(0) : 'U' }}
            </el-avatar>
            <span class="user-name">{{ userInfo.username }} ({{ userInfo.id }})</span>
            <el-tag size="small" :type="roleTagType" style="margin-left: 8px;" effect="dark">
              {{ roleDisplayName }}
            </el-tag>
          </div>
          
          <!-- 只有点击后才出现的下拉菜单 -->
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="logout" style="color: #F56C6C;">
                🚪 退出登录
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>

        </el-dropdown>
      </div>
    </div>

    <div class="main-body">
      <router-view />
    </div>
  </div>
</template>

<script setup>
import { ElMessage } from 'element-plus'
import { ref, computed, watchEffect } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const userInfo = ref(null)

// 动态获取并解析本地存储的用户信息
watchEffect(() => {
  const infoStr = localStorage.getItem('user_info')
  if (infoStr) {
    try {
      userInfo.value = JSON.parse(infoStr)
    } catch (e) {
      userInfo.value = null
    }
  } else {
    userInfo.value = null
  }
})

// 角色权限判断
const isAdmin = computed(() => userInfo.value?.role === 'ADMIN')
const isOwner = computed(() => {
  const role = String(userInfo.value?.role || '').toUpperCase()
  return role === 'OWNER' || role === 'LEADER'
})

// 计算属性：翻译角色名称
const roleDisplayName = computed(() => {
  if (!userInfo.value) return ''
  const role = String(userInfo.value.role).toUpperCase()
  if (role === 'ADMIN') return '管理员'
  if (role === 'OWNER' || role === 'LEADER') return '项目负责人'
  return '普通员工'
})

// 计算属性：角色标签颜色
const roleTagType = computed(() => {
  if (!userInfo.value) return 'info'
  const role = String(userInfo.value.role).toUpperCase()
  if (role === 'ADMIN') return 'danger'
  if (role === 'OWNER' || role === 'LEADER') return 'warning'
  return 'info'
})

// 统一处理下拉菜单指令
const handleUserCommand = (command) => {
  if (command === 'logout') {
    logout()
  }
}

// 退出登录逻辑
const logout = () => {
  localStorage.removeItem('user_info')
  userInfo.value = null

  ElMessage.success('已安全退出登录')
  router.push('/login')
}
</script>

<style>
body { 
  margin: 0; 
  background: #f5f7fa; 
  font-family: sans-serif; 
}

.main-body { 
  padding: 20px; 
}

/* ================= 顶部导航栏整体布局 ================= */
.header-layout {
  display: flex;
  align-items: center; /* 垂直居中 */
  background-color: #ffffff;
  border-bottom: 1px solid #dcdfe6;
}

/* 左侧菜单占据剩余的所有可用宽度 */
.left-menu {
  flex: 1; 
  border-bottom: none !important; /* 去除原本自带的底边框，防止双重边框 */
}

/* ================= 右侧用户信息 ================= */
.right-profile {
  padding: 0 20px; /* 右侧留白 */
  display: flex;
  align-items: center;
}

/* 常显区域鼠标样式 */
.user-info-trigger {
  display: flex;
  align-items: center;
  color: #303133;
  font-weight: 500;
  cursor: pointer;
  outline: none;
  padding: 5px 10px;
  border-radius: 4px;
  transition: background-color 0.3s;
}

/* 鼠标悬浮时给一点背景色反馈 */
.user-info-trigger:hover {
  background-color: #f0f2f5;
}

.user-name {
  font-size: 14px;
}
</style>
