<template>
  <div class="ledger-overview">
    <el-card shadow="never">
      <template #header>台账系统</template>
      <el-empty description="台账功能建设中，暂未开放数据录入与查询">
        <el-button @click="$router.push('/applications')">返回应用中心</el-button>
      </el-empty>
    </el-card>
  </div>
</template>
<style scoped>
.ledger-overview { padding: 20px; }
</style>
