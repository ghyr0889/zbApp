
import { createRouter, createWebHistory } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useUserStore } from '../stores/user'

// 确保这 4 个文件在 src/views/ 目录下都真实存在
import Login from '../views/Login.vue'
import MyLogs from '../views/MyLogs.vue'
import Review from '../views/Review.vue'
import ScoreBoard from '../views/ScoreBoard.vue'
import AdminPanel from '../views/AdminPanel.vue'
import WorkPackageHall from '../views/WorkPackageHall.vue'
import MyProjects from '../views/MyProjects.vue'

const routes = [
  { path: '/', redirect: '/login' },
  { path: '/login', name: 'Login', component: Login },
  { path: '/my-logs', name: 'MyLogs', component: MyLogs },
  { path: '/work-packages', name: 'WorkPackageHall', component: WorkPackageHall },
  { path: '/review', name: 'ReviewLogs', component: Review, meta: { requiresOwner: true } },
  { path: '/score-board', name: 'ScoreBoard', component: ScoreBoard },
  { path: '/admin', name: 'AdminPanel', component: AdminPanel, meta: { requiresAdmin: true}},
  { path: '/my-projects', name: 'MyProjects', component: MyProjects, meta: { requiresOwner: true } }
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

  //  如果访问的是需要管理员权限的页面 (/admin)
  if (to.meta.requiresAdmin) {
    if (userStore.isAdmin) {
      next() // 允许进入
    } else {
      ElMessage.error('权限不足！仅管理员可以访问管理后台。')
      next('/my-logs') // 拦截并重定向到员工填报页
    }
  } else if (to.meta.requiresOwner) {
    if (userStore.isOwner) {
      next()
    } else {
      ElMessage.error('权限不足！仅项目负责人可以访问审批工作台。')
      next('/my-logs')
    }
  } else {
    next()
  }
})

export default router
