// Event delegation also covers tables mounted later and dialogs teleported to body.
export function installTableContentPreview() {
  const cellSelector = '.el-table td.el-table__cell > .cell'
  const interactiveSelector = 'button, input, textarea, select, [role="button"], .el-table, .el-table__expand-icon, .el-checkbox, .el-radio, .el-select, .el-input, .el-input-number, .el-progress, .el-dropdown, .el-table__column-filter-trigger, .caret-wrapper'
  const pendingCells = new Set()
  let updateFrame = null
  // 用 DOM 检查代替 :has()，兼容不支持该选择器的浏览器。
  function queueCell(cell) {
    if (cell && cell.matches(cellSelector)) pendingCells.add(cell)
  }
  function scheduleCellUpdate() {
    if (updateFrame !== null || !pendingCells.size) return
    updateFrame = requestAnimationFrame(() => {
      updateFrame = null
      pendingCells.forEach(cell => cell.classList.toggle('table-text-cell', !cell.querySelector(interactiveSelector)))
      pendingCells.clear()
    })
  }
  document.querySelectorAll(cellSelector).forEach(queueCell)
  scheduleCellUpdate()
  const observer = new MutationObserver(records => {
    for (const record of records) {
      const target = record.target.nodeType === 1 ? record.target : record.target.parentElement
      if (target && target.closest) queueCell(target.closest(cellSelector))
      record.addedNodes.forEach(node => {
        if (node.nodeType !== 1) return
        queueCell(node)
        node.querySelectorAll(cellSelector).forEach(queueCell)
      })
    }
    scheduleCellUpdate()
  })
  observer.observe(document.body, { childList: true, subtree: true })
  const tooltip = document.createElement('div')
  tooltip.className = 'table-full-content'
  tooltip.id = 'table-full-content-preview'
  tooltip.setAttribute('role', 'tooltip')
  const supportsPopover = typeof tooltip.showPopover === 'function' && typeof tooltip.hidePopover === 'function'
  if (supportsPopover) tooltip.setAttribute('popover', 'manual')
  tooltip.hidden = true
  document.body.appendChild(tooltip)
  let active = null, timer, popoverShown = false
  function hide() {
    clearTimeout(timer)
    if (active?.getAttribute('aria-describedby') === tooltip.id) active.removeAttribute('aria-describedby')
    active = null
    if (supportsPopover && popoverShown) { tooltip.hidePopover(); popoverShown = false }
    tooltip.hidden = true
  }
  function scheduleHide() { clearTimeout(timer); timer = setTimeout(hide, 180) }
  function show(cell) {
    if (active === cell) { clearTimeout(timer); return }
    hide()
    const style = getComputedStyle(cell)
    if (style.webkitLineClamp !== '2' || cell.scrollHeight <= cell.clientHeight + 1) return
    const text = cell.innerText.trim()
    if (!text) return
    active = cell
    tooltip.textContent = text
    tooltip.hidden = false
    if (supportsPopover) { tooltip.showPopover(); popoverShown = true }
    if (!cell.hasAttribute('aria-describedby')) cell.setAttribute('aria-describedby', tooltip.id)
    const rect = cell.getBoundingClientRect()
    const width = tooltip.offsetWidth, height = tooltip.offsetHeight
    tooltip.style.left = `${Math.max(12, Math.min(rect.left, innerWidth - width - 12))}px`
    const below = rect.bottom + 6
    tooltip.style.top = `${Math.max(12, Math.min(below + height <= innerHeight - 12 ? below : rect.top - height - 6, innerHeight - height - 12))}px`
  }
  function over(event) {
    if (tooltip.contains(event.target)) { clearTimeout(timer); return }
    const cell = event.target.closest?.('.el-table .el-table__cell > .cell')
    if (cell) show(cell)
    else scheduleHide()
  }
  function out(event) {
    if (active?.contains(event.relatedTarget) || tooltip.contains(event.relatedTarget)) return
    scheduleHide()
  }
  function key(event) { if (event.key === 'Escape') hide() }
  function scroll(event) { if (!tooltip.contains(event.target)) hide() }
  document.addEventListener('pointerover', over)
  document.addEventListener('pointerout', out)
  document.addEventListener('focusin', over)
  document.addEventListener('keydown', key)
  document.addEventListener('scroll', scroll, true)
  window.addEventListener('resize', hide)
  return () => {
    observer.disconnect()
    if (updateFrame !== null) cancelAnimationFrame(updateFrame)
    pendingCells.clear()
    hide(); tooltip.remove()
    document.removeEventListener('pointerover', over)
    document.removeEventListener('pointerout', out)
    document.removeEventListener('focusin', over)
    document.removeEventListener('keydown', key)
    document.removeEventListener('scroll', scroll, true)
    window.removeEventListener('resize', hide)
  }
}
