<template>
  <div id="app">
    <!-- 顶部导航栏容器：使用 flex 布局强行左右分栏 -->
    <div class="header-layout" v-if="$route.path !== '/login'">
      
      <!-- 品牌标识区 -->
      <div class="brand-logo">
        <span class="logo-text">综保工作管理系统</span>
      </div>

      <!-- 左侧：功能菜单 -->
      <el-menu 
        class="left-menu"
        mode="vertical" 
        router 
        :default-active="$route.path"
        :ellipsis="false" 
        active-text-color="#409EFF"
      >
        <el-menu-item index="/project-overview">
          <i class="el-icon-menu"></i>
          <span>项目总览</span>
        </el-menu-item>
        <el-menu-item index="/review">
          <i class="el-icon-s-check"></i>
          <span>审批查阅</span>
        </el-menu-item>
        <el-menu-item index="/score-board">
          <i class="el-icon-data-line"></i>
          <span>积分查看</span>
        </el-menu-item>
        <el-menu-item index="/personal-info">
          <i class="el-icon-user"></i>
          <span>个人信息</span>
        </el-menu-item>
        <el-menu-item index="/admin-panel" v-if="isAdmin">
          <i class="el-icon-setting"></i>
          <span>后台管理</span>
        </el-menu-item>
      </el-menu>
    </div>

    <!-- 右侧：永远常显的个人信息与下拉退出 -->
    <div class="right-profile" v-if="$route.path !== '/login' && userInfo">
      <el-dropdown @command="handleUserCommand" trigger="hover">
        
        <!-- 常显触发区：直接展示头像、姓名、工号、角色 -->
        <div class="user-info-trigger">
          <el-avatar size="small" class="user-avatar">
            {{ userInfo.username ? userInfo.username.charAt(0) : 'U' }}
          </el-avatar>
          <div class="user-text-info">
            <span class="user-name">{{ userInfo.username }}</span>
            <span class="user-id">ID: {{ userInfo.id }}</span>
          </div>
          <el-tag size="small" :type="roleTagType" effect="light" class="role-tag">
            {{ roleDisplayName }}
          </el-tag>
        </div>
        
        <!-- 只有点击后才出现的下拉菜单 -->
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="logout" class="logout-item">
              退出登录
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>

    <div :class="$route.path === '/login' ? 'login-body' : 'main-body'">
      <div class="page-container">
        <router-view />
      </div>
    </div>
  </div>
</template>

<script setup>
// 脚本部分保持原样，未做修改以保证逻辑稳定
import { ElMessage } from 'element-plus'
import { computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from './stores/user'

const router = useRouter()
const userStore = useUserStore()
const userInfo = computed(() => userStore.userInfo)

const isAdmin = computed(() => userStore.isAdmin)
const isLEADER = computed(() => userStore.isLEADER)

const roleDisplayName = computed(() => {
  if (!userInfo.value) return ''
  const role = String(userInfo.value.role).toUpperCase()
  if (role === 'ADMIN') return '管理员'
  if (role === 'LEADER') return '领导（部门主管、项目负责人）'
  if (role === 'DEPARTMENT') return '科室'
  return '普通员工'
})

const roleTagType = computed(() => {
  if (!userInfo.value) return 'info'
  const role = String(userInfo.value.role).toUpperCase()
  if (role === 'ADMIN') return 'danger'
  if (role === 'LEADER') return 'warning'
  if (role === 'DEPARTMENT') return 'success'
  return 'info'
})

const handleUserCommand = (command) => {
  if (command === 'logout') {
    logout()
  }
}

const logout = () => {
  userStore.clearUser()
  ElMessage.success('已安全退出登录')
  router.push('/login')
}
</script>

<style>
/* ================= 基础重置与全局背景 ================= */
body { 
  margin: 0; 
  background-color: #f0f2f5; 
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', '微软雅黑', Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
}

.main-body { 
  margin-left: 240px;
  padding-top: 64px;
  min-height: 100vh;
  box-sizing: border-box;
}

.page-container {
  padding: 24px;
}

.login-body {
  min-height: 100vh;
}

/* ================= 左侧导航栏整体布局 ================= */
.header-layout {
  position: fixed;
  left: 0;
  top: 0;
  bottom: 0;
  z-index: 1001;
  width: 240px;
  background-color: #ffffff;
  box-shadow: 2px 0 8px 0 rgba(29, 35, 41, 0.05);
  display: flex;
  flex-direction: column;
}

/* 品牌 Logo 区域 */
.brand-logo {
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  font-weight: 600;
  color: #303133;
  border-bottom: 1px solid #f0f2f5;
  background-color: #ffffff;
}

.logo-icon {
  margin-right: 8px;
  font-size: 22px;
}

.logo-text {
  letter-spacing: 1px;
}

/* 左侧菜单 */
.left-menu {
  flex: 1;
  width: 100%;
  border-right: none !important;
}

.el-menu-item {
  margin: 4px 12px;
  border-radius: 8px;
  height: 48px;
  line-height: 48px;
}

.el-menu-item.is-active {
  background-color: #e6f1fc !important;
  font-weight: bold;
}

.el-menu-item:hover {
  background-color: #f5f7fa !important;
}

/* ================= 右侧顶部栏 ================= */
.right-profile {
  position: fixed;
  top: 0;
  left: 240px;
  right: 0;
  height: 64px;
  padding: 0 24px;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  background-color: #ffffff;
  box-shadow: 0 1px 4px rgba(0, 21, 41, 0.08);
  z-index: 1000;
}

/* 常显区域鼠标样式 */
.user-info-trigger {
  display: flex;
  align-items: center;
  padding: 6px 12px;
  border-radius: 24px;
  cursor: pointer;
  transition: all 0.3s ease;
  border: 1px solid transparent;
}

.user-info-trigger:hover {
  background-color: #f5f7fa;
  border-color: #e4e7ed;
}

.user-avatar {
  background: linear-gradient(135deg, #409EFF 0%, #53a8ff 100%);
  color: #fff;
  font-weight: bold;
}

.user-text-info {
  display: flex;
  flex-direction: column;
  margin-left: 10px;
  margin-right: 12px;
  line-height: 1.2;
}

.user-name {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}

.user-id {
  font-size: 12px;
  color: #909399;
  margin-top: 2px;
}

.role-tag {
  border-radius: 12px;
  padding: 0 10px;
}

.logout-item {
  color: #F56C6C;
  font-weight: 500;
}
.logout-item:hover {
  background-color: #fef0f0 !important;
  color: #f56c6c !important;
}
</style>