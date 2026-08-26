
import { createRouter, createWebHistory } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useUserStore } from '../stores/user'

import Login from '../views/Login.vue'
import Review from '../views/Review.vue'
import ScoreBoard from '../views/ScoreBoard.vue'
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
  { path: '/score-board', name: 'ScoreBoard', component: ScoreBoard },
  { path: '/personal-info', name: 'PersonalInfo', component: PersonalInfo },
  { path: '/personnel-management', name: 'PersonnelManagement', component: PersonnelManagement, meta: { requiresAdmin: true } },
  { path: '/admin-panel', name: 'AdminPanel', component: AdminPanel, meta: { requiresAdmin: true } },
  { path: '/project/:id', name: 'ProjectDetail', component: ProjectDetail }
]

const router = createRouter({
  history: createWebHistory(), 
  routes
})

//  全局路由前置守卫：进行权限校验
router.beforeEach((to, from, next) => {
  const userStore = useUserStore()

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
