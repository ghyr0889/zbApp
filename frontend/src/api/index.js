import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 5000
})

export const getPublicScoreBoardApi = (period, year, month, quarter) => {
  const params = { period, year, month, quarter }
  Object.keys(params).forEach(k => {
    if (params[k] === '' || params[k] === null || params[k] === undefined) delete params[k]
  })
  return api.get('/score-board/public-score-board', { params })
}

export const getAllUsersApi = () => api.get('/admin/users')
export const createUserApi = (data) => api.post('/admin/users', data)
export const deleteUserApi = (userId) => api.delete(`/admin/users/${userId}`)
export const updateUserApi = (userId,data) => api.put(`/admin/users/${userId}`, data)
// 修改自己的登录密码（校验旧密码）
export const changePasswordApi = (data) => api.put('/auth/password', data) 

export const getAllProjectsApi = () => api.get('/admin/projects')
export const createProjectApi = (data) => api.post('/admin/projects', data)
export const deleteProjectApi = (projectId, userId) => api.delete(`/admin/projects/${projectId}`,{params: { user_id: userId}})

export const createWorkPackageApi = (data) => api.post('/admin/work-packages', data)

export const initiateTransferApi = (data) => api.post('/transfers/initiate', data)
export const getIncomingTransfersApi = (userId) => api.get(`/transfers/my-incoming?user_id=${userId}`)
export const processTransferApi = (transferId, action) => api.post(`/transfers/process?transfer_id=${transferId}&action=${action}`)
export const getMyOutgoingTransfersApi = (userId) => api.get(`/transfers/my-outgoing?user_id=${userId}`)

export const userLoginApi = (data) => api.post('/auth/user-login', data)
export const adminLoginApi = (data) => api.post('/auth/admin-login', data)


// 工作项管理（工作包 → 工作项）
export const getWorkItemsApi = (workPackageId) => api.get(`/work-logs/work-packages/${workPackageId}/work-items`)
export const deleteWorkPackageApi = (workPackageId, userId) => api.delete(`/admin/work-packages/${workPackageId}`,{params: { user_id: userId}})
export const deleteWorkItemApi = (workItemId) => api.delete(`/work-logs/work-items/${workItemId}`)

// 确认/取消完成（负责人手动标记）
export const confirmCompletionApi = (data) => api.put('/work-logs/confirm-completion', data)

// 项目总览分页/筛选（大数据量）
export const getPagedProjectsApi = (params) => api.get('/work-logs/projects', { params })
export const getProjectDetailApi = (projectId) => api.get(`/work-logs/projects/${projectId}`)
export const getPagedProjectWorkPackagesApi = (projectId, params) =>
  api.get(`/work-logs/projects/${projectId}/work-packages`, { params })
export const getMyWorkPackagesPagedApi = (userId, params) =>
  api.get(`/work-logs/my-work-packages/${userId}`, { params })
// 保存工作项本月分值（直接生效，不经过审核）
export const saveMonthScoreApi = (workItemId, data) => api.put(`/score-board/work-items/${workItemId}/month-score`, data)

// 工作包拆分申请（员工申请拆解工作包 → 领导审核）
export const createSplitRequestApi = (data) => api.post('/review/split-requests', data)
export const getSplitRequestsApi = (userId) => api.get(`/review/split-requests?user_id=${userId}`)
export const reviewSplitRequestApi = (requestId, data) => api.post(`/review/split-requests/${requestId}/review`, data)

export const saveQualityScoreApi = (workItemId, data) =>
  api.put(`/score-board/work-items/${workItemId}/quality_score`, data)

export const updateMonthlyExtraScoreApi = (data) => api.put('/score-board/monthly-extra-scores', data)

// 后台管理：计算得分系数
export const getComputedScoreDimensionsApi = () => api.get('/admin/computed-score-dimensions')
export const putComputedScoreDimensionsApi = (data) => api.put('/admin/computed-score-dimensions', data)

// 后台管理：档位字典（职级/难度/重要度/创新度）
export const getLevelDefsApi = () => api.get('/admin/level-defs')
export const putLevelDefsApi = (data) => api.put('/admin/level-defs', data)

export default api
