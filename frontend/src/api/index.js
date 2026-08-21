import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 5000
})

export const loginApi = (data) => api.post('/auth/login', data)

export const getMyAssignedWorkPackagesApi = (userId) => api.get(`/work-logs/my-assigned-work-packages/${userId}`)

export const getPublicScoreBoardApi = (period, year, month, quarter) => {
  const params = { period, year, month, quarter }
  Object.keys(params).forEach(k => {
    if (params[k] === '' || params[k] === null || params[k] === undefined) delete params[k]
  })
  return api.get('/score-board/public-score-board', { params })
}

export const getPublicWorkPackagesApi = () => api.get('/work-logs/public-work-packages')

export const getAllUsersApi = () => api.get('/admin/users')
export const createUserApi = (data) => api.post('/admin/users', data)
export const deleteUserApi = (userId) => api.delete(`/admin/users/${userId}`)
export const updateUserApi = (userId) => api.put(`/admin/user/${userId}`, data)
// 修改自己的登录密码（校验旧密码）
export const changePasswordApi = (data) => api.put('/auth/password', data) 

export const getAllProjectsApi = () => api.get('/admin/projects')
export const createProjectApi = (data) => api.post('/admin/projects', data)

export const getWorkPackagesOverviewApi = () => api.get('/admin/work-packages-overview')

export const createWorkPackageApi = (data) => api.post('/admin/work-packages', data)

export const initiateTransferApi = (data) => api.post('/transfers/initiate', data)
export const getIncomingTransfersApi = (userId) => api.get(`/transfers/my-incoming?user_id=${userId}`)
export const processTransferApi = (transferId, action) => api.post(`/transfers/process?transfer_id=${transferId}&action=${action}`)
export const getMyOutgoingTransfersApi = (userId) => api.get(`/transfers/my-outgoing?user_id=${userId}`)

// 审核通过接口
export const taskAssignmentApi = (data) => api.post('/review/projects/assign', data)


export const userLoginApi = (data) => api.post('/auth/user-login', data)
export const adminLoginApi = (data) => api.post('/auth/admin-login', data)


// 工作项管理（工作包 → 工作项）
export const getWorkItemsApi = (workPackageId) => api.get(`/work-logs/work-packages/${workPackageId}/work-items`)
export const deleteWorkItemApi = (workItemId) => api.delete(`/work-logs/work-items/${workItemId}`)
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
