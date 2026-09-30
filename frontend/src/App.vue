<template>
  <div id="app">
    <!-- 顶部导航栏容器：使用 flex 布局强行左右分栏 -->
    <div class="header-layout" v-if="$route.path !== '/login'">
      
      <!-- 品牌标识区 -->
      <div class="brand-logo">
        <span class="logo-text">综保工作管理系统</span>
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
        <el-menu-item index="/personal-info">
          <i class="el-icon-user"></i>
          <span>个人信息</span>
        </el-menu-item>
        <el-menu-item index="/announcements">
          <i class="el-icon-bell" aria-hidden="true"></i>
          <span>公告板</span>
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
    </div>

    <!-- 右侧：永远常显的个人信息与下拉退出 -->
    <div class="right-profile" v-if="$route.path !== '/login' && userInfo">
      <el-dropdown @command="handleUserCommand" trigger="hover">
        
        <!-- 常显触发区：直接展示头像、姓名、工号、角色 -->
        <div class="user-info-trigger">
          <el-avatar size="small" class="user-avatar">
            {{ userInfo.username ? userInfo.username.charAt(0) : 'U' }}
          </el-avatar>
          <div class="user-text-info">
            <span class="user-name">{{ userInfo.username }}</span>
            <span class="user-id">ID: {{ userInfo.id }}</span>
          </div>
          <el-tag size="small" :type="roleTagType" effect="light" class="role-tag">
            {{ roleDisplayName }}
          </el-tag>
        </div>
        
        <!-- 只有点击后才出现的下拉菜单 -->
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="toggle-notify">
              {{ notifyEnabled ? '关闭待办提醒' : '开启待办提醒' }}
            </el-dropdown-item>
            <el-dropdown-item command="toggle-sound">
              {{ soundEnabled ? '关闭提醒音' : '开启提醒音' }}
            </el-dropdown-item>
            <el-dropdown-item command="logout" class="logout-item" divided>
              退出登录
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>

    <div :class="$route.path === '/login' ? 'login-body' : 'main-body'">
      <div class="page-container">
        <router-view />
      </div>
    </div>
  </div>
</template>

