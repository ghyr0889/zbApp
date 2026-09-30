
import { createRouter, createWebHistory } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useUserStore } from '../stores/user'

import Login from '../views/Login.vue'
import Review from '../views/Review.vue'
import ScoreBoard from '../views/ScoreBoard.vue'
import DataBoard from '../views/DataBoard.vue'
import ProjectOverview from '../views/ProjectOverview.vue'
import PersonalInfo from '../views/PersonalInfo.vue'
import PersonnelManagement from '../views/PersonnelManagement.vue'
import AdminPanel from '../views/AdminPanel.vue'
import ProjectDetail from '../views/ProjectDetail.vue'

const routes = [
  { path: '/', redirect: '/project-overview' },
  { path: '/login', name: 'Login', component: Login },
  { path: '/project-overview', name: 'ProjectOverview', component: ProjectOverview },
  { path: '/review', name: 'ReviewLogs', component: Review },
  // 完成申请已并入「审批查阅」页签；保留旧路径重定向，避免书签失效
  { path: '/complete-review', redirect: '/review' },
  { path: '/score-board', name: 'ScoreBoard', component: ScoreBoard },
  // 数据看板：完成情况 + 项目汇总（由「积分查看」页拆分而来）
  { path: '/data-board', name: 'DataBoard', component: DataBoard },
  { path: '/personal-info', name: 'PersonalInfo', component: PersonalInfo },
  { path: '/personnel-management', name: 'PersonnelManagement', component: PersonnelManagement, meta: { requiresAdmin: true } },
  { path: '/admin-panel', name: 'AdminPanel', component: AdminPanel, meta: { requiresAdmin: true } },
  { path: '/project/:id', name: 'ProjectDetail', component: ProjectDetail },
  { path: '/announcements', name: 'Announcements', component: () => import('../views/Announcement.vue'), },
]

const router = createRouter({
  history: createWebHistory(), 
  routes
})

//  全局路由前置守卫：进行权限校验
router.beforeEach(async (to, from, next) => {
  const userStore = useUserStore()

  // 刷新页面后从服务器恢复真实身份；仅有旧 user_info 缓存不能视为已登录。
  if (to.path !== '/login' && userStore.accessToken && !userStore.sessionChecked) {
    try { await userStore.restoreSession() }
    catch (error) {
      if (error.response?.status === 401) {
        userStore.clearUser()
        return next('/login')
      }
      ElMessage.error('登录状态验证失败，请检查后端连接后刷新页面')
      return next('/login')
    }
  }

  // 如果访问的是未登录页面且用户没登录，重定向到登录页
  if (to.path !== '/login' && !userStore.isLoggedIn) {
    ElMessage.warning('请先登录！')
    return next('/login')
  }

  //  如果访问的是需要管理员权限的页面
  if (to.meta.requiresAdmin) {
    if (userStore.isAdmin) {
      next() // 允许进入
    } else {
      ElMessage.error('权限不足！仅管理员可以访问该页面。')
      next('/project-overview')
    }
  } else {
    next()
  }
})

export default router
