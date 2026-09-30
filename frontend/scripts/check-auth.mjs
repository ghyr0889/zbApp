// 检查登录相关 Vue 文件语法，以及 Axios 是否正确携带和处理凭证。
// 使用内存存储和模拟响应，不发送网络请求。
import fs from 'node:fs'
import assert from 'node:assert/strict'
import { parse, compileScript, compileTemplate } from '@vue/compiler-sfc'

for (const filename of ['src/views/Login.vue', 'src/views/PersonalInfo.vue', 'src/App.vue']) {
  const { descriptor, errors } = parse(fs.readFileSync(filename, 'utf8'))
  assert.equal(errors.length, 0)
  const script = compileScript(descriptor, { id: filename })
  const template = compileTemplate({ source: descriptor.template.content, filename, id: filename,
    compilerOptions: { bindingMetadata: script.bindings } })
  assert.equal(template.errors.length, 0, String(template.errors))
  console.log(`${filename}：脚本、模板语法检查通过`)
}

const storage = new Map()
globalThis.sessionStorage = {
  getItem: key => storage.get(key) ?? null,
  setItem: (key, value) => storage.set(key, String(value)),
  removeItem: key => storage.delete(key),
}
const { default: api, setUnauthorizedHandler } = await import('../src/api/index.js')
let unauthorizedCount = 0
setUnauthorizedHandler(() => { unauthorizedCount++ })

sessionStorage.setItem('access_token', 'real-session-token')
api.defaults.adapter = async config => {
  assert.equal(config.headers.Authorization, 'Bearer real-session-token')
  return { data: {}, status: 200, headers: {}, config }
}
await api.get('/auth/me')

for (const status of [403, 401]) {
  api.defaults.adapter = async config => { throw { response: { status }, config } }
  await api.get('/auth/me').catch(() => {})
  assert.equal(unauthorizedCount, status === 403 ? 0 : 1)
}
// 旧请求到达前已重新登录时，不能将新令牌对应的用户清除。
api.defaults.adapter = async config => {
  sessionStorage.setItem('access_token', 'new-session-token')
  throw { response: { status: 401 }, config }
}
await api.get('/auth/me').catch(() => {})
assert.equal(unauthorizedCount, 1)
sessionStorage.removeItem('access_token')
api.defaults.adapter = async config => {
  assert.equal(config.headers.Authorization, undefined)
  return { data: {}, status: 200, headers: {}, config }
}
await api.post('/auth/user-login', {})
console.log('凭证携带、401/403 区分、旧请求隔离及无凭证请求检查通过')
