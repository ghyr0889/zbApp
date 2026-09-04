import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import { createPinia } from 'pinia'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'
import { startAutoUpdate } from './autoUpdate'


const app = createApp(App)
app.use(createPinia())
app.use(router)
app.use(ElementPlus, { locale: zhCn })
app.mount('#app')

// 生产环境：轮询 /version.json，发现新版本自动刷新（开发环境无需）
if (import.meta.env.PROD) {
  startAutoUpdate()
}
