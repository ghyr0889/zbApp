<!-- 应用中心 -->
<template>
  <main class="applications-page">
    <h1>应用中心</h1>
    <div class="application-grid">
      <el-card shadow="hover" class="application-card">
        <div class="application-heading">
          <div class="application-icon time-icon" aria-hidden="true"><el-icon><Clock /></el-icon></div>
          <h2>工时管理</h2>
        </div>
        <p>工作项计时、工时记录及相关工作管理功能</p>
        <router-link to="/work" class="application-link">进入应用 →</router-link>
      </el-card>
      <el-card shadow="hover" class="application-card">
        <div class="application-heading">
          <div class="application-icon ledger-icon" aria-hidden="true"><el-icon><Document /></el-icon></div>
          <h2>台账系统</h2>
        </div>
        <p>台账信息查询与管理</p>
        <!-- 进入台账入口页，由该页携带登录令牌跳转到独立的台账管理系统。 -->
        <router-link to="/ledger" class="application-link">进入应用 →</router-link>
      </el-card>
    </div>
  </main>
</template>

<script setup>
// 使用现有组件库的矢量图标，避免依赖未加载的图标字体。
import { Clock, Document } from '@element-plus/icons-vue'
</script>

<style scoped>
.applications-page { width: calc(100% - 48px); max-width: 1440px; margin: 24px auto; padding: 28px 36px 40px; box-sizing: border-box; background: #fff; border-radius: 8px; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08); }
h1 { font-size: 22px; color: #303133; margin: 0 0 24px; padding-bottom: 20px; border-bottom: 1px solid #eee; }
.application-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 24px; }
.application-card { border: none; border-radius: 10px; box-shadow: 0 3px 16px rgba(0, 0, 0, 0.08); }
.application-card :deep(.el-card__body) { padding: 28px; }
.application-heading { display: flex; align-items: center; gap: 12px; }
.application-icon { width: 44px; height: 44px; border-radius: 50%; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.application-icon .el-icon { color: #fff; font-size: 24px; }
.time-icon { background: #2196ff; }
.ledger-icon { background: #00c9b1; }
h2 { margin: 0; font-size: 18px; color: #303133; }
p { color: #909399; font-size: 14px; line-height: 1.8; margin: 24px 0 32px; }
.application-link { display: inline-block; color: #409eff; text-decoration: none; padding: 7px 0; }
.application-link:hover { text-decoration: underline; }
@media (max-width: 700px) { .application-grid { grid-template-columns: 1fr; } .applications-page { width: calc(100% - 24px); padding: 20px 16px; } }
</style>
