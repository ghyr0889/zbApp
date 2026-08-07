import { defineStore } from 'pinia'

const STORAGE_KEY = 'user_info'

function readStoredUser() {
  const raw = localStorage.getItem(STORAGE_KEY)
  if (!raw) return null

  try {
    return JSON.parse(raw)
  } catch {
    localStorage.removeItem(STORAGE_KEY)
    return null
  }
}

export const useUserStore = defineStore('user', {
  state: () => ({
    userInfo: readStoredUser()
  }),
  getters: {
    isLoggedIn: (state) => !!state.userInfo,
    role: (state) => String(state.userInfo?.role || '').toUpperCase(),
    isAdmin() {
      return this.role === 'ADMIN'
    },
    isOwner() {
      return this.role === 'OWNER' || this.role === 'LEADER'
    }
  },
  actions: {
    setUser(user) {
      this.userInfo = user
      localStorage.setItem(STORAGE_KEY, JSON.stringify(user))
    },
    clearUser() {
      this.userInfo = null
      localStorage.removeItem(STORAGE_KEY)
      localStorage.removeItem('token')
      sessionStorage.removeItem('deadline_notified')
    }
  }
})
