// 自动更新：轮询服务器上的 /version.json，发现新版本后自动刷新页面，
// 让「已打开、没有手动刷新」的用户也能无感切到最新前端。
// 依赖：nginx 对 /version.json 与 /index.html 均返回 no-cache（见 deploy/nginx.conf.example）。

const VERSION_URL = '/version.json'
const CHECK_INTERVAL = 60 * 1000 // 每 60 秒检查一次

let currentBuildId = null

async function fetchBuildId() {
  const res = await fetch(`${VERSION_URL}?t=${Date.now()}`, {
    cache: 'no-store',
    headers: { 'Cache-Control': 'no-cache' }
  })
  if (!res.ok) return null
  const data = await res.json()
  return data && data.buildId ? String(data.buildId) : null
}

async function check() {
  try {
    const id = await fetchBuildId()
    if (!id) return
    if (currentBuildId === null) {
      // 首次：记录当前版本
      currentBuildId = id
      return
    }
    if (id !== currentBuildId) {
      // 检测到新版本 → 刷新页面（刷新后 index.html 会 revalidate 拿到新资源）
      window.location.reload()
    }
  } catch {
    /* 网络/接口异常时静默，下次再试 */
  }
}

export function startAutoUpdate(intervalMs = CHECK_INTERVAL) {
  // 首次检查
  check()
  // 定时检查
  const timer = setInterval(check, intervalMs)
  // 页面从后台切回前台时立即检查，避免等待一个轮询周期
  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible') check()
  })
  // 组件/应用卸载时清理（SPA 中 main.js 引入，基本不会触发，但保留以保规范）
  if (typeof window !== 'undefined') {
    window.addEventListener('beforeunload', () => clearInterval(timer))
  }
}
