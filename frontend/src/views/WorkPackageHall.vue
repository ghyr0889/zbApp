<template>
  <div class="work-package-hall">
    <el-card shadow="hover">
      <template #header>
        <div class="card-header">
          <span>📚 所有工作包</span>
          <el-input
            v-model="searchKeyword"
            placeholder="请输入项目名称进行筛选..."
            clearable
            style="width: 200px;"
          />
          <el-button type="primary" plain @click="fetchAllWorkPackages">🔄 刷新库</el-button>
        </div>
      </template>

      <!-- 1. 外层表格：直接展示每一个项目及其责任人 -->
      <el-table
        :data="filterProjects"
        border
        style="width: 100%"
        v-loading="loadingAllWorkPackages"
        height="650"
        empty-text="暂无项目数据"
        :row-class-name="tableRowClassName"
      >
        <!-- 2. 展开行机制：点开后可以看到该项目中的所有工作包 -->
        <el-table-column type="expand">
          <template #default="{ row }">
            <div class="nested-table-container">
              <!-- 内层表格：工作包详情 -->
              <el-table :data="row.work_packages" border size="small" style="width: 100%" :row-class-name="tableRowClassName">
                <el-table-column prop="category_name" label="工作类型" width="140" />
                <el-table-column prop="name" label="工作包名称" min-width="180" show-overflow-tooltip />
                
                <el-table-column label="工作负责人" min-width="140">
                  <template #default="{ row: pkg }">
                    <div v-if="pkg.assigned_employees && pkg.assigned_employees.length" class="employee-list">
                      <el-tag
                        v-for="employee in pkg.assigned_employees"
                        :key="employee.id"
                        type="success"
                        effect="plain"
                      >
                        {{ employee.name }}（{{ employee.id }}）
                      </el-tag>
                    </div>
                    <span v-else-if="pkg.assignee_id" class="employee-text">
                      {{ pkg.assignee_name || pkg.assignee_id }}（{{ pkg.assignee_id }}）
                    </span>
                  </template>
                </el-table-column>
                
                <el-table-column prop="score" label="基础分值" width="100" align="center">
                  <template #default="{ row: pkg }">
                    <span class="score-text">🏆 {{ pkg.score }}</span>
                  </template>
                </el-table-column>
                
                <el-table-column label="时间节点要求" width="180">
                  <template #default="{ row: pkg }">
                    <el-tag type="info" effect="plain" v-if="pkg.deadline">
                      ⏰ {{ pkg.deadline }}
                    </el-tag>
                    <span v-else class="tip-text">无节点要求</span>
                  </template>
                </el-table-column>

                <el-table-column label="完成状态" width="120">
                  <template #default="{ row: pkg }">
                    <el-tag v-if="pkg.pkg_completed" effect="plain" round>
                      已完成
                    </el-tag>
                    <el-tag v-else effect="plain" round>
                      进行中
                    </el-tag> 
                  </template>
                </el-table-column>
              </el-table>
            </div>
          </template>
        </el-table-column>

        <!-- 外层表格列 -->
        <el-table-column prop="project_name" label="项目名称" min-width="200" />
        <el-table-column label="项目责任人" width="180">
          <template #default="{ row }">
            <!--注意：这里绑定的是 project_owner_name，如果后端暂未提供此字段，会显示暂未指定 -->
            <span style="font-weight: bold; color: #409EFF;">
              {{row.owner_name ? `${row.owner_name}(${row.owner_id})` : '暂未指定'}}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="包含任务总数" width="150" align="center">
          <template #default="{ row }">
            <el-tag type="primary" round>{{ row.work_packages.length }} 个工作包</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="完成状态" width="150">
          <template #default="{ row }">
            <el-tag v-if="row.project_completed"  effect="plain" round>
              整体完结
            </el-tag>
            <el-tag v-else type="primary" effect="plain" round>
              推进中
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { onMounted, ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
// 确保从 api 中引入了正确的接口[cite: 1]
import { getPublicWorkPackagesApi } from '../api'

const allWorkPackages = ref([])
const loadingAllWorkPackages = ref(false)

const fetchAllWorkPackages = async () => {
  loadingAllWorkPackages.value = true
  try {
    const res = await getPublicWorkPackagesApi()
    if (res.data && res.data.code === 200) {
      allWorkPackages.value = res.data.data || []
    }
  } catch (err) {
    console.error('获取所有工作包失败:', err)
    ElMessage.error(err.response?.data?.detail || '获取所有工作包失败')
  } finally {
    loadingAllWorkPackages.value = false
  }
}

const tableRowClassName = ({ row }) => {
  if (row.pkg_completed) {
    return 'completed-row'
  }
  // 没完成的行，什么都不加
  if (row.project_completed) {
    return 'completed-row'
  }
  return ''
}

// 核心转换逻辑：将后端返回的扁平数组，按照 project_name 进行分组合并
const groupedProjects = computed(() => {
  const map = {} //临时字典map
  allWorkPackages.value.forEach(pkg => {
    if (!map[pkg.project_id]) {
      map[pkg.project_id] = {
        project_name: pkg.project_name,
        // 如果扁平数据中自带项目负责人的名字，这里会自动提取。需确保后端返回了这个字段
        owner_name: pkg.owner_name, 
        owner_id: pkg.owner_id,
        project_completed: pkg.project_completed,
        work_packages: []
      }
    }
    // 将工作包塞入对应的项目中
    map[pkg.project_id].work_packages.push(pkg)
  })
  return Object.values(map) // 将对象转回数组供表格渲染
})

const searchKeyword = ref('')

const filterProjects = computed(() => {
  if (!searchKeyword.value){
    return groupedProjects.value
  }
  return groupedProjects.value.filter(project => {
    return project.project_name.includes(searchKeyword.value  )
  })
})

onMounted(() => {
  fetchAllWorkPackages()
})
</script>


<style scoped>
.work-package-hall { padding: 20px; }
.card-header { display: flex; justify-content: space-between; align-items: center; font-weight: bold; }
/* 优化嵌套表格的展示区域 */
.nested-table-container { 
  padding: 15px 30px; 
  background-color: #f8f9fa; 
  border-radius: 4px;
}
.employee-list { display: flex; flex-wrap: wrap; gap: 6px; }
.employee-text { color: #67c23a; font-weight: bold; }
.score-text { color: #67c23a; font-weight: bold; }
.tip-text { color: #909399; font-size: 13px; }

/* 针对贴了 'completed-row' 标签的行进行置灰处理 */
:deep(.el-table .completed-row) {
  /* 修改背景色为浅灰色 */
  --el-table-tr-bg-color: #f5f7fa; 
  /* 修改字体颜色为次要灰 */
  color: #a8abb2; 
}

/* 即使鼠标悬停在这一行上，也不要改变颜色（防止它又亮起来） */
:deep(.el-table .completed-row:hover > td) {
  background-color: #f5f7fa !important;
}

/* （可选）如果你想让变灰这一行里面的按钮、标签也稍微透明一点，显得更彻底，可以加上这句 */
:deep(.el-table .completed-row .el-tag) {
  opacity: 0.6;
}
</style>