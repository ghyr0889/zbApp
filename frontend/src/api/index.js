import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 5000
})

// 只在统一的 API 实例中携带真实令牌，不能使用用户 ID 充当 Bearer 凭证。
api.interceptors.request.use(config => {
  const token = sessionStorage.getItem('access_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// 由入口注入清理登录状态的回调，避免 API、用户 store、router 循环导入。
let unauthorizedHandler = null
export const setUnauthorizedHandler = handler => { unauthorizedHandler = handler }
api.interceptors.response.use(response => response, error => {
  const token = sessionStorage.getItem('access_token')
  const sentToken = error.config?.headers?.Authorization
  // 仅处理当前会话的 401；旧请求迟到的响应不能清除刚刚重新登录的新会话。
  // 403 是业务权限不足，不退出登录。
  if (error.response?.status === 401 && token && sentToken === `Bearer ${token}`) {
    unauthorizedHandler?.()
  }
  return Promise.reject(error)
})

export const getCurrentUserApi = () => api.get('/auth/me')
export const logoutApi = () => api.post('/auth/logout')

export const getPublicScoreBoardApi = (period, year, month, quarter) => {
  const params = { period, year, month, quarter }
  Object.keys(params).forEach(k => {
    if (params[k] === '' || params[k] === null || params[k] === undefined) delete params[k]
  })
  return api.get('/score-board/public-score-board', { params })
}

// 项目汇总（项目/工作包 分值汇总，按 月/季/年/全部）
export const getProjectSummaryApi = (params) => api.get('/score-board/project-summary', { params })

export const getAllUsersApi = () => api.get('/admin/users')
export const createUserApi = (data) => api.post('/admin/users', data)
export const deleteUserApi = (userId, currentUserId) => api.delete(`/admin/users/${userId}`, { params: { currentUserId } })
export const updateUserApi = (userId,data) => api.put(`/admin/users/${userId}`, data)
// 修改自己的登录密码（校验旧密码）
export const changePasswordApi = (data) => api.put('/auth/password', data) 

export const getAllProjectsApi = () => api.get('/admin/projects')
export const createProjectApi = (data) => api.post('/admin/projects', data)
export const deleteProjectApi = (projectId, userId) => api.delete(`/admin/projects/${projectId}`,{params: { user_id: userId}})

export const createWorkPackageApi = (data) => api.post('/admin/work-packages', data)
// 工作包类别（来自数据库 work_project_categories 表）
export const getWorkCategoriesApi = () => api.get('/admin/work-categories')

export const initiateTransferApi = (data) => api.post('/transfers/initiate', data)
export const getIncomingTransfersApi = (userId) => api.get(`/transfers/my-incoming?user_id=${userId}`)
export const processTransferApi = (transferId, action) => api.post(`/transfers/process?transfer_id=${transferId}&action=${action}`)
export const getMyOutgoingTransfersApi = (userId) => api.get(`/transfers/my-outgoing?user_id=${userId}`)

export const userLoginApi = (data) => api.post('/auth/user-login', data)
export const adminLoginApi = (data) => api.post('/auth/admin-login', data)


// 工作项管理（工作包 → 工作项）
export const getWorkItemsApi = (workPackageId, params) =>
  api.get(`/work-logs/work-packages/${workPackageId}/work-items`, { params })
export const deleteWorkPackageApi = (workPackageId, userId) => api.delete(`/admin/work-packages/${workPackageId}`,{params: { user_id: userId}})
export const deleteWorkItemApi = (workItemId) => api.delete(`/work-logs/work-items/${workItemId}`)

// 确认/取消完成（负责人手动标记）
export const confirmCompletionApi = (data) => api.put('/work-logs/confirm-completion', data)

// 工作项完成审核（进度满 / 手动提交 → 技术负责人审核）
export const createCompleteRequestApi = (data) => api.post('/complete_review/complete-requests', data)
export const getCompleteRequestsApi = (userId) =>
  api.get('/complete_review/complete-requests', { params: { user_id: userId } })
export const reviewCompleteRequestApi = (requestId, data) =>
  api.post(`/complete_review/complete-requests/${requestId}/review`, data)

// 确认/取消关闭（负责人手动标记）
export const confirmClosedApi = (data) => api.put('/work-logs/confirm-closed', data)

// 项目总览分页/筛选（大数据量）
export const getPagedProjectsApi = (params) => api.get('/work-logs/projects', { params })
export const getProjectDetailApi = (projectId) => api.get(`/work-logs/projects/${projectId}`)
export const getPagedProjectWorkPackagesApi = (projectId, params) =>
  api.get(`/work-logs/projects/${projectId}/work-packages`, { params })
export const getMyWorkPackagesPagedApi = (userId, params) =>
  api.get(`/work-logs/my-work-packages/${userId}`, { params })
// 保存工作项本月分值（直接生效，不经过审核）
export const saveMonthScoreApi = (workItemId, data) => api.put(`/score-board/work-items/${workItemId}/month-score`, data)
//工作完成情况汇总
export const getCompletedSituationApi = (params) => api.get('/score-board/completed-situation', { params })
// 工作包拆分申请（员工申请拆解工作包 → 领导审核）
export const createSplitRequestApi = (data) => api.post('/review/split-requests', data)
export const getSplitRequestsApi = (userId) => api.get(`/review/split-requests?user_id=${userId}`)
export const reviewSplitRequestApi = (requestId, data) => api.post(`/review/split-requests/${requestId}/review`, data)
export const editSplitRequestApi = (requestId, body) => api.put(`/review/split-requests/${requestId}`, body)
export const removeSplitItemApi = (requestId, body) => api.post(`/review/split-requests/${requestId}/remove-item`, body)

export const saveQualityScoreApi = (workItemId, data) =>
  api.put(`/score-board/work-items/${workItemId}/quality_score`, data)

export const updateMonthlyExtraScoreApi = (data) => api.put('/score-board/monthly-extra-scores', data)

// 后台管理：计算得分系数
export const getComputedScoreDimensionsApi = () => api.get('/admin/computed-score-dimensions')
export const putComputedScoreDimensionsApi = (data) => api.put('/admin/computed-score-dimensions', data)

// 后台管理：档位字典（职级/难度/重要度/创新度）
export const getLevelDefsApi = () => api.get('/admin/level-defs')
export const putLevelDefsApi = (data) => api.put('/admin/level-defs', data)
// 全局红点提示：待办数量汇总（菜单红点 = review + complete + transfers）
export const getPendingSummaryApi = (userId) => api.get('/pending/summary', { params: { user_id: userId } })

//登录认证 拉取个人信息
export const getUserProfileApi = (userId) => api.get(`/auth/profile/${encodeURIComponent(userId)}`)

// 创建公告，后端默认保存为草稿。
export const createAnnouncementApi = data => api.post('/announcements', data)
// 收到的公告：后端根据登录用户筛选可见范围。
export const getAnnouncementsApi = params => api.get('/announcements', { params })
// 查看公告详情
export const getAnnouncementDetailApi = announcementId => api.get(`/announcements/${announcementId}`)
// 查询当前登录用户创建的公告
export const getMyAnnouncementsApi = params => api.get('/announcements/mine', { params })
// 发布已有草稿或重新发布已撤回公告。
export const publishAnnouncementApi = id => api.post(`/announcements/${id}/publish`)
// 撤回指定公告
export const withdrawAnnouncementApi = announcementId => api.post(`/announcements/${announcementId}/withdraw`)

export default api

// 后台信息管理：统一的科室选项与工作包类型维护。
export const getDepartmentOptionsApi = () => api.get('/admin/departments')
export const getInformationApi = kind => api.get(`/admin/information/${kind}`)
export const createInformationApi = (kind, data) => api.post(`/admin/information/${kind}`, data)
export const updateInformationApi = (kind, id, data) => api.put(`/admin/information/${kind}/${id}`, data)

export const getChartOptionsApi = (userId) => api.get('/analytics/options', { params: { user_id: userId }, timeout: 30000 })
export const getCustomChartApi = (data) => api.post('/analytics/chart', data, { timeout: 30000 })
