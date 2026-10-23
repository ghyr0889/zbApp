<template>
  <div class="assignments">
      <div class="toolbar">
        <el-input v-model="keyword" placeholder="搜索姓名或工号" clearable style="width: 280px" @keyup.enter="load(1)" @clear="load(1)" />
        <el-button type="primary" @click="load(1)">查询</el-button>
        <el-button @click="load(page)">刷新</el-button>
      </div>
      <p class="hint">统计当前负责的全部正式工作项（含已完成），分值为基础总分值之和。点击「查看详情」查看人员工作详情，详情仅供查看。</p>
      <el-table :data="people" v-loading="loading" border empty-text="暂无人员">
        <el-table-column prop="user_id" label="工号" min-width="100" />
        <el-table-column prop="username" label="姓名" min-width="140">
          <template #default="{ row }"><span>{{ row.username }}</span></template>
        </el-table-column>
        <el-table-column prop="department" label="科室" min-width="140" />
        <el-table-column prop="work_item_count" label="工作项数量" min-width="140" align="center" />
        <el-table-column prop="total_score" label="已分配工作项总分值" min-width="180" align="center" />
        <el-table-column label="查看" width="100" align="center">
          <template #default="{ row }"><el-button link type="primary" @click="openPerson(row)">查看详情</el-button></template>
        </el-table-column>
      </el-table>
      <el-pagination v-model:current-page="page" :page-size="20" :total="total" layout="total, prev, pager, next" @current-change="load" />
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getAssignmentsApi } from '../../api'

const router = useRouter()
const people = ref([]), keyword = ref(''), page = ref(1), total = ref(0), loading = ref(false)
let requestId = 0
async function load(nextPage = 1) {
  const id = ++requestId
  page.value = nextPage
  loading.value = true
  try {
    const { data } = await getAssignmentsApi({ page: nextPage, page_size: 20, keyword: keyword.value })
    if (id !== requestId) return
    people.value = data.data.items
    total.value = data.data.total
  } catch (error) {
    if (id === requestId) ElMessage.error(error.response?.data?.detail || '获取员工工作内容失败')
  } finally {
    if (id === requestId) loading.value = false
  }
}
const openPerson = row => router.push(`/assignments/${encodeURIComponent(row.user_id)}`)
onMounted(() => load())
onBeforeUnmount(() => { requestId++ })
</script>

<style scoped>
.assignments { padding: 12px 0; }
.toolbar { display: flex; gap: 12px; align-items: center; }
.hint { color: #909399; font-size: 13px; margin: 16px 0; }
.el-pagination { margin-top: 20px; justify-content: flex-end; }
</style>
