<!-- xiangmu/frontend/src/views/WorkItemList.vue -->
<template>
  <div class="work-item-page">
    <el-card class="box-card" shadow="never">
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <el-button link @click="goBack">← 返回</el-button>
            <span class="title">工作项管理</span>
          </div>
          <el-button v-if="canManage" type="success" plain @click="handleAddWorkItem">
            新增工作项
          </el-button>
        </div>
      </template>

      <!-- 工作包信息概览 (按要求精简为3项) -->
      <div class="wp-info" v-if="workPackage">
        <el-descriptions :column="3" border size="small">
          <el-descriptions-item label="工作包编号">{{ workPackage.id }}</el-descriptions-item>
          <el-descriptions-item label="所属项目名称">{{ workPackage.project_name }}</el-descriptions-item>
          <el-descriptions-item label="工作包负责人">
            {{ workPackage.owner_name || workPackage.owner_id || '未指定' }}
          </el-descriptions-item>
        </el-descriptions>
      </div>

      <!-- 工作项列表 -->
      <el-table
        :data="workItems"
        v-loading="loading"
        border
        stripe
        style="width: 100%"
        empty-text="该工作包下暂无工作项，点击右上角可新增"
      >
        <el-table-column prop="name" label="工作项名称" min-width="150">
          <template #default="{ row }">
            <el-input v-if="row.isEdit" v-model="row.name" size="small" placeholder="请输入名称" />
            <span v-else>{{ row.name }}</span>
          </template>
        </el-table-column>

        <el-table-column prop="standard" label="完成标准" min-width="180">
          <template #default="{ row }">
            <el-input v-if="row.isEdit" type="textarea" autosize v-model="row.standard" size="small" placeholder="描述标准" />
            <span v-else>{{ row.standard || '-' }}</span>
          </template>
        </el-table-column>

        <el-table-column prop="difficulty" label="难度" width="100" align="center">
          <template #default="{ row }">
            <el-select v-if="row.isEdit" v-model="row.difficulty" size="small">
              <el-option v-for="o in ['P1', 'P2', 'P3']" :key="o" :label="o" :value="o" />
            </el-select>
            <el-tag v-else size="small" :type="row.difficulty === 'P3' ? 'danger' : (row.difficulty === 'P2' ? 'warning' : 'info')">
              {{ row.difficulty || '-' }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="importance" label="重要性" width="100" align="center">
          <template #default="{ row }">
            <el-select v-if="row.isEdit" v-model="row.importance" size="small">
              <el-option v-for="o in ['Ⅰ级', 'Ⅱ级', 'Ⅲ级']" :key="o" :label="o" :value="o" />
            </el-select>
            <el-tag v-else size="small" :type="row.importance === 'Ⅲ级' ? 'danger' : (row.importance === 'Ⅱ级' ? 'warning' : 'info')">
              {{ row.importance || '-' }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="innovation" label="创新性" width="100" align="center">
          <template #default="{ row }">
            <el-select v-if="row.isEdit" v-model="row.innovation" size="small">
              <el-option v-for="o in ['低', '中', '高']" :key="o" :label="o" :value="o" />
            </el-select>
            <span v-else>{{ row.innovation || '-' }}</span>
          </template>
        </el-table-column>

        <el-table-column prop="category" label="类别" width="120" align="center">
          <template #default="{ row }">
            <el-input v-if="row.isEdit" v-model="row.category" size="small" placeholder="如:类别1" />
            <span v-else>{{ row.category || '-' }}</span>
          </template>
        </el-table-column>

        <el-table-column prop="deadline" label="截止时间" width="150" align="center">
          <template #default="{ row }">
            <el-date-picker 
              v-if="row.isEdit" 
              v-model="row.deadline" 
              type="date" 
              value-format="YYYY-MM-DD" 
              size="small" 
              style="width: 100%" 
              placeholder="选择日期" 
            />
            <el-tag v-else-if="row.deadline" type="danger" effect="plain">⏰ {{ row.deadline }}</el-tag>
            <span v-else>-</span>
          </template>
        </el-table-column>

        <el-table-column prop="score" label="分值" width="100" align="center">
          <template #default="{ row }">
            <el-input-number v-if="row.isEdit" v-model="row.score" :min="0" :step="0.5" size="small" style="width: 100%" controls-position="right" />
            <span v-else class="score-text">{{ row.score }}</span>
          </template>
        </el-table-column>

        <el-table-column v-if="canManage" label="操作" width="120" align="center" fixed="right">
          <template #default="{ row, $index }">
            <template v-if="row.isEdit">
              <el-button type="success" link size="small" :loading="saving" @click="handleSaveItem(row)">保存</el-button>
              <el-button type="info" link size="small" @click="cancelEdit(row, $index)">取消</el-button>
            </template>
            <template v-else>
              <el-button type="primary" link size="small" @click="row.isEdit = true">编辑</el-button>
              <el-popconfirm title="确定删除该工作项？" confirm-button-type="danger" @confirm="removeItem(row)">
                <template #reference>
                  <el-button type="danger" link size="small">删除</el-button>
                </template>
              </el-popconfirm>
            </template>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { createWorkItemApi, deleteWorkItemApi, getWorkItemsApi } from '../api'
import { useUserStore } from '../stores/user'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const workPackageId = route.params.id
const workPackage = ref(null)
const workItems = ref([])
const loading = ref(false)
const saving = ref(false)

// 管理权限：管理员 / 项目负责人 / 该工作包负责人 可以新增、编辑、删除工作项
const canManage = computed(() => {
  if (!userStore.isLoggedIn) return false
  if (userStore.isAdmin || userStore.isOwner) return true
  return workPackage.value && String(workPackage.value.owner_id) === String(userStore.userInfo?.id)
})

const fetchData = async () => {
  loading.value = true
  try {
    const res = await getWorkItemsApi(workPackageId)
    if (res.data?.code === 200) {
      workPackage.value = res.data.data.work_package
      // 为每条数据追加编辑状态和历史备份以供取消编辑时回退
      workItems.value = (res.data.data.work_items || []).map(item => ({
        ...item,
        isEdit: false,
        isNew: false,
        _original: JSON.parse(JSON.stringify(item))
      }))
    }
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '获取工作项失败')
  } finally {
    loading.value = false
  }
}

const handleAddWorkItem = () => {
  // 在表格最上方追加一行处于编辑状态的空数据
  workItems.value.unshift({
    id: null,
    name: '',
    standard: '',
    difficulty: '低',
    importance: '中',
    innovation: '低',
    deadline: '',
    score: 0,
    category: '',
    work_package_id: workPackageId,
    isEdit: true,
    isNew: true
  })
}

const handleSaveItem = async (row) => {
  if (!row.name || !row.name.trim()) return ElMessage.warning('请输入工作项名称')
  saving.value = true
  try {
    const res = await createWorkItemApi({
      work_package_id: workPackageId,
      work_item_id: row.isNew ? null : row.id,
      name: row.name.trim(),
      standard: row.standard,
      difficulty: row.difficulty,
      importance: row.importance,
      innovation: row.innovation,
      deadline: row.deadline || '',
      score: row.score,
      category: row.category
    })
    if (res.data?.code === 200) {
      ElMessage.success('工作项保存成功')
      await fetchData() // 保存成功后重新拉取最新数据
    }
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

const cancelEdit = (row, index) => {
  if (row.isNew) {
    workItems.value.splice(index, 1) // 新增的数据直接移除该行
  } else {
    // 已有的数据撤销编辑，还原到备份的初始状态
    Object.assign(row, row._original)
    row.isEdit = false
  }
}

const removeItem = async (row) => {
  try {
    const res = await deleteWorkItemApi(row.id)
    if (res.data?.code === 200) {
      ElMessage.success('工作项已删除')
      await fetchData()
    }
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '删除失败')
  }
}

const goBack = () => {
  router.push('/project-overview')
}

onMounted(fetchData)
</script>

<style scoped>
.work-item-page {
  padding: 20px;
  animation: fadeIn 0.4s ease;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.box-card {
  border-radius: 12px;
  border: none;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.04);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.title {
  font-size: 18px;
  font-weight: 600;
  color: #1e293b;
}

.wp-info {
  margin-bottom: 16px;
}

.score-text {
  color: #67c23a;
  font-weight: 700;
}

.tip-text {
  color: #94a3b8;
  font-size: 13px;
}
</style>