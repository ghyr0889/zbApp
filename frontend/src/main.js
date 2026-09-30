import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import { createPinia } from 'pinia'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'
import { startAutoUpdate } from './autoUpdate'
import { setUnauthorizedHandler } from './api'
import { useUserStore } from './stores/user'


const app = createApp(App)
app.use(createPinia())
// 统一处理凭证过期，立即清除用户及待办缓存，避免页面继续使用旧身份。
setUnauthorizedHandler(() => {
  useUserStore().clearUser()
  if (router.currentRoute.value.path !== '/login') router.replace('/login')
})
app.use(router)
app.use(ElementPlus, { locale: zhCn })
app.mount('#app')

// 生产环境：轮询 /version.json，发现新版本自动刷新（开发环境无需）
if (import.meta.env.PROD) {
  startAutoUpdate()
}
