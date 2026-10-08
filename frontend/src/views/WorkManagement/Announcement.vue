<template>
  <div class="announcements-page">
    <el-card shadow="never">
      <template #header>
        <div class="page-header">
          <div>
            <h2>公告板</h2>
            <span class="description">查看通知，管理自己发布的公告</span>
          </div>

          <div>
            <el-button :loading="loading" @click="fetchList"> 刷新 </el-button>

            <el-button
              v-if="canPublish"
              type="primary"
              @click="openCreate"
            >
              新建公告
            </el-button>
          </div>
        </div>
      </template>

      <el-tabs v-model="activeTab" @tab-change="handleTabChange">
        <el-tab-pane label="收到的公告" name="received" />
        <el-tab-pane label="我的公告" name="mine" />
      </el-tabs>

      <el-table
        :data="items"
        v-loading="loading"
        border
        stripe
        empty-text="暂无公告"
      >
        <el-table-column label="公告标题" min-width="260">
          <template #default="{ row }">
            <div class="title-cell">
              <el-tag v-if="row.is_pinned"  type="danger"  size="small" >
                置顶
              </el-tag>
              <el-link type="primary" @click="openDetail(row.id)">
                {{ row.title }}
              </el-link>
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="publisher_id" label="发布人工号" width="130" />

        <el-table-column v-if="activeTab === 'mine'" label="状态" width="100" >
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)">
              {{ statusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="发布时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.published_at) }}
          </template>
        </el-table-column>

        <el-table-column label="操作" width="200">
          <template #default="{ row }">
            <el-button link type="primary" @click="openDetail(row.id)" >
              查看
            </el-button>

            <template v-if="activeTab === 'mine'">
              <el-button v-if=" canPublish && ['DRAFT', 'WITHDRAWN'].includes(row.status) "
                link
                type="success"
                :disabled="actionId !== null"
                :loading="actionId === row.id"
                @click="changeStatus(row, 'publish')"
              >
                {{ row.status === 'WITHDRAWN' ? '重新发布' : '发布' }}
              </el-button>

              <el-button
                v-if="row.status === 'PUBLISHED'"
                link
                type="danger"
                :disabled="actionId !== null"
                :loading="actionId === row.id"
                @click="changeStatus(row, 'withdraw')"
              >
                撤回
              </el-button>
            </template>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50]"
          :total="total"
          layout="total, sizes, prev, pager, next"
          background
          @current-change="fetchList"
          @size-change="handleSizeChange"
        />
      </div>
    </el-card>

    <!-- 查看详情：正文使用文本插值，不执行用户输入的 HTML。 -->
    <el-dialog
      v-model="detailVisible"
      title="公告详情"
      width="min(900px, 94vw)"
      top="6vh"
      @closed="clearDetail"
    >
      <div v-loading="detailLoading" class="detail-container">
        <template v-if="detail">
          <h2>{{ detail.title }}</h2>

          <div class="detail-meta">
            <span>发布人工号：{{ detail.publisher_id }}</span>
            <span>发布时间：{{ formatTime(detail.published_at) }}</span>
            <el-tag :type="statusType(detail.status)">
              {{ statusText(detail.status) }}
            </el-tag>
          </div>

          <p class="description"> 接收范围：{{ audienceText(detail) }} </p>
          <el-divider />

          <div class="announcement-content">{{ detail.content }}</div>
        </template>
      </div>
    </el-dialog>

    <!-- 创建公告：先保存草稿，再从“我的公告”中发布。 -->
    <el-dialog
      v-model="createVisible"
      title="新建公告"
      width="min(680px, 94vw)"
      :close-on-click-modal="false"
      :close-on-press-escape="!saving"
      :show-close="!saving"
    >
      <el-form label-position="top">
        <el-form-item label="公告标题" required>
          <el-input
            v-model="form.title"
            maxlength="200"
            show-word-limit
            placeholder="请输入公告标题"
          />
        </el-form-item>

        <el-form-item label="公告正文" required>
          <el-input
            v-model="form.content"
            type="textarea"
            :rows="10"
            placeholder="请输入公告内容，支持换行"
          />
        </el-form-item>

        <el-form-item label="可见范围" required>
          <el-select
            v-model="form.audience_mode"
            style="width: 100%"
            @change="form.roles = []"
          >
            <el-option label="所有登录用户" value="ALL" />
            <el-option label="指定角色" value="ROLE" />
          </el-select>
        </el-form-item>

        <el-form-item
          v-if="form.audience_mode === 'ROLE'"
          label="可见范围"
          required
        >
          <el-select
            v-model="form.roles"
            multiple
            placeholder="请选择可见范围"
            style="width: 100%"
          >
            <el-option
              v-for="option in roleOptions"
              :key="option.value"
              :label="option.label"
              :value="option.value"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="是否置顶">
          <el-switch v-model="form.is_pinned" />
        </el-form-item>

        <el-alert
          title="保存后为草稿，接收者暂时看不到。请在“我的公告”中点击发布。"
          type="info"
          :closable="false"
          show-icon
        />
      </el-form>

      <template #footer>
        <el-button :disabled="saving" @click="createVisible = false">
          取消
        </el-button>

        <el-button
          type="primary"
          :loading="saving"
          @click="saveDraft"
        >
          保存草稿
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, onBeforeUnmount, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useUserStore } from '../../stores/user'
import {
  getAnnouncementsApi,
  getMyAnnouncementsApi,
  getAnnouncementDetailApi,
  createAnnouncementApi,
  publishAnnouncementApi,
  withdrawAnnouncementApi,
} from '../../api'

