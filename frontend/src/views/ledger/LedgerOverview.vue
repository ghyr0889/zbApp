<!-- 台账系统入口：跳转到独立的台账管理系统，并带上当前登录令牌实现免二次登录 -->
<template>
  <div class="ledger-overview">
    <el-card shadow="never">
      <template #header>台账系统</template>
      <el-result :icon="failed ? 'warning' : 'info'" :title="title" :sub-title="subTitle">
        <template #extra>
          <el-button type="primary" @click="gotoLedger">重新进入台账系统</el-button>
          <el-button @click="$router.push('/applications')">返回应用中心</el-button>
        </template>
      </el-result>
      <p class="ledger-tip">台账管理系统为独立部署的服务，地址：{{ LEDGER_URL }}</p>
    </el-card>
  </div>
</template>

<script setup>
// 台账系统是独立前后端、独立数据库的另一个服务，这里只负责带令牌跳转。
// 令牌沿用工作系统的登录令牌，台账后端会只读校验 login_sessions，因此无需二次登录。
import { ref } from 'vue'

const LEDGER_URL =
  import.meta.env.VITE_LEDGER_URL || `${window.location.protocol}//${window.location.hostname}:8010`

const failed = ref(false)
const title = ref('正在进入台账系统…')
const subTitle = ref('如长时间无响应，请点击下方按钮手动进入。')

function gotoLedger () {
  const token = sessionStorage.getItem('access_token')
  if (!token) {
    failed.value = true
    title.value = '没有有效的登录信息'
    subTitle.value = '请先在首页重新登录，再从应用中心进入台账系统。'
    return
  }
  window.location.replace(`${LEDGER_URL}/?token=${encodeURIComponent(token)}`)
}

gotoLedger()
</script>

<style scoped>
.ledger-overview { padding: 20px; }
.ledger-tip { text-align: center; color: #909399; font-size: 13px; margin: 0 0 8px; }
</style>
