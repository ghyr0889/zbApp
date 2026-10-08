import { defineStore } from 'pinia'
import { useUserStore } from './user'
import { getCurrentWorkTimeApi, startWorkTimeApi, finishWorkTimeApi } from '../api'

export const formatDuration = seconds => {
  const value = Math.max(0, Math.floor(seconds || 0))
  return `${String(Math.floor(value / 3600)).padStart(2, '0')}:${String(Math.floor(value / 60) % 60).padStart(2, '0')}:${String(value % 60).padStart(2, '0')}`
}

export const useWorkTimeStore = defineStore('workTime', {
  state: () => ({ current: null, busy: false, ready: false, syncError: '', revision: 0,
    receivedAt: 0, tick: 0, requestSequence: 0 }),
  getters: {
    elapsedSeconds: state => state.current ? state.current.elapsed_seconds + (
      state.current.status === 'RUNNING' ? Math.max(0, state.tick - state.receivedAt) / 1000 : 0
    ) : 0,
  },
  actions: {
    apply(row) {
      this.current = row?.status === 'FINISHED' ? null : row
      this.receivedAt = performance.now()
      this.tick = this.receivedAt
      this.ready = true
      this.syncError = ''
      this.revision++
    },
    reset() {
      this.requestSequence++
      this.current = null
      this.ready = false
      this.busy = false
      this.syncError = ''
      this.revision++
    },
    async refresh() {
      const user = useUserStore(), token = user.accessToken
      if (!token) return
      const sequence = ++this.requestSequence
      try {
        const { data } = await getCurrentWorkTimeApi()
        if (token === user.accessToken && sequence === this.requestSequence) this.apply(data.data)
      } catch (error) {
        if (token === user.accessToken && sequence === this.requestSequence) this.syncError = '计时状态同步失败，请检查网络后重试'
        throw error
      }
    },
    async start(itemId) {
      if (this.busy) return
      const user = useUserStore(), token = user.accessToken
      const keyName = `work-time-start:${user.userInfo.id}:${itemId}`
      // 网络超时后保留请求号，再次点击或刷新后重试不会重复创建记录。
      let requestKey = sessionStorage.getItem(keyName)
      if (!requestKey) {
        requestKey = Array.from(crypto.getRandomValues(new Uint8Array(16)), n => n.toString(16).padStart(2, '0')).join('')
        sessionStorage.setItem(keyName, requestKey)
      }
      this.busy = true
      this.requestSequence++
      try {
        const { data } = await startWorkTimeApi({ work_item_id: itemId, request_key: requestKey })
        sessionStorage.removeItem(keyName)
        if (user.accessToken === token) this.apply(data.data)
      } catch (error) {
        if (error.response && error.response.status < 500) sessionStorage.removeItem(keyName)
        if (user.accessToken === token) await this.refresh().catch(() => {})
        throw error
      } finally { if (user.accessToken === token) this.busy = false }
    },
    async finish() {
      if (this.busy || !this.current) return
      const user = useUserStore(), token = user.accessToken
      const { id, version } = this.current
      this.busy = true
      this.requestSequence++
      try {
        const { data } = await finishWorkTimeApi(id, version)
        if (user.accessToken === token) this.apply(data.data)
      } catch (error) {
        // 超时不代表后端失败，主动重查真实状态，禁止在本地擅自增加或删除工时。
        if (user.accessToken === token) await this.refresh().catch(() => {})
        throw error
      } finally { if (user.accessToken === token) this.busy = false }
    },
  },
})
