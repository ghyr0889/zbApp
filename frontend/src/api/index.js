import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 5000
})

export const loginApi = (data) => api.post('/auth/login', data)

export const getMyAssignedWorkPackagesApi = (userId) => api.get(`/work-logs/my-assigned-work-packages/${userId}`)
export const createLogApi = (data) => api.post('/work-logs', data)
export const getMyLogsApi = (userId) => api.get(`/work-logs/my/${userId}`)
export const getPendingLogsApi = (ownerId) => api.get(`/review/reviews/pending?user_id=${ownerId}`)

export const getScoreBoardApi = (userId, period) => api.get(`/work-logs/score-board/${userId}?period=${period}`)
export const getPublicScoreBoardApi = (period) => api.get(`/work-logs/public-score-board?period=${period}`)
export const getCascadeOptionsApi = (userId) => api.get(`/work-logs/cascade-options?user_id=${userId}`)
export const getPublicWorkPackagesApi = () => api.get('/work-logs/public-work-packages')

export const getAllUsersApi = () => api.get('/admin/users')
export const createUserApi = (data) => api.post('/admin/users', data)
export const getAllProjectsApi = () => api.get('/admin/projects')
export const createProjectApi = (data) => api.post('/admin/projects', data)
export const getWorkPackagesOverviewApi = () => api.get('/admin/work-packages-overview')
export const createWorkPackageApi = (data) => api.post('/admin/work-packages', data)
export const assignTaskApi = (data) => api.post('/admin/assign-task', data)

export const initiateTransferApi = (data) => api.post('/transfers/initiate', data)
export const getIncomingTransfersApi = (userId) => api.get(`/transfers/my-incoming?user_id=${userId}`)
export const processTransferApi = (transferId, action) => api.post(`/transfers/process?transfer_id=${transferId}&action=${action}`)
export const reviewLogApi = (logId,data) => api.post(`/review/${logId}`, data)

// 审核通过接口 (带上 weight 参数)
export const approveReviewApi = (logId, weight) => {
  return api.post(`/reviews/${logId}/approve`, { weight: weight })
}

export const deleteUserApi = (userId) => api.delete(`/users/${userId}`)
export default api