<script setup>
// 脚本部分保持原样，未做修改以保证逻辑稳定
import { ElMessage, ElNotification } from 'element-plus'
import { computed, ref, watch, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from './stores/user'

const router = useRouter()
const userStore = useUserStore()
const userInfo = computed(() => userStore.userInfo)

const isAdmin = computed(() => userStore.isAdmin)
const isLEADER = computed(() => userStore.isLEADER)

const pendingTotal = computed(() => userStore.pendingTotal)

// ================= 待办提醒（站内浮层 + 提示音 + 标题闪烁） =================
// 不依赖 Notification 权限：局域网 http 下浏览器不允许系统通知，这种方案任何环境都能用
const NOTIFY_KEY = 'pending_notify_enabled'
const SOUND_KEY = 'pending_notify_sound'

const notifyEnabled = ref(localStorage.getItem(NOTIFY_KEY) !== '0')  // 默认开启
const soundEnabled = ref(localStorage.getItem(SOUND_KEY) !== '0')    // 默认开启

const TAB_KEYS = ['review', 'complete', 'transfers']
const TAB_LABEL = { review: '审批查阅', complete: '完成申请', transfers: '工作包转办' }
const BASE_TITLE = '综保工作管理系统'   // 与 index.html 的 <title> 保持一致

let lastPending = null         // 上一次的待办快照；null = 还没建基线
let pendingWhileHidden = false // 页面在后台期间累积了新增，切回前台时合并提示

// ---- 提示音：用 Web Audio 现场生成两声"叮咚"，免去引入音频文件 ----
let audioCtx = null
async function unlockAudio() {
  try {
    if (!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)()
    if (audioCtx.state === 'suspended') await audioCtx.resume()
    return audioCtx
  } catch {
    return null   // 浏览器不支持就静默降级，不影响浮层和标题提醒
  }
}

function playBeep() {
  if (!soundEnabled.value || !audioCtx || audioCtx.state !== 'running') return
  const start = audioCtx.currentTime
  ;[880, 1174].forEach((freq, i) => {          // A5 → D6
    const at = start + i * 0.18
    const osc = audioCtx.createOscillator()
    const gain = audioCtx.createGain()
    osc.type = 'sine'
    osc.frequency.value = freq
    gain.gain.setValueAtTime(0.0001, at)                        // 淡入淡出，避免爆音
    gain.gain.exponentialRampToValueAtTime(0.18, at + 0.02)
    gain.gain.exponentialRampToValueAtTime(0.0001, at + 0.16)
    osc.connect(gain).connect(audioCtx.destination)
    osc.start(at)
    osc.stop(at + 0.18)
  })
}

// 浏览器自动播放策略：必须有过用户交互才允许出声，所以首次点击时解锁
function handleFirstGesture() {
  unlockAudio()
  document.removeEventListener('pointerdown', handleFirstGesture)
}
document.addEventListener('pointerdown', handleFirstGesture)

// ---- 页面在后台时把数量标在标题上（切回前台恢复） ----
function setTitleBadge(n) {
  document.title = n > 0 ? `(${n}) ${BASE_TITLE}` : BASE_TITLE
}

// ---- 只在待办"变多"时提醒；处理完变少时静默 ----
function pendingDelta(prev, now) {
  let added = 0
  let target = 'review'
  let best = 0
  const parts = []
  for (const key of TAB_KEYS) {
    const d = (now[key] || 0) - (prev[key] || 0)
    if (d > 0) {
      added += d
      parts.push(`${TAB_LABEL[key]} +${d}`)
      if (d > best) { best = d; target = key }   // 增量最大的那个页签作为跳转目标
    }
  }
  return { added, parts, target }
}

function remind(added, parts, total, target) {
  playBeep()
  ElNotification({
    title: `有 ${added} 条新的待办`,
    message: `${parts.join('、')}（当前共 ${total} 条）`,
    type: 'warning',
    duration: 6000,
    position: 'bottom-right',
    // 点一下直接跳到对应页签，不用自己去翻
    onClick: () => router.push({ path: '/review', query: { tab: target } })
  })
}

watch(() => userStore.pending, (now) => {
  const prev = lastPending
  lastPending = { ...now }
  if (!prev || !notifyEnabled.value) return   // 登录后的第一笔只做基线，不提醒
  const { added, parts, target } = pendingDelta(prev, now)
  if (added <= 0) return
  const total = userStore.pendingTotal
  if (document.hidden) {
    // 免打扰：不弹浮层，只在标题上显示数字，切回前台再合并成一条
    pendingWhileHidden = true
    setTitleBadge(total)
    return
  }
  remind(added, parts, total, target)
})

let pendingTimer = null

function startPendingPolling() {
  stopPendingPolling()
  userStore.refreshPendingCount()
  pendingTimer = setInterval(() => {
    userStore.refreshPendingCount()
  }, 45000) // 45s，30~60s 之间
}

function stopPendingPolling() {
  if (pendingTimer) {
    clearInterval(pendingTimer)
    pendingTimer = null
  }
}

// 用户切换（登录/退出）时统一处理：有用户就拉 + 起轮询，没用户就停 + 归零
watch(
  () => userInfo.value,
  (u) => {
    if (u) {
      startPendingPolling()
    } else {
      stopPendingPolling()
      userStore.clearPending()
      // 退出后重置提醒状态：下次登录重新建基线，避免把"登录瞬间拉到数据"当成新增
      lastPending = null
      pendingWhileHidden = false
      setTitleBadge(0)
    }
  },
  { immediate: true }
)

// 切回页面 / 窗口聚焦时立即拉一次，数字马上是新的
async function handleVisible() {
  if (document.visibilityState !== 'visible') return
  setTitleBadge(0)                       // 回到前台，标题恢复正常
  if (!userInfo.value) return
  if (pendingWhileHidden && notifyEnabled.value) {
    pendingWhileHidden = false
    const total = userStore.pendingTotal
    if (total > 0) {
      playBeep()
      ElNotification({
        title: '你有待处理的申请',
        message: `当前共 ${total} 条`,
        type: 'warning',
        duration: 8000,
        position: 'bottom-right',
        onClick: () => router.push('/review')
      })
    }
  }
  userStore.refreshPendingCount()
}

onBeforeUnmount(() => {
  stopPendingPolling()
  document.removeEventListener('visibilitychange', handleVisible)
  window.removeEventListener('focus', handleVisible)
  document.removeEventListener('pointerdown', handleFirstGesture)
  setTitleBadge(0)
})

document.addEventListener('visibilitychange', handleVisible)
window.addEventListener('focus', handleVisible)

const roleDisplayName = computed(() => {
  if (!userInfo.value) return ''
  const role = String(userInfo.value.role).toUpperCase()
  if (role === 'ADMIN') return '管理员'
  if (role === 'LEADER') return '领导（部门主管、项目负责人）'
  if (role === 'DEPARTMENT') return '科室'
  return '普通员工'
})

const roleTagType = computed(() => {
  if (!userInfo.value) return 'info'
  const role = String(userInfo.value.role).toUpperCase()
  if (role === 'ADMIN') return 'danger'
  if (role === 'LEADER') return 'warning'
  if (role === 'DEPARTMENT') return 'success'
  return 'info'
})

const handleUserCommand = (command) => {
  if (command === 'logout') {
    logout()
    return
  }
  if (command === 'toggle-notify') {
    notifyEnabled.value = !notifyEnabled.value
    localStorage.setItem(NOTIFY_KEY, notifyEnabled.value ? '1' : '0')
    ElMessage.success(notifyEnabled.value ? '已开启待办提醒' : '已关闭待办提醒')
    if (notifyEnabled.value) {
      lastPending = { ...userStore.pending }   // 重新开启时重建基线，不补弹历史
      setTitleBadge(0)
    }
    return
  }
  if (command === 'toggle-sound') {
    soundEnabled.value = !soundEnabled.value
    localStorage.setItem(SOUND_KEY, soundEnabled.value ? '1' : '0')
    ElMessage.success(soundEnabled.value ? '已开启提醒音' : '已关闭提醒音')
    // 开启后试听一声：此时正处于用户点击的上下文里，正好用来解锁音频
    if (soundEnabled.value) unlockAudio().then(playBeep)
  }
}

const logout = async () => {
  try {
    await userStore.logout() // 撤销服务端令牌后再退出页面。
    ElMessage.success('已安全退出登录')
    router.push('/login')
  } catch (error) {
    ElMessage.error('退出失败，请检查网络后重试')
  }
}
</script>

<style>
/* ================= 基础重置与全局背景 ================= */
body { 
  margin: 0; 
  background-color: #f0f2f5; 
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', '微软雅黑', Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  
  /* 1. 锁死屏幕整体高度，禁止整个网页出现外层滚动条 */
  height: 100vh;
  width: 100vw;
  overflow: hidden; 
}

.main-body { 
  margin-left: 200px;
  height: 100vh;
  /* 顶部50px给顶部栏占位;左右/底部空隙统一由各页面根 div 的 padding(20px)控制 */
  padding: 64px 0 0;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
}

.page-container {
  padding: 0; /* 空隙统一由各页面根 div 的 padding 控制 */
  flex: 1;       /* 自动占满 header 下方的剩余屏幕高度 */
  overflow: hidden; 
  display: flex;
  flex-direction: column;
}

.login-body {
  min-height: 100vh;
}

/* ================= 页面内部卡片自适应容器 (已修复登录页拉伸) ================= */

/*  让登录页的容器恢复居中并且取消拉伸 */
.login-body {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
}

.login-body .page-container {
  padding: 0;
  display: block; /* 彻底取消登录页的 Flex 纵向拉伸 */
}


/* ================= 全局表格紧凑化 (缩小表格) ================= */
/* 缩小全局表格字体 */
.el-table {
  font-size: 13px !important; 
  flex: 1; /* 让表格自动撑满卡片的高度 */
}

/* 压缩表格行高 */
.el-table .el-table__cell {
  padding: 6px 0 !important; 
}

/* 表格内部按钮也跟着稍微缩小 */
.el-table .el-button--small {
  padding: 4px 8px !important;
  font-size: 12px !important;
}

/* 分页条靠底压缩留白 */
.pagination-bar {
  padding-top: 8px !important;
  padding-bottom: 4px !important;
}

/* ================= 左侧导航栏整体布局 (原样保留) ================= */
.header-layout {
  position: fixed;
  left: 0;
  top: 0;
  bottom: 0;
  z-index: 1001;
  width: 200px;
  background-color: #ffffff;
  box-shadow: 2px 0 8px 0 rgba(29, 35, 41, 0.05);
  display: flex;
  flex-direction: column;
}

/* 品牌 Logo 文字 */
.brand-logo {
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 17px;
  font-weight: 700;
  color: #010203;
  letter-spacing: 2px;
  border-bottom: 1px solid #f0f2f5;
  background: linear-gradient(135deg, #ffffff, #f8fafc);
}

.logo-icon {
  margin-right: 8px;
  font-size: 22px;
}

.logo-text {
  letter-spacing: 1px;
}

/* 左侧菜单 */
.left-menu {
  flex: 1;
  width: 100%;
  border-right: none !important;
  padding: 6px 0;
  box-sizing: border-box;
  --el-menu-item-height: 40px;
}

/* 紧凑菜单：统一高度和间距，仅影响左侧导航。 */
.left-menu .el-menu-item {
  position: relative;
  margin: 2px 10px;
  border-radius: 8px;
  height: 40px;
  line-height: 40px;
  padding-left: 14px !important;
  padding-right: 12px !important;
  
  /* 文字样式 */
  color: #303640;
  font-size: 14px;
  font-weight: 400;
  letter-spacing: 0;
  transition: background-color 0.2s ease, color 0.2s ease;
}

/* 统一图标占位，让各菜单文字的起始位置一致。 */
.left-menu .el-menu-item > i {
  display: inline-block;
  flex: 0 0 22px;
  width: 22px;
  margin-right: 10px;
  text-align: center;
  font-size: 19px;
}

.left-menu .el-menu-item:hover {
  background-color: #f0f5fb !important;
}

/* 浅蓝底色和左侧细线表示当前页面，选中时不改变字重。 */
.left-menu .el-menu-item.is-active {
  color: #409eff;
  background-color: #eaf4ff !important;
  font-weight: 400;
}

.left-menu .el-menu-item.is-active::before {
  content: "";
  position: absolute;
  left: 0;
  top: 10px;
  bottom: 10px;
  width: 2px;
  border-radius: 2px;
  background-color: #409eff;
}

/* 菜单红点：紧贴「审批查阅」四个字的右上角
   关键：把文字包进 .menu-label，红点定位的基准就从「按钮」变成了「文字」 */
.menu-label {
  position: relative;
  display: inline-block;
  line-height: 1.4;   /* 使用文字本身的高度定位红点，避免菜单行高影响位置。 */
}
/* 微调开关：
   top  越小越往上（负值 = 越过文字顶边继续往上）
   right 越大越往左（负值 = 往文字右侧外面挪）
   当前值让红点压在文字的右上角上，略微探出文字右边 */
.menu-label .menu-badge {
  position: absolute;
  top: -9px;
  right: -14px;
  margin: 0;
}

/* el-badge 默认会给数字加 translateY(-50%) translateX(100%)，
   即把数字甩到盒子右侧外面；这里取消，让数字老老实实待在自己盒子的右上角，
   位置就只由上面的 top / right 决定，一位数两位数都不会跑偏 */
.menu-label .menu-badge .el-badge__content {
  transform: none;
}

/* ================= 右侧顶部栏 (原样保留) ================= */
.right-profile {
  position: fixed;
  top: 0;
  left: 200px;
  right: 0;
  height: 64px;
  padding: 0 24px;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  background-color: #ffffff;
  box-shadow: 0 1px 4px rgba(0, 21, 41, 0.08);
  z-index: 1000;
}

/* 常显区域鼠标样式 */
.user-info-trigger {
  display: flex;
  align-items: center;
  padding: 6px 12px;
  border-radius: 24px;
  cursor: pointer;
  transition: all 0.3s ease;
  border: 1px solid transparent;
}

.user-info-trigger:hover {
  background-color: #f5f7fa;
  border-color: #e4e7ed;
}

.user-avatar {
  background: linear-gradient(135deg, #409EFF 0%, #53a8ff 100%);
  color: #fff;
  font-weight: bold;
}

.user-text-info {
  display: flex;
  flex-direction: column;
  margin-left: 10px;
  margin-right: 12px;
  line-height: 1.2;
}

.user-name {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}

.user-id {
  font-size: 12px;
  color: #909399;
  margin-top: 2px;
}

.role-tag {
  border-radius: 12px;
  padding: 0 10px;
}

.logout-item {
  color: #F56C6C;
  font-weight: 500;
}
.logout-item:hover {
  background-color: #fef0f0 !important;
  color: #f56c6c !important;
}
</style>
