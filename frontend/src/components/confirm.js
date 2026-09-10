import { ElMessageBox } from 'element-plus'

/**
 * 通用关闭确认弹窗
 * @param {string} targetType - 对象类型：'工作项' | '工作包' | '项目'
 * @param {Function} onConfirm - 确认后执行的回调
 */
export const confirmClose = (targetType, onConfirm) => {
  ElMessageBox.confirm(
    `关闭后该${targetType}将不可再编辑/填分，且只有管理员可以取消关闭状态。\n确定要关闭吗？`,
    '确认关闭',
    {
      confirmButtonText: '确认关闭',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(() => {
    onConfirm()
  }).catch(() => {})
}

/**
 * 通用取消关闭确认弹窗
 */
export const confirmCancelClose = (targetType, onConfirm) => {
  ElMessageBox.confirm(
    `确定取消关闭？取消后该${targetType}恢复为可编辑状态。`,
    '取消关闭',
    {
      confirmButtonText: '确定取消',
      cancelButtonText: '取消',
      type: 'info'
    }
  ).then(() => {
    onConfirm()
  }).catch(() => {})
}