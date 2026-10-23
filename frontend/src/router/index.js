
import { createRouter, createWebHistory } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useUserStore } from '../stores/user'

import Login from '../views/Login.vue'
import Review from '../views/WorkManagement/Review.vue'
import ScoreBoard from '../views/WorkManagement/ScoreBoard.vue'
import DataBoard from '../views/WorkManagement/DataBoard.vue'
import ProjectOverview from '../views/WorkManagement/ProjectOverview.vue'
import PersonalInfo from '../views/PersonalInfo.vue'
import PersonnelManagement from '../views/WorkManagement/PersonnelManagement.vue'
import AdminPanel from '../views/WorkManagement/AdminPanel.vue'
import ProjectDetail from '../views/WorkManagement/ProjectDetail.vue'

// 子路由保留原有绝对路径，旧书签和现有页面跳转无需修改。
const routes = [
  { path: '/', redirect: '/home' },
  { path: '/home', name: 'Home', component: () => import('../views/Home.vue'), meta: { layout: 'portal' } },
  { path: '/applications', name: 'Applications', redirect: { path: '/home', hash: '#application-center' } },
  { path: '/login', name: 'Login', component: Login },
  { path: '/personal-info', name: 'PersonalInfo', component: PersonalInfo, meta: { layout: 'portal' } },
  { path: '/announcements', name: 'Announcements', component: () => import('../views/WorkManagement/Announcement.vue'), meta: { layout: 'portal' } },
  {
    path: '/work',
    component: () => import('../layouts/WorkManagement.vue'),
    redirect: '/project-overview',
    meta: { module: 'work' },
    children: [
    { path: '/work-time', name: 'WorkTime', component: () => import('../views/WorkManagement/WorkTime.vue') },
    { path: '/assignments', redirect: { path: '/project-overview', query: { tab: 'employees' } }, meta: { requiresLeader: true } },
    { path: '/assignments/:userId', component: ProjectOverview, props: route => ({ viewUserId: route.params.userId }), meta: { requiresLeader: true } },
    { path: '/project-overview', name: 'ProjectOverview', component: ProjectOverview },
    { path: '/review', name: 'ReviewLogs', component: Review },
    { path: '/complete-review', redirect: '/review' },
    { path: '/score-board', name: 'ScoreBoard', component: ScoreBoard },
    { path: '/data-board', name: 'DataBoard', component: DataBoard },
    { path: '/personnel-management', name: 'PersonnelManagement', component: PersonnelManagement, meta: { requiresAdmin: true } },
    { path: '/admin-panel', name: 'AdminPanel', component: AdminPanel, meta: { requiresAdmin: true } },
    { path: '/project/:id', name: 'ProjectDetail', component: ProjectDetail },
    ]
  },
  {
    path: '/ledger',
    component: () => import('../layouts/LedgerLay.vue'),
    redirect: '/ledger/overview',
    meta: { module: 'ledger' },
    children: [
      { path: 'overview', name: 'LedgerOverview', component: () => import('../views/ledger/LedgerOverview.vue') }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(), 
  routes,
  scrollBehavior(to) {
    if (to.hash === '#application-center') {
      return new Promise(resolve => {
        requestAnimationFrame(() => requestAnimationFrame(() => {
          document.getElementById('application-center')?.scrollIntoView({ block: 'start' })
          resolve(false)
        }))
      })
    }
    return { top: 0 }
  }
})

//  全局路由前置守卫：进行权限校验
router.beforeEach(async (to, from, next) => {
  const userStore = useUserStore()

  // 刷新页面后从服务器恢复真实身份；仅有旧 user_info 缓存不能视为已登录。
  if (userStore.accessToken && !userStore.sessionChecked) {
    try { await userStore.restoreSession() }
    catch (error) {
      if (error.response?.status === 401) {
        userStore.clearUser()
        return next(to.path === '/login' ? undefined : '/login')
      }
      ElMessage.error('登录状态验证失败，请检查后端连接后刷新页面')
      return next(to.path === '/login' ? undefined : '/login')
    }
  }

  // 已登录时再次访问登录页，直接回到主页面。
  if (to.path === '/login' && userStore.isLoggedIn) return next('/home')

  // 如果访问的是未登录页面且用户没登录，重定向到登录页
  if (to.path !== '/login' && !userStore.isLoggedIn) {
    ElMessage.warning('请先登录！')
    return next(to.path === '/login' ? undefined : '/login')
  }

  if (to.meta.requiresLeader && !userStore.isLEADER) {
    ElMessage.error("仅部门领导可以查看员工工作内容")
    return next("/home")
  }

  //  如果访问的是需要管理员权限的页面
  if (to.meta.requiresAdmin) {
    if (userStore.isAdmin) {
      next() // 允许进入
    } else {
      ElMessage.error('权限不足！仅管理员可以访问该页面。')
      next('/home')
    }
  } else {
    next()
  }
})

export default router