const userStore = useUserStore()

// 与当前后端 PUBLISH_ROLES 保持一致。
// 前端按钮控制只是显示逻辑，最终权限仍由后端检查。
const canPublish = computed(() =>
  ['ADMIN', 'LEADER'].includes(userStore.role)
)

const roleOptions = [
  { label: '员工', value: 'EMPLOYEE' },
  { label: '科室主任', value: 'DEPARTMENT' },
  { label: '领导', value: 'LEADER' },
  { label: '管理员', value: 'ADMIN' },
]

const activeTab = ref('received')
const items = ref([])
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)
const loading = ref(false)
const actionId = ref(null)

const detailVisible = ref(false)
const detailLoading = ref(false)
const detail = ref(null)

const createVisible = ref(false)
const saving = ref(false)

const emptyForm = () => ({
  title: '',
  content: '',
  audience_mode: 'ALL',
  roles: [],
  is_pinned: false,
})

const form = reactive(emptyForm())

// 请求序号用于避免快速切换标签或公告时，旧响应覆盖新结果。
let listRequestId = 0
let detailRequestId = 0

const statusText = status => ({
  DRAFT: '草稿',
  PUBLISHED: '已发布',
  WITHDRAWN: '已撤回',
}[status] || status || '-')

const statusType = status => ({
  DRAFT: 'info',
  PUBLISHED: 'success',
  WITHDRAWN: 'warning',
}[status] || 'info')

// 直接展示后端日期字符串，避免浏览器自行转换时区。
const formatTime = value =>
  value ? String(value).replace('T', ' ').slice(0, 19) : '-'

const audienceText = announcement => {
  if (announcement.audience_mode === 'ALL') return '所有登录用户'

  return (announcement.roles || [])
    .map(role =>
      roleOptions.find(option => option.value === role)?.label || role
    )
    .join('、') || '未设置'
}

const showError = (error, fallback) => {
  const message = error.response?.data?.detail

  ElMessage.error(
    typeof message === 'string' ? message : fallback
  )
}

async function fetchList() {
  const requestId = ++listRequestId
  loading.value = true

  try {
    const queryApi = activeTab.value === 'mine'
      ? getMyAnnouncementsApi
      : getAnnouncementsApi

    const res = await queryApi({
      page: page.value,
      page_size: pageSize.value,
    })

    if (requestId !== listRequestId) return

    // 两个列表接口都有 code、data 包装。
    items.value = res.data.data.items
    total.value = res.data.data.total
  } catch (error) {
    if (requestId !== listRequestId) return
    items.value = []
    total.value = 0
    showError(error, '加载公告失败')
  } finally {
    if (requestId === listRequestId) loading.value = false
  }
}

