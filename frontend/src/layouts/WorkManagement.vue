<!-- 工时管理菜单 -->
<template>
  <div class="module-layout">
    <div class="module-sidebar">
      
      <!-- 品牌标识区 -->
      <div class="brand-logo">
        <span class="logo-text">工时管理</span>
      </div>

      <!-- 左侧：功能菜单 -->
      <el-menu 
        class="left-menu"
        mode="vertical" 
        router 
        :default-active="$route.path"
        :ellipsis="false" 
        active-text-color="#409EFF"
      >
        <el-menu-item index="/project-overview">
          <i class="el-icon-menu"></i>
          <span>项目总览</span>
        </el-menu-item>
        <el-menu-item index="/review">
          <i class="el-icon-s-check"></i>
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
          <i class="el-icon-data-line"></i>
          <span>积分查看</span>
        </el-menu-item>
        <el-menu-item index="/work-time">
          <i class="el-icon-time" aria-hidden="true"></i>
          <span>工时记录</span>
        </el-menu-item>
        <!-- 数据看板只对领导/管理员开放（内部两个看板都是这个口径） -->
        <el-menu-item index="/data-board" v-if="isLEADER || isAdmin">
          <i class="el-icon-data-analysis"></i>
          <span>数据看板</span>
        </el-menu-item>
        <el-menu-item index="/admin-panel" v-if="isAdmin">
          <i class="el-icon-setting"></i>
          <span>后台管理</span>
        </el-menu-item>
      </el-menu>

      <!-- 底部菜单：个人信息、公告板 -->
      <el-menu
        class="left-menu bottom-menu"
        mode="vertical"
        router
        :default-active="$route.path"
        active-text-color="#409EFF"
      >
        <el-menu-item index="/announcements">
          <i class="el-icon-bell" aria-hidden="true"></i>
          <span>公告板</span>
        </el-menu-item>

        <el-menu-item index="/personal-info">
          <i class="el-icon-user"></i>
          <span>个人信息</span>
        </el-menu-item>
      </el-menu>
    </div>
    <!-- 子路由对应的项目、审批、工时页面显示在右侧。 -->
    <main class="module-content">
      <router-view />
    </main>
  </div>
</template>
<script setup>
// 菜单与布局合并维护，权限和待办角标仍读取公共用户状态。
import { computed } from 'vue'
import { useUserStore } from '../stores/user'
import './module-layout.css'

const user = useUserStore()
const isAdmin = computed(() => user.isAdmin)
const isLEADER = computed(() => user.isLEADER)
const pendingTotal = computed(() => user.pendingTotal)
</script>
