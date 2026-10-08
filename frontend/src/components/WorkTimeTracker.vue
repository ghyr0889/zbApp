<template>
  <section class="tracker">
    <div class="list-header">
      <div><h3>我的工作 <span>{{ groups.length }} 个工作包 · {{ owned.length }} 个工作项</span></h3></div>
      <div class="search"><el-input v-model="keyword" clearable placeholder="搜索工作项名称或工作包编号" /><el-button :loading="loading" @click="$emit('refresh')">刷新</el-button></div>
    </div>
    <el-alert v-if="error" :title="error" type="error" :closable="false" />
    <el-table :data="filteredGroups" v-loading="loading" border size="small" style="width: 100%" max-height="calc(100vh - 320px)" :header-cell-style="{ background: '#ffffff', color: '#64748b', fontWeight: '600' }" row-key="id" :expand-row-keys="expandedKeys" @expand-change="onExpand" empty-text="暂无符合条件的工作包">
      <el-table-column type="expand">
        <template #default="{ row: pkg }">
          <div class="nested-table">
            <el-table :data="pkg.items" border size="small" highlight-current-row :current-row-key="selectedId" row-key="id" @row-click="select" empty-text="暂无符合条件的工作项">
              <el-table-column type="index" label="序号" width="60" align="center" />
              <el-table-column prop="name" label="工作项名称" min-width="220" show-overflow-tooltip />
              <el-table-column label="状态" width="150"><template #default="{ row }"><el-tag :type="isCurrent(row) ? 'success' : row.can_start ? 'info' : 'warning'">{{ isCurrent(row) ? '本次计时未结束' : row.can_start ? '可计时' : '已完成 / 关闭' }}</el-tag></template></el-table-column>
              <el-table-column label="计时操作" width="150" fixed="right"><template #default="{ row }">
                <WorkTimeActions v-if="isCurrent(row)" />
                <el-button v-else type="primary" plain size="small" :disabled="timer.busy || !row.can_start || !!timer.current || !timer.ready || !!timer.syncError || !!error || loading" :loading="timer.busy && selectedId === row.id" @click.stop="start(row)">开始计时</el-button>
              </template></el-table-column>
            </el-table>
          </div>
        </template>
      </el-table-column>
      <el-table-column type="index" label="序号" width="60" align="center" />
      <el-table-column label="工作包编号" min-width="150" show-overflow-tooltip><template #default="{ row }">{{ row.work_package_code || '—' }}</template></el-table-column>
      <el-table-column prop="work_package_name" label="工作包名称" min-width="200" show-overflow-tooltip />
      <el-table-column prop="project_name" label="所属项目" min-width="180" show-overflow-tooltip />
      <el-table-column label="工作项数" width="110" align="center"><template #default="{ row }">{{ row.items.length }}</template></el-table-column>
    </el-table>
    <p v-if="timer.current" class="list-note">每次只能计时一个工作项，请先结束当前计时再切换。关闭页面不会停止计时。</p>
  </section>
</template>
<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useWorkTimeStore } from '../stores/workTime'
import WorkTimeActions from './WorkTimeActions.vue'
const props = defineProps({ items: { type: Array, default: () => [] }, loading: Boolean, error: String })
defineEmits(['refresh'])
const timer = useWorkTimeStore(), route = useRoute(), keyword = ref(''), selectedId = ref(Number(route.query.item) || null)
// 历史工时选项可能属于已转办的工作项，只把当前本人负责的项目显示在操作列表中。
const owned = computed(() => props.items.filter(x => x.is_owned))
// 当前工作项即使已转办或删除，仍保留一行结束入口，避免计时无法结束。
const listed = computed(() => {
  const current = timer.current
  if (!current || owned.value.some(x => x.id === current.work_item_id)) return owned.value
  return [{ id: current.work_item_id, name: current.work_item_name, project_name: current.project_name,
    work_package_id: current.work_package_id,
    work_package_code: props.items.find(x => x.id === current.work_item_id)?.work_package_code,
    work_package_name: current.work_package_name, can_start: false }, ...owned.value]
})
// 按工作包主键分组，避免不同工作包名称相同时被合并。
const groups = computed(() => {
  const result = new Map()
  for (const item of listed.value) {
    if (!result.has(item.work_package_id)) result.set(item.work_package_id, {
      id: item.work_package_id, work_package_code: item.work_package_code,
      work_package_name: item.work_package_name, project_name: item.project_name, items: []
    })
    result.get(item.work_package_id).items.push(item)
  }
  return [...result.values()]
})
// 编号命中时显示整个工作包；名称命中时只显示该包内匹配的工作项。
const filteredGroups = computed(() => {
  const key = keyword.value.trim().toLowerCase()
  if (!key) return groups.value
  return groups.value.map(pkg => ({ ...pkg, items: String(pkg.work_package_code ?? '').toLowerCase().includes(key)
    ? pkg.items : pkg.items.filter(item => String(item.name ?? '').toLowerCase().includes(key))
  })).filter(pkg => pkg.items.length)
})
const expandedKeys = ref([])
function onExpand(row, expandedRows) { expandedKeys.value = expandedRows.map(pkg => pkg.id) }
// 搜索时展开匹配工作包；从计时链接进入时展开目标工作项所属工作包。
watch([filteredGroups, selectedId, keyword], () => {
  if (keyword.value.trim()) { expandedKeys.value = filteredGroups.value.map(pkg => pkg.id); return }
  const keys = expandedKeys.value.filter(id => groups.value.some(pkg => pkg.id === id))
  const selectedPackage = groups.value.find(pkg => pkg.items.some(item => item.id === selectedId.value))
  if (selectedPackage && !keys.includes(selectedPackage.id)) keys.push(selectedPackage.id)
  expandedKeys.value = keys
}, { immediate: true })
const isCurrent = row => row.id === timer.current?.work_item_id
function select(row) { if (!timer.current) selectedId.value = row.id }
watch(() => route.query.item, value => { if (route.query.view === 'timer') selectedId.value = Number(value) || null })
watch(() => timer.current?.work_item_id, value => { if (value) selectedId.value = value }, { immediate: true })
async function start(row) {
  if (!row?.can_start || timer.busy || timer.current) return
  selectedId.value = row.id
  try { await timer.start(row.id) }
  catch (e) { ElMessage.error(typeof e.response?.data?.detail === 'string' ? e.response.data.detail : '开始失败，请检查当前计时状态后重试') }
}
</script>
<style scoped>
.list-header { display: flex; justify-content: space-between; align-items: center; gap: 16px; flex-wrap: wrap; margin: 8px 0 16px; }
h3 { margin: 0 0 8px; font-size: 18px; } h3 span { font-size: 13px; color: #64748b; margin-left: 8px; }
.list-header p, .list-note { margin: 0; font-size: 13px; color: #64748b; }
.list-note { margin-top: 14px; }
.search { display: flex; gap: 10px; width: 420px; max-width: 100%; }
.nested-table { padding: 12px 20px 12px 48px; background: #f8fafc; }
</style>