function handleTabChange() {
  page.value = 1
  items.value = []
  total.value = 0
  fetchList()
}

function handleSizeChange() {
  page.value = 1
  fetchList()
}

async function openDetail(id) {
  const requestId = ++detailRequestId

  // 先清除上一次正文，防止加载时显示旧公告。
  detail.value = null
  detailVisible.value = true
  detailLoading.value = true

  try {
    const res = await getAnnouncementDetailApi(id)

    if (requestId !== detailRequestId) return

    // 详情接口直接返回公告对象。
    detail.value = res.data
  } catch (error) {
    if (requestId !== detailRequestId) return

    detailVisible.value = false
    showError(error, '公告不存在或无权查看')
  } finally {
    if (requestId === detailRequestId) detailLoading.value = false
  }
}

function clearDetail() {
  detailRequestId++
  detail.value = null
  detailLoading.value = false
}

function openCreate() {
  Object.assign(form, emptyForm())
  createVisible.value = true
}

async function saveDraft() {
  if (saving.value) return

  if (!form.title.trim()) {
    return ElMessage.warning('请输入公告标题')
  }

  if (!form.content.trim()) {
    return ElMessage.warning('请输入公告正文')
  }

  if (form.audience_mode === 'ROLE' && !form.roles.length) {
    return ElMessage.warning('请选择至少一个接收角色')
  }

  saving.value = true

  try {
    await createAnnouncementApi({
      title: form.title.trim(),
      content: form.content.trim(),
      audience_mode: form.audience_mode,
      roles: form.audience_mode === 'ROLE' ? [...form.roles] : [],
      is_pinned: form.is_pinned,
    })

    ElMessage.success('草稿已保存，请在“我的公告”中发布')
    createVisible.value = false
    activeTab.value = 'mine'
    page.value = 1
    await fetchList()
  } catch (error) {
    showError(error, '保存草稿失败')
  } finally {
    saving.value = false
  }
}

async function changeStatus(row, action) {
  if (actionId.value !== null) return

  const isPublish = action === 'publish'

  try {
    await ElMessageBox.confirm(
      isPublish
        ? '发布后，符合接收范围的用户即可查看这条公告。'
        : '撤回后，接收者将无法继续通过列表或详情查看这条公告。',
      isPublish ? '确认发布' : '确认撤回',
      {
        confirmButtonText: isPublish ? '发布' : '撤回',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
  } catch {
    return
  }

  actionId.value = row.id

  try {
    if (isPublish) {
      await publishAnnouncementApi(row.id)
    } else {
      await withdrawAnnouncementApi(row.id)
    }

    ElMessage.success(isPublish ? '公告已发布' : '公告已撤回')
    await fetchList()
  } catch (error) {
    showError(error, isPublish ? '发布失败' : '撤回失败')
  } finally {
    actionId.value = null
  }
}

onMounted(fetchList)

onBeforeUnmount(() => {
  // 离开页面后，不再接收旧列表和详情请求的结果。
  listRequestId++
  detailRequestId++
})
</script>

<style scoped>
.announcements-page {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}

.page-header h2 {
  margin: 0 0 6px;
  font-size: 22px;
}

.description {
  color: #64748b;
  font-size: 13px;
}

.title-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.pagination {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
  overflow-x: auto;
}

.detail-container {
  min-height: 160px;
  max-height: 65vh;
  overflow-y: auto;
  padding: 0 16px 16px;
  box-sizing: border-box;
}

.detail-meta {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
  color: #64748b;
  font-size: 13px;
}

.announcement-content {
  white-space: pre-wrap;   /* 保留输入时的换行 */
  overflow-wrap: anywhere; /* 长链接等内容自动换行 */
  line-height: 2;
  font-size: 16px;
  color: #334155;
}

@media (max-width: 600px) {
  .announcements-page {
    padding: 10px;
  }
}
</style>