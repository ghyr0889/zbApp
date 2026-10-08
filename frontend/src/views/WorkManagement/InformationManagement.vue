<template>
  <div class="information-management">
    <el-alert
      title="在此统一维护科室和工作包类型。改名会同步关联数据；未被使用的科室或类型可以删除。"
      type="info" :closable="false" show-icon
    />
    <div class="information-grid">
      <el-card v-for="group in groups" :key="group.kind" shadow="never">
        <template #header>
          <div class="group-header">
            <strong>{{ group.title }}</strong>
            <el-button :loading="group.loading" :disabled="group.saving" @click="loadGroup(group)">刷新</el-button>
          </div>
        </template>
        <div class="create-row">
          <el-input v-model="group.newName" :maxlength="group.maxLength" show-word-limit
            :placeholder="`输入新的${group.title}名称`" :disabled="group.saving"
            @keyup.enter="createEntry(group)" />
          <el-button type="primary" :loading="group.saving" :disabled="group.loading" @click="createEntry(group)">新增并保存</el-button>
        </div>
        <el-alert v-if="group.error" :title="group.error" type="error" :closable="false" class="error-message" />
        <el-table :data="group.items" v-loading="group.loading" border stripe max-height="460" empty-text="暂无信息，请先新增">
          <el-table-column type="index" label="序号" width="65" />
          <el-table-column :label="`${group.title}名称`" min-width="180">
            <template #default="{ row }">
              <el-input v-model="row.name" :maxlength="group.maxLength" :disabled="group.saving" />
            </template>
          </el-table-column>
          <el-table-column label="操作" width="190" align="center">
            <template #default="{ row }">
              <el-button link type="primary" :disabled="group.saving || row.name.trim() === row.originalName" @click="saveEntry(group, row)">保存</el-button>
              <el-button link :disabled="group.saving || row.name === row.originalName" @click="row.name = row.originalName">还原</el-button>
              <el-button link type="danger" :disabled="group.loading || group.saving" @click="deleteEntry(group, row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
        <p class="group-note">修改后点击该行“保存”。{{ group.kind === 'departments' ? '新增科室即使尚无人员，也会出现在人员管理下拉框中。' : '改名会同步已有工作包；工作包类型不可重名。' }}</p>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { onMounted, reactive } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getInformationApi, createInformationApi, updateInformationApi, deleteInformationApi } from '../../api'

const emit = defineEmits(['changed'])
const groups = reactive([
  { kind: 'departments', title: '科室', maxLength: 255 },
  { kind: 'work-categories', title: '工作包类型', maxLength: 100 },
].map(group => ({ ...group, items: [], newName: '', loading: false, saving: false, error: '' })))

const errorMessage = (error, fallback) => typeof error.response?.data?.detail === 'string'
  ? error.response.data.detail : fallback

async function loadGroup(group) {
  if (group.loading || group.saving) return
  group.loading = true
  group.error = ''
  try {
    const { data } = await getInformationApi(group.kind)
    // 保留原始名称用于识别修改、还原输入；保存某一行不会丢掉其他行尚未保存的输入。
    group.items = data.data.map(row => ({ ...row, originalName: row.name }))
  } catch (error) {
    group.error = errorMessage(error, '加载失败，请点击刷新重试')
  } finally { group.loading = false }
}

function validName(group, value, exceptId) {
  const name = value.trim()
  if (!name) { ElMessage.warning('请输入名称'); return null }
  if (name.length > group.maxLength) { ElMessage.warning(`名称不能超过${group.maxLength}个字符`); return null }
  if (group.items.some(row => row.id !== exceptId && row.originalName === name)) {
    ElMessage.warning('该名称已存在'); return null
  }
  return name
}

async function createEntry(group) {
  if (group.loading || group.saving) return
  const name = validName(group, group.newName)
  if (!name) return
  group.saving = true
  try {
    const { data } = await createInformationApi(group.kind, { name })
    group.items.push({ ...data.data, originalName: data.data.name })
    group.newName = ''
    ElMessage.success('新增成功')
    emit('changed', group.kind)
  } catch (error) { ElMessage.error(errorMessage(error, '新增失败')) }
  finally { group.saving = false }
}

async function saveEntry(group, row) {
  if (group.loading || group.saving) return
  const name = validName(group, row.name, row.id)
  if (!name) return
  group.saving = true
  try {
    const { data } = await updateInformationApi(group.kind, row.id, { name })
    // 类型改名可能返回新的字典 ID，必须使用服务端返回值更新后续保存目标。
    Object.assign(row, data.data, { originalName: data.data.name })
    ElMessage.success(`保存成功，已同步 ${data.data.affected_count} 条关联记录`)
    emit('changed', group.kind)
  } catch (error) { ElMessage.error(errorMessage(error, '保存失败')) }
  finally { group.saving = false }
}

async function deleteEntry(group, row) {
  if (group.loading || group.saving) return
  // 确认期间锁定本组编辑，提示使用已保存名称，避免误认未保存的输入。
  group.saving = true
  try {
    try {
      await ElMessageBox.confirm(
        `确定删除${group.title}“${row.originalName}”吗？删除后将从下拉选项中移除，已被使用的条目无法删除。`,
        '确认删除', { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' }
      )
    } catch { return }
    await deleteInformationApi(group.kind, row.id)
    // 只移除成功删除的行，保留其他行未保存的编辑。
    group.items = group.items.filter(item => item.id !== row.id)
    ElMessage.success('删除成功')
    emit('changed', group.kind)
  } catch (error) { ElMessage.error(errorMessage(error, '删除结果未确认，请刷新列表检查')) }
  finally { group.saving = false }
}

onMounted(() => Promise.allSettled(groups.map(loadGroup)))
</script>

<style scoped>
.information-management { padding: 12px 0; }
.information-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 20px; margin-top: 20px; }
.group-header, .create-row { display: flex; align-items: center; gap: 12px; }
.group-header { justify-content: space-between; }
.create-row { margin-bottom: 16px; }
.group-note { color: #64748b; font-size: 13px; line-height: 1.7; margin-bottom: 0; }
.error-message { margin-bottom: 12px; }
@media (max-width: 1100px) { .information-grid { grid-template-columns: 1fr; } }
</style>
