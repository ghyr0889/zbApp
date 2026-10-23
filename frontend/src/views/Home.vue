<!-- 主页面 -->
<template>
  <main class="home-page">
    <PageIntro title="我的工作台" description="查看个人信息与公告，选择应用开始工作。" />
    <div class="home-grid">
      <el-card shadow="never" class="home-card">
        <template #header><h2>个人信息</h2></template>
        <div class="profile-summary">
          <el-avatar :size="80" class="user-avatar">{{ user.username?.charAt(0) || 'U' }}</el-avatar>
          <dl>
            <div><dt>姓名</dt><dd>{{ user.username || '—' }}</dd></div>
            <div><dt>工号</dt><dd>{{ user.id || '—' }}</dd></div>
            <div><dt>科室</dt><dd>{{ user.department || '未分配' }}</dd></div>
            <div><dt>角色</dt><dd>{{ roleName }}</dd></div>
          </dl>
        </div>
        <div class="profile-actions">
          <el-button type="primary" plain @click="$router.push('/personal-info')">查看个人信息</el-button>
        </div>
      </el-card>

      <el-card shadow="never" class="home-card">
        <template #header>
          <div class="announcement-heading">
            <h2>公告板</h2>
            <router-link to="/announcements">更多 ›</router-link>
          </div>
        </template>
        <div v-loading="loading" class="announcement-list">
          <div v-if="listError" class="load-error" role="alert">
            <p>{{ listError }}</p>
            <el-button @click="loadAnnouncements">重新加载</el-button>
          </div>
          <template v-else>
            <ul v-if="items.length">
              <li v-for="item in items" :key="item.id">
                <el-tag v-if="item.is_pinned" size="small" type="danger">置顶</el-tag>
                <button class="announcement-title" :title="item.title" @click="openDetail(item.id)">{{ item.title }}</button>
                <time>{{ formatDate(item.published_at) }}</time>
              </li>
            </ul>
            <el-empty v-else-if="!loading" description="暂无公告" :image-size="90" />
          </template>
        </div>
      </el-card>
    </div>

    <ApplicationCenter />

    <el-dialog v-model="detailVisible" title="公告详情" width="min(900px, 94vw)" top="6vh" @closed="clearDetail">
      <div v-loading="detailLoading" class="announcement-detail">
        <template v-if="detail">
          <h2>{{ detail.title }}</h2>
          <p class="detail-meta">发布人工号：{{ detail.publisher_id }}　发布时间：{{ formatDate(detail.published_at, true) }}</p>
          <el-divider />
          <!-- 使用文本插值展示正文，保留换行，不执行公告中的 HTML。 -->
          <div class="detail-content">{{ detail.content }}</div>
        </template>
      </div>
    </el-dialog>
  </main>
</template>

