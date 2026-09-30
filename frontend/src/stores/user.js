import { defineStore } from 'pinia'
import { getPendingSummaryApi, getCurrentUserApi, logoutApi } from '../api'

const STORAGE_KEY = 'user_info'

// 三个页签各自的待办数量，初始全 0
const emptyPending = () => ({ review: 0, complete: 0, transfers: 0 })

function readStoredUser() {
  // 用户与令牌按标签页配对，避免另一标签页登录其他账号后串用身份。
  if (!sessionStorage.getItem('access_token')) return null
  const raw = sessionStorage.getItem(STORAGE_KEY)
  if (!raw) return null

  try {
    return JSON.parse(raw)
  } catch {
    sessionStorage.removeItem(STORAGE_KEY)
    return null
  }
}

export const useUserStore = defineStore('user', {
  state: () => ({
    userInfo: readStoredUser(),
    accessToken: sessionStorage.getItem('access_token') || '',
    sessionChecked: false,
    // 菜单红点 / 三个页签角标共用的待办计数（不持久化）
    pending: emptyPending()
  }),

  getters: {
    isLoggedIn: (state) => !!state.userInfo && !!state.accessToken,
    role: (state) => String(state.userInfo?.role || '').toUpperCase(),
    // 菜单红点 = 三个页签待办之和
    pendingTotal: (state) =>
      (state.pending.review || 0) + (state.pending.complete || 0) + (state.pending.transfers || 0),
    isAdmin() {
      return this.role === 'ADMIN'
    },
    isLEADER() {
      return this.role === 'LEADER'
    },
    isDEPARTMENT() {
      return this.role === 'DEPARTMENT'
    }
  },

  actions: {
    setUser(user, token) {
      if (token) {
        sessionStorage.setItem('access_token', token)
        this.accessToken = token
        this.sessionChecked = true
      }
      this.userInfo = user
      sessionStorage.setItem(STORAGE_KEY, JSON.stringify(user))
      // 兼容现有页面读取 user_info 的方式；身份认证以令牌和 /auth/me 为准。
      localStorage.setItem(STORAGE_KEY, JSON.stringify(user))
      // 登录后立刻拉一次待办数量
      this.refreshPendingCount()
    },

    clearUser() {
      this.userInfo = null
      this.accessToken = ''
      this.sessionChecked = false
      sessionStorage.removeItem('access_token')
      sessionStorage.removeItem(STORAGE_KEY)
      this.clearPending()        // 退出清零，避免残留红点
      localStorage.removeItem(STORAGE_KEY)
      localStorage.removeItem('token')
      sessionStorage.removeItem('deadline_notified')
    },

    async restoreSession() {
      // 每次页面重新加载时验证一次令牌；网络错误保留凭证，允许用户稍后重试。
      if (this.sessionChecked || !this.accessToken) return
      const token = this.accessToken
      const { data } = await getCurrentUserApi()
      if (this.accessToken !== token) return
      this.setUser(data.data)
      this.sessionChecked = true
    },

    async logout() {
      // 先撤销服务端会话，再清除本地数据；已过期的令牌按已退出处理。
      if (this.accessToken) {
        try { await logoutApi() }
        catch (error) { if (error.response?.status !== 401) throw error }
      }
      this.clearUser()
    },

    // 待办计数清零（退出登录 / 拉取不到用户时）
    clearPending() {
      this.pending = emptyPending()
    },

    async refreshPendingCount() {
      const uid = this.userInfo?.id
      if (!uid) {
        this.clearPending()
        return
      }
      // 页面隐藏时跳过请求，省一次轮询
      if (typeof document !== 'undefined' && document.visibilityState === 'hidden') {
        return
      }
      try {
        const { data } = await getPendingSummaryApi(uid)
        if (this.userInfo?.id !== uid) return // 退出后不回填旧请求的待办数。
        const d = data?.data || {}
        this.pending = {
          review: d.review ?? 0,
          complete: d.complete ?? 0,
          transfers: d.transfers ?? 0
        }
      } catch (e) {
        // 拉取失败保留上一次的值，避免红点误闪消失
        console.error('拉取待办数量失败', e)
      }
    }
  }
})
