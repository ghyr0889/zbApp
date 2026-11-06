<!-- 管理员编辑工作包模板的弹窗组件 -->
<template>
  <el-dialog v-model="visible" :title="`${category?.originalName || ''} · 工作项模板`" width="min(1100px, 95vw)" class="work-package-template-dialog" draggable append-to-body>
    <div class="template-layout">
      <div class="template-list">
        <el-button type="primary" plain style="width: 100%" @click="newTemplate">新增模板</el-button>
        <el-scrollbar max-height="550px">
          <div v-for="template in templates" 
            :key="template.id" 
            class="template-option" 
            :class="{ selected: form.id === template.id }" 
            @click="selectTemplate(template)">
            <span>{{ template.name }}</span>
            <el-tag size="small" :type="template.is_active ? 'success' : 'info'">{{ template.is_active ? '启用' : '停用' }}</el-tag>
          </div>
        </el-scrollbar>
      </div>
      <div class="template-editor" v-loading="loading">
        <el-form label-position="top">
          <div class="template-fields">
            <el-form-item label="模板名称" required>
              <el-input v-model="form.name" maxlength="100" show-word-limit />
            </el-form-item>
            <el-form-item label="状态">
              <el-switch v-model="form.is_active" active-text="启用" inactive-text="停用" />
            </el-form-item>
          </div>
          <el-form-item label="说明">
            <el-input v-model="form.description" type="textarea" :rows="2" maxlength="500" show-word-limit />
          </el-form-item>
        </el-form>
        <div class="items-heading"><strong>工作项内容</strong><el-button type="primary" plain size="small" @click="addItem">增加一行</el-button></div>
        <el-table :data="form.items" border size="small" max-height="370px">
          <el-table-column label="工作项名称" min-width="170">
            <template #default="{ row }">
              <el-input v-model="row.name" maxlength="100" placeholder="可留空，导入后填写" />
            </template>
          </el-table-column>
          <el-table-column label="完成标准" min-width="190">
            <template #default="{ row }">
              <el-input v-model="row.standard" type="textarea" :rows="2" />
            </template>
          </el-table-column>
          <el-table-column label="截止时间" width="165">
            <template #default="{ row }">
              <el-date-picker v-model="row.deadline" type="date" value-format="YYYY-MM-DD" clearable placeholder="选择日期" style="width: 100%" />
            </template>
          </el-table-column>
          <el-table-column label="难度" width="105">
            <template #default="{ row }">
              <el-select v-model="row.difficulty" clearable>
                <el-option v-for="v in levels.difficulty" :key="v" :label="v" :value="v" />
              </el-select>
            </template>
          </el-table-column>
          <el-table-column label="重要度" width="105">
            <template #default="{ row }">
              <el-select v-model="row.importance" clearable>
                <el-option v-for="v in levels.importance" :key="v" :label="v" :value="v" />
              </el-select>
            </template>
          </el-table-column>
          <el-table-column label="创新度" width="105">
            <template #default="{ row }">
              <el-select v-model="row.innovation" clearable>
                <el-option v-for="v in levels.innovation" :key="v" :label="v" :value="v" />
              </el-select>
            </template>
          </el-table-column>
          <el-table-column label="建议分值" width="115">
            <template #default="{ row }">
              <el-input-number v-model="row.score" :min="0" :controls="false" style="width: 100%" />
            </template>
          </el-table-column>
          <el-table-column label="备注" min-width="140">
            <template #default="{ row }">
              <el-input v-model="row.notes" />
            </template>
          </el-table-column>
          <el-table-column label="操作" width="150" align="center" fixed="right">
            <template #default="{ $index }">
              <div class="item-actions">
                <el-button text class="item-action item-action-text" :disabled="$index === 0" @click="moveItem($index, -1)">上移</el-button>
                <el-button text class="item-action item-action-text" :disabled="$index === form.items.length - 1" @click="moveItem($index, 1)">下移</el-button>
                <el-button text type="danger" class="item-action" title="删除此行" aria-label="删除此行" @click="form.items.splice($index, 1)"><el-icon><Delete /></el-icon></el-button>
              </div>
            </template>
          </el-table-column>
        </el-table>
        <p class="template-hint">工作项名称和截止时间可留空，导入后由人员补填；实际工作项提交前仍需填写名称。修改模板不会更改已提交的申请。</p>
      </div>
    </div>
    <template #footer>
      <el-button v-if="form.id" type="danger" plain :loading="saving" @click="remove">删除模板</el-button>
      <el-button @click="visible = false">关闭</el-button>
      <el-button type="primary" :loading="saving" @click="save">保存模板</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { reactive, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Delete } from '@element-plus/icons-vue'
import { getAdminWorkPackageTemplatesApi, createWorkPackageTemplateApi, updateWorkPackageTemplateApi, deleteWorkPackageTemplateApi } from '../api'
import { useLevelDefs } from '../comosables/useLevelDefs'

