<!-- xiangmu/frontend/src/views/ScoreBoard.vue -->
<template>
  <div class="score-board-page">
    <el-card shadow="hover">
      <template #header>
        <div class="page-header">
          <div>
            <h2>积分查看</h2>
            <p>所有人员已审核通过的工作包积分明细</p>
          </div>
          <el-radio-group v-model="currentPeriod" size="small" @change="fetchPublicScoreBoard">
            <el-radio-button label="day">今日</el-radio-button>
            <el-radio-button label="month">本月</el-radio-button>
            <el-radio-button label="quarter">本季度</el-radio-button>
            <el-radio-button label="all">全部历史</el-radio-button>
          </el-radio-group>
        </div>
      </template>

      <div class="summary-row">
        <el-statistic title="当前周期总积分" :value="totalScore" />
        <el-statistic title="有积分人员" :value="activePeopleCount" />
        <el-statistic title="公开工作包记录" :value="totalWorkPackageCount" />
      </div>

      <el-table
        :data="peopleList"
        v-loading="loading"
        stripe
        border
        style="width: 100%"
        empty-text="当前周期暂无已通过的积分数据"
      >
        <el-table-column type="expand" width="48">
          <template #default="{ row }">
            <div class="detail-panel">
              <el-table
                v-if="row.details && row.details.length"
                :data="row.details"
                size="small"
                border
                style="width: 100%"
              >
                <el-table-column prop="project_name" label="所属项目" width="130" />
                <el-table-column prop="category_name" label="工作类型" width="130" />
                <el-table-column prop="work_package_name" label="工作包名称" min-width="220" show-overflow-tooltip />
                <el-table-column prop="base_score" label="获得分值" width="110" align="center">
                  <template #default="scope">
                    <el-tag type="success">+{{ scope.row.base_score }} 分</el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="approved_at" label="审核通过时间" width="170" align="center" />
              </el-table>
              <el-empty v-else description="该人员当前周期暂无积分工作包" :image-size="56" />
            </div>
          </template>
        </el-table-column>

        <el-table-column type="index" label="排名" width="70" align="center" />
        <el-table-column prop="username" label="姓名" width="140" />
        <el-table-column prop="user_id" label="工号" width="120" />
        <el-table-column label="角色" width="140" align="center">
          <template #default="{ row }">
            <el-tag :type="roleTagType(row.role)">{{ roleLabel(row.role) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="total_score" label="周期总分" width="130" align="center" sortable>
          <template #default="{ row }">
            <span class="score-text">{{ row.total_score }}</span>
          </template>
        </el-table-column>
        <el-table-column label="对应工作包数量" width="150" align="center">
          <template #default="{ row }">
            {{ row.details?.length || 0 }}
          </template>
        </el-table-column>
        <el-table-column label="工作包概览" min-width="260" show-overflow-tooltip>
          <template #default="{ row }">
            <span v-if="row.details && row.details.length">
              {{ row.details.map(item => item.work_package_name).join('、') }}
            </span>
            <span v-else class="muted-text">暂无</span>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { getPublicScoreBoardApi } from '../api'

const currentPeriod = ref('all')
const peopleList = ref([])
const loading = ref(false)

const totalScore = computed(() => {
  return peopleList.value.reduce((sum, person) => sum + Number(person.total_score || 0), 0)
})

const activePeopleCount = computed(() => {
  return peopleList.value.filter(person => Number(person.total_score || 0) > 0).length
})

const totalWorkPackageCount = computed(() => {
  return peopleList.value.reduce((sum, person) => sum + (person.details?.length || 0), 0)
})

const roleLabel = (role) => {
  const normalizedRole = String(role || '').toUpperCase()
  if (normalizedRole === 'ADMIN') return '管理员'
  if (normalizedRole === 'OWNER' || normalizedRole === 'LEADER') return '项目负责人'
  return '普通员工'
}

const roleTagType = (role) => {
  const normalizedRole = String(role || '').toUpperCase()
  if (normalizedRole === 'ADMIN') return 'danger'
  if (normalizedRole === 'OWNER' || normalizedRole === 'LEADER') return 'warning'
  return 'info'
}

const fetchPublicScoreBoard = async () => {
  loading.value = true
  try {
    const res = await getPublicScoreBoardApi(currentPeriod.value)
    if (res?.data?.code === 200) {
      peopleList.value = res.data.data.people || []
    }
  } catch (err) {
    console.error('获取公开积分数据报错:', err)
    ElMessage.error('获取公开积分数据失败')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchPublicScoreBoard()
})
</script>

<style scoped>
.score-board-page {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
}

.page-header h2 {
  margin: 0;
  font-size: 20px;
  color: #303133;
}

.page-header p {
  margin: 6px 0 0;
  color: #909399;
  font-size: 13px;
}

.summary-row {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
  margin-bottom: 20px;
  padding: 16px;
  background: #f8fafc;
  border: 1px solid #ebeef5;
  border-radius: 8px;
}

.detail-panel {
  padding: 12px 24px;
  background: #fbfdff;
}

.score-text {
  color: #67c23a;
  font-weight: 700;
}

.muted-text {
  color: #c0c4cc;
}

@media (max-width: 900px) {
  .page-header {
    align-items: flex-start;
    flex-direction: column;
  }

  .summary-row {
    grid-template-columns: 1fr;
  }
}
</style>

