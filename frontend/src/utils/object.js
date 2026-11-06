// 使用广泛兼容的写法判断自有字段，避免旧浏览器缺少 Object.hasOwn。
export function hasOwn(object, key) {
  return Object.prototype.hasOwnProperty.call(object, key)
}
