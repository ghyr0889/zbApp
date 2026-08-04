// 前端路由配置

import { createRouter, createWebHistory } from 'vue-router'
import Login from '../views/Login.vue'
import MyLogs from '../views/MyLogs.vue'
import Review from '../views/Review.vue'
import ScoreBoard from '../views/ScoreBoard.vue'
S
const routes = [
  { path: '/', redirect: '/login' },
  { path: '/login', name: 'Login', component: Login },
  { path: '/my-logs', name: 'MyLogs', component: MyLogs },
  { path: '/review', name: 'Review', component: Review },
  { path: '/ScoreBoard', name: 'ScoreBoard', component: ScoreBoard }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由拦截：未登录则重定向到登录页
router.beforeEach((to, from, next) => {
  const user = localStorage.getItem('user_info')
  if (to.path !== '/login' && !user) {
    next('/login')
  } else {
    next()
  }
})

export default router
