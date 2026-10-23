// Event delegation also covers tables mounted later and dialogs teleported to body.
export function installTableContentPreview() {
  const tooltip = document.createElement('div')
  tooltip.className = 'table-full-content'
  tooltip.id = 'table-full-content-preview'
  tooltip.setAttribute('role', 'tooltip')
  tooltip.setAttribute('popover', 'manual')
  tooltip.hidden = true
  document.body.appendChild(tooltip)
  let active = null, timer
  function hide() {
    clearTimeout(timer)
    if (active?.getAttribute('aria-describedby') === tooltip.id) active.removeAttribute('aria-describedby')
    active = null
    if (tooltip.matches(':popover-open')) tooltip.hidePopover()
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
    if (tooltip.showPopover) tooltip.showPopover()
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
    hide(); tooltip.remove()
    document.removeEventListener('pointerover', over)
    document.removeEventListener('pointerout', out)
    document.removeEventListener('focusin', over)
    document.removeEventListener('keydown', key)
    document.removeEventListener('scroll', scroll, true)
    window.removeEventListener('resize', hide)
  }
}
