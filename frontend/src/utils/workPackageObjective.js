import { ElMessage } from 'element-plus'

// 与工作包目标的数据库兼容上限及后端校验保持一致，按 Unicode 字符计数。
export const WORK_PACKAGE_OBJECTIVE_MAX_LENGTH = 100
export const objectiveLength = value => Array.from(value || '').length

export function warnObjectiveLength(value) {
  if (objectiveLength(value) > WORK_PACKAGE_OBJECTIVE_MAX_LENGTH) {
    ElMessage.warning({ message: `工作目标不能超过 ${WORK_PACKAGE_OBJECTIVE_MAX_LENGTH} 字，请删减后提交`, grouping: true })
  }
}
