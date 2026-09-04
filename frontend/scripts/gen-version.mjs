// 构建后生成 dist/version.json，供前端「自动更新」轮询比对版本
// 用法：vite build && node scripts/gen-version.mjs
import { writeFileSync } from 'node:fs'
import { resolve } from 'node:path'

const out = resolve('dist/version.json')
const buildId = String(Date.now()) // 每次构建唯一；部署后发生变化即触发前端自动刷新
const payload = {
  buildId,
  buildTime: new Date().toISOString()
}
writeFileSync(out, JSON.stringify(payload), 'utf8')
console.log('[gen-version] generated', out, payload)
