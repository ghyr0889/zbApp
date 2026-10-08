<!-- 台账系统菜单 -->
<template>
  <div class="module-layout">
  <aside class="module-sidebar">
    <div class="brand-logo">台账系统</div>
    <!-- 台账菜单单独维护，后续业务页面在这里增加入口。 -->
    <el-menu class="left-menu" router :default-active="$route.path" active-text-color="#409eff">
      <el-menu-item index="/ledger/overview">
        <el-icon><Document /></el-icon>
        <span>台账首页</span>
      </el-menu-item>
    </el-menu>
    <el-menu class="left-menu bottom-menu" router>
      <el-menu-item index="/applications">返回应用中心</el-menu-item>
    </el-menu>
  </aside>
    <!-- 台账子页面在此显示，左侧菜单保持可见。 -->
    <main class="module-content">
      <router-view />
    </main>
  </div>
</template>
<script setup>
import { Document } from '@element-plus/icons-vue'
// 本模块的布局只组织菜单和业务页面，公共导航、计时同步仍由 App 管理。
import './module-layout.css'
</script>
