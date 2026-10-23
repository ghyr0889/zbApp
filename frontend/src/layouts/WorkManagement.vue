<!-- 工时管理菜单 -->
<template>
  <div class="module-layout">
    <aside class="module-sidebar" aria-label="工作管理导航">
      
      <!-- 品牌标识区 -->
      <div class="brand-logo">
        <span class="logo-text">工时管理</span>
      </div>

      <p class="sidebar-group-label">工作空间</p>
      <!-- 左侧：功能菜单 -->
      <el-menu 
        class="left-menu"
        mode="vertical" 
        router 
        :default-active="$route.path.startsWith('/assignments') ? '/project-overview' : $route.path"
        :ellipsis="false" 
        active-text-color="#409EFF"
      >
        <el-menu-item index="/project-overview">
          <el-icon aria-hidden="true"><Grid /></el-icon>
          <span>项目总览</span>
        </el-menu-item>
        <el-menu-item index="/review">
          <el-icon aria-hidden="true"><Checked /></el-icon>
          <!-- 红点锚在文字上（不是按钮上），所以放进这个 span 里 -->
          <span class="menu-label">
            审批查阅
            <el-badge
              v-if="pendingTotal"
              :value="pendingTotal"
              :max="99"
              class="menu-badge"/>
          </span>
        </el-menu-item>
        <el-menu-item index="/score-board">
          <el-icon aria-hidden="true"><TrendCharts /></el-icon>
          <span>积分查看</span>
        </el-menu-item>
        <el-menu-item index="/work-time">
          <el-icon aria-hidden="true"><Clock /></el-icon>
          <span>工时记录</span>
        </el-menu-item>
        <!-- 数据看板只对领导/管理员开放（内部两个看板都是这个口径） -->
        <el-menu-item index="/data-board" v-if="isLEADER || isAdmin">
          <el-icon aria-hidden="true"><DataAnalysis /></el-icon>
          <span>数据看板</span>
        </el-menu-item>
        <el-menu-item index="/admin-panel" v-if="isAdmin">
          <el-icon aria-hidden="true"><Setting /></el-icon>
          <span>后台管理</span>
        </el-menu-item>
      </el-menu>

      <!-- 底部菜单：个人信息、公告板 -->
      <p class="sidebar-group-label">个人中心</p>
      <el-menu
        class="left-menu bottom-menu"
        mode="vertical"
        router
        :default-active="$route.path"
        active-text-color="#409EFF"
      >
        <el-menu-item index="/announcements">
          <el-icon aria-hidden="true"><Bell /></el-icon>
          <span>公告板</span>
        </el-menu-item>

        <el-menu-item index="/personal-info">
          <el-icon aria-hidden="true"><User /></el-icon>
          <span>个人信息</span>
        </el-menu-item>
      </el-menu>
    </aside>
    <!-- 子路由对应的项目、审批、工时页面显示在右侧。 -->
    <main class="module-content">
      <router-view />
    </main>
  </div>
</template>
<script setup>
// 菜单与布局合并维护，权限和待办角标仍读取公共用户状态。
import { Grid, Checked, TrendCharts, Clock, DataAnalysis, Setting, Bell, User } from '@element-plus/icons-vue'
import { computed } from 'vue'
import { useUserStore } from '../stores/user'
import './module-layout.css'

const user = useUserStore()
const isAdmin = computed(() => user.isAdmin)
const isLEADER = computed(() => user.isLEADER)
const pendingTotal = computed(() => user.pendingTotal)
</script>
