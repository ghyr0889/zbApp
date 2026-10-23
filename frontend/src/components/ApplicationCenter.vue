<!-- 应用中心 -->
<template>
  <section id="application-center" class="application-center" aria-labelledby="application-center-title">
    <header class="application-center-heading"><h2 id="application-center-title">应用中心</h2><p>选择应用，进入工作空间。</p></header>
    <div class="application-grid">
      <el-card shadow="hover" class="application-card">
        <div class="application-heading">
          <div class="application-icon time-icon" aria-hidden="true"><el-icon><Clock /></el-icon></div>
          <h3>工时管理</h3>
        </div>
        <p>工作项计时、工时记录及相关工作管理功能</p>
        <router-link to="/work" class="application-link">进入应用 →</router-link>
      </el-card>
      <el-card shadow="hover" class="application-card">
        <div class="application-heading">
          <div class="application-icon ledger-icon" aria-hidden="true"><el-icon><Document /></el-icon></div>
          <h3>台账系统</h3>
        </div>
        <p>台账信息查询与管理</p>
        <!-- 进入台账入口页，由该页携带登录令牌跳转到独立的台账管理系统。 -->
        <router-link to="/ledger" class="application-link">进入应用 →</router-link>
      </el-card>
    </div>
  </section>
</template>

<script setup>
// 使用现有组件库的矢量图标，避免依赖未加载的图标字体。
import { Clock, Document } from '@element-plus/icons-vue'
</script>

<style scoped>
.application-center { margin-top: 28px; padding: 24px; border: 1px solid #e1eaf4; border-radius: 12px; background: #fff; scroll-margin-top: 24px; }
.application-center-heading { margin-bottom: 20px; }
.application-center-heading h2 { margin: 0; color: #303d50; font-size: 20px; }
.application-center-heading p { margin: 8px 0 0; }
.application-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 24px; }
.application-card { border: none; border-radius: 10px; box-shadow: 0 3px 16px rgba(0, 0, 0, 0.08); }
.application-card :deep(.el-card__body) { padding: 28px; }
.application-heading { display: flex; align-items: center; gap: 12px; }
.application-icon { width: 44px; height: 44px; border-radius: 50%; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.application-icon .el-icon { color: #fff; font-size: 24px; }
.time-icon { background: #2196ff; }
.ledger-icon { background: #00c9b1; }
h3 { margin: 0; font-size: 18px; color: #303133; }
p { color: #909399; font-size: 14px; line-height: 1.8; margin: 24px 0 32px; }
.application-link { display: inline-flex; align-items: center; min-height: 44px; box-sizing: border-box; color: #409eff; text-decoration: none; padding: 7px 0; }
.application-link:hover { text-decoration: underline; }
@media (max-width: 700px) { .application-grid { grid-template-columns: 1fr; } .application-center { padding: 20px 16px; } }
</style>