<script setup>
import PageIntro from '../components/PageIntro.vue'
import ApplicationCenter from '../components/ApplicationCenter.vue'
import { computed, onMounted, onBeforeUnmount, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { useUserStore } from '../stores/user'
import { getAnnouncementsApi, getAnnouncementDetailApi } from '../api'

const userStore = useUserStore()
const user = computed(() => userStore.userInfo || {})
const roleName = computed(() => ({ ADMIN: '管理员', LEADER: '领导', DEPARTMENT: '科室主任', EMPLOYEE: '普通员工' }[userStore.role] || '—'))
const items = ref([])
const loading = ref(false)
const listError = ref('')
const detailVisible = ref(false)
const detailLoading = ref(false)
const detail = ref(null)
let listRequest = 0
let detailRequest = 0

const formatDate = (value, full = false) => value ? String(value).replace('T', ' ').slice(0, full ? 19 : 10) : '—'

async function loadAnnouncements() {
  const request = ++listRequest
  loading.value = true
  listError.value = ''
  try {
    // 复用“收到的公告”接口，由后端过滤权限，并按置顶、发布时间排序。
    const { data } = await getAnnouncementsApi({ page: 1, page_size: 6 })
    if (request !== listRequest) return
    items.value = data.data.items
  } catch {
    if (request === listRequest) listError.value = '公告加载失败，请稍后重试'
  } finally {
    if (request === listRequest) loading.value = false
  }
}

async function openDetail(id) {
  const request = ++detailRequest
  detail.value = null
  detailVisible.value = true
  detailLoading.value = true
  try {
    // 再次请求详情，使已撤回或已失去查看权限的公告不能只凭首页缓存打开。
    const { data } = await getAnnouncementDetailApi(id)
    if (request === detailRequest) detail.value = data
  } catch (error) {
    if (request !== detailRequest) return
    detailVisible.value = false
    const message = error.response?.data?.detail
    ElMessage.error(typeof message === 'string' ? message : '公告不存在或无权查看')
  } finally {
    if (request === detailRequest) detailLoading.value = false
  }
}

function clearDetail() {
  detailRequest++
  detail.value = null
  detailLoading.value = false
}
onMounted(loadAnnouncements)
onBeforeUnmount(() => { listRequest++; detailRequest++ })
</script>

<style scoped>
.home-page { width: 100%; max-width: 1280px; margin: 0 auto; padding: 24px 20px; box-sizing: border-box; }
.home-grid { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 2fr); gap: 20px; align-items: stretch; }
.home-card { border: none; border-radius: 12px; min-width: 0; background: #fff; box-shadow: none; }
.home-card :deep(.el-card__header) { margin: 0 20px; padding: 20px 0 12px; border-bottom: 1px solid #e5e5e5; }
.home-card :deep(.el-card__body) { padding: 20px; }
/* 栏目标题下的短横线与截图一致。 */
.home-card h1 { position: relative; width: fit-content; }
.home-card h1::after { content: ''; position: absolute; left: 0; right: 0; bottom: -13px; height: 2px; background: #409eff; }
.profile-actions :deep(.el-button) { border-radius: 20px; color: #409eff; background: #fff; border-color: #dcdfe6; }
.profile-actions :deep(.el-button:hover) { background: #eef8fd; border-color: #409eff; }
h1 { margin: 0; font-size: 18px; font-weight: 600; color: #409eff; }
.announcement-heading { display: flex; justify-content: space-between; align-items: center; }
.announcement-heading a { font-size: 14px; color: #606266; text-decoration: none; }
.announcement-heading a:hover { color: #409eff; }
.profile-summary { display: flex; align-items: center; gap: 22px; padding: 16px 0; }
.profile-summary .el-avatar { flex-shrink: 0; font-size: 28px; }
dl { margin: 0; min-width: 0; flex: 1; font-size: 14px; overflow-x: auto; }
dl > div { display: grid; grid-template-columns: 4em max-content; column-gap: 12px; margin: 14px 0; line-height: 1.6; }
dt { color: #737f90; white-space: nowrap; }
dd { margin: 0; color: #303133; white-space: nowrap; }
.profile-actions { padding: 20px 0 10px; text-align: center; }
.announcement-list { min-height: 280px; }
ul { margin: 0; padding: 0; list-style: none; }
li { display: flex; align-items: center; gap: 10px; min-height: 44px; border-bottom: none; }
li:last-child { border-bottom: none; }
.announcement-title { flex: 1; min-width: 0; padding: 10px 0; border: none; background: none; color: #303133; font: inherit; font-size: 14px; text-align: left; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; cursor: pointer; }
.announcement-title:hover { color: #409eff; }
time { color: #777; font-size: 13px; white-space: nowrap; }
.load-error { text-align: center; color: #909399; padding: 50px 0; }
.announcement-detail { min-height: 160px; max-height: 65vh; overflow-y: auto; overflow-wrap: anywhere; }
.announcement-detail h2 { color: #303133; }
.detail-meta { color: #909399; font-size: 13px; line-height: 1.8; }
.detail-content { white-space: pre-wrap; line-height: 2; color: #303133; }
@media (max-width: 900px) { .home-grid { grid-template-columns: 1fr; } .home-page { padding: 20px 12px; } }
@media (max-width: 480px) { .profile-summary { flex-direction: column; align-items: stretch; gap: 12px; } .profile-summary .el-avatar { align-self: flex-start; } }
</style>