const visible = defineModel({ type: Boolean, default: false })
const props = defineProps({ category: { type: Object, default: null } })
const levels = useLevelDefs()
const templates = ref([])
const loading = ref(false)
const saving = ref(false)
const emptyItem = () => ({ name: '', standard: '', deadline: null, difficulty: '', importance: '', innovation: '', score: 0, notes: '' })
const form = reactive({ id: null, name: '', description: '', is_active: true, items: [emptyItem()] })
function newTemplate() { Object.assign(form, { id: null, name: '', description: '', is_active: true, items: [emptyItem()] }) }
function selectTemplate(template) { Object.assign(form, JSON.parse(JSON.stringify(template))) }
function addItem() { form.items.push(emptyItem()) }
function moveItem(index, direction) {
  const other = index + direction
  ;[form.items[index], form.items[other]] = [form.items[other], form.items[index]]
}
async function load() {
  if (!props.category) return
  loading.value = true
  try {
    const response = await getAdminWorkPackageTemplatesApi(props.category.id)
    templates.value = response.data.data
    newTemplate()
  } catch (error) { ElMessage.error(error.response?.data?.detail || '加载模板失败') }
  finally { loading.value = false }
}
watch([visible, () => props.category?.id], ([open]) => { if (open) load() })
async function save() {
  if (!form.name.trim()) return ElMessage.warning('请填写模板名称')
  if (!form.items.length) return ElMessage.warning('请至少增加一条工作项模板内容')
  if (form.items.some(item => !Number.isFinite(Number(item.score)) || Number(item.score) < 0)) return ElMessage.warning('建议分值应为非负数字')
  saving.value = true
  try {
    const payload = { 
      category_id: props.category.id, 
      name: form.name.trim(), 
      description: form.description, 
      is_active: form.is_active, 
      items: form.items }
    const response = form.id ? await updateWorkPackageTemplateApi(form.id, payload) : await createWorkPackageTemplateApi(payload)
    const saved = response.data.data
    const index = templates.value.findIndex(item => item.id === saved.id)
    if (index < 0) templates.value.unshift(saved)
    else templates.value[index] = saved
    selectTemplate(saved)
    ElMessage.success('模板已保存')
  } catch (error) { ElMessage.error(error.response?.data?.detail || '保存模板失败') }
  finally { saving.value = false }
}
async function remove() {
  if (!form.id) return
  try { await ElMessageBox.confirm(`确定删除模板“${form.name}”吗？`, '删除模板', { type: 'warning' }) }
  catch { return }
  saving.value = true
  try {
    await deleteWorkPackageTemplateApi(form.id)
    templates.value = templates.value.filter(item => item.id !== form.id)
    newTemplate()
    ElMessage.success('模板已删除')
  } catch (error) { ElMessage.error(error.response?.data?.detail || '删除模板失败') }
  finally { saving.value = false }
}
</script>

<style scoped>
/* 弹窗本身不滚动，只让中间内容滚动，标题和关闭按钮固定在顶部。 */
:global(body .el-dialog.work-package-template-dialog) { display: flex; flex-direction: column; max-height: 90dvh; overflow: hidden; }
:global(body .work-package-template-dialog .el-dialog__header),
:global(body .work-package-template-dialog .el-dialog__footer) { flex: none; }
:global(body .work-package-template-dialog .el-dialog__body) { flex: 1 1 auto; min-height: 0; overflow-y: auto; }
.template-layout { display: grid; grid-template-columns: 200px minmax(0, 1fr); gap: 20px; }
.template-list { border-right: 1px solid #e5eaf3; padding-right: 16px; }
.template-option { 
  display: flex; 
  align-items: 
  center; 
  justify-content: space-between; 
  gap: 8px; 
  padding: 12px; 
  cursor: pointer; 
  border-radius: 8px; 
  margin-top: 6px; }
.template-option:hover, .template-option.selected { background: #ecf4ff; }
.template-editor { min-width: 0; }
.template-fields { display: grid; grid-template-columns: minmax(0, 1fr) 120px; gap: 16px; }
.items-heading { display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px; }
.template-hint { color: #64748b; font-size: 13px; }
.item-actions { display: flex; align-items: center; justify-content: center; gap: 2px; white-space: nowrap; }
.item-action.el-button { width: 28px; height: 28px; padding: 0; margin: 0; border-radius: 6px; }
.item-action-text.el-button { width: 42px; }
.item-action.el-button:not(:disabled):hover { background: #edf4ff; }
.item-action.el-button--danger:not(:disabled):hover { background: #fff1f0; }
@media (max-width: 700px) { 
  .template-layout { grid-template-columns: 1fr; } 
  .template-list { border-right: 0; border-bottom: 1px solid #e5eaf3; } }
</style>
