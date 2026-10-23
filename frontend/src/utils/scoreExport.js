// 所有人员积分数据导出excel工具文件，导出字段与积分页面保持一致；只读取接口结果，不在导出时重新计算积分。
export function createScoreSnapshot(people, mode, period, quarter = 1) {
  // 整理导出列和数据，保存本次导出的快照
  const columns = [['user_id', '工号', 'text'], ['username', '名字', 'text']]
  if (mode === 'month') {
    columns.push(
      ['month_score', '工作项-基础得分'], ['calculate_score', '工作项-计算得分'],
      ['deducted_score', '工作项-进度扣分'], ['tech_improve', '技术提升合计'], ['patent_score', '技术提升-专利'],
      ['knowledge_score', '技术提升-知识库'], ['train_score', '技术提升-培训'],
      ['daily_manage', '日常管理合计'], ['deduct_score', '日常管理-扣分'], ['quality_event_score', '日常管理-质量事件'],
      ['carrier_inspection_score', '日常管理-载体检查'], ['tech_growth_score', '技术成长分'],
      ['total_calculated', '计算总分'], ['converted_score', '折算总分'],
    )
  } else {
    for (let i = 1; i <= (mode === 'year' ? 4 : 3); i++) {
      columns.push([`period_${i}`, mode === 'year' ? `第${i}季度` : `${(quarter - 1) * 3 + i}月`])
    }
    columns.push(['total_score', '得分'], ['final_calculated', '计算得分'])
  }
  columns.push(['grade', '等级', 'text'], ['settlement_label', '入账状态', 'text'])
  // 立即复制单元格值，避免等待加载导出库时切换周期或编辑影响本次文件。
  const rows = people.map(person => columns.map(([key, label, type]) => {
    const value = key === 'settlement_label'
      ? (person.is_provisional ? '实时预览（未入账）' : ({IMPORTED:'历史补录已入账',CONFIRMED:'本人已确认',AUTO:'自动入账',PARTIAL:'部分月份未入账',HISTORY:'历史积分'}[person.confirmation_status] || '统计结果'))
      : person[key]
    if (value === null || value === undefined || value === '') return null
    if (type === 'text') return String(value) // 工号保留 0004 等前导零，文本不会作为公式执行。
    const number = Number(value)
    if (!Number.isFinite(number)) throw new Error(`${person.username || ''}的“${label}”不是有效数字`)
    return number
  }))
  return { columns, rows, period, exportedAt: new Date() }
}

export async function createScoreWorkbook(snapshot) {
  // 创建 Excel 工作簿，填写内容和设置格式
  // 仅点击导出时加载 ExcelJS，减少积分页面首次加载的开销。
  const { default: ExcelJS } = await import('exceljs')
  const workbook = new ExcelJS.Workbook() //工作薄
  const sheet = workbook.addWorksheet('所有人员积分') // 工作表

  // 按字段名设置列宽。
  // 数值越大，列越宽；这里使用 Excel 列宽单位，不是像素。
  const columnWidths = {
    user_id: 10, username: 14,                 // 工号、名字
    // 工作项
    month_score: 12,  calculate_score: 12, deducted_score: 12,
    // 技术提升
    patent_score: 10,  knowledge_score: 12, train_score: 10, 
    // 日常管理
    deduct_score: 10, quality_event_score: 12, carrier_inspection_score: 12,
    // 月度汇总
    tech_growth_score: 14, total_calculated: 14, converted_score: 14, grade: 10,
    // 季度、年度
    period_1: 14, period_2: 14, period_3: 14, period_4: 14,  total_score: 14, final_calculated: 14,
  }

  // 根据当前导出列的字段名，找到对应宽度。
  // 未配置的字段默认使用 14，避免新增列时没有宽度设置。
  sheet.columns = snapshot.columns.map(([key]) => ({
    width: columnWidths[key] ?? 14,
  }))
  sheet.mergeCells(1, 1, 1, snapshot.columns.length)
  sheet.getCell('A1').value = '所有人员积分'
  sheet.getCell('A1').font = { bold: true, size: 18 }
  sheet.getCell('A1').alignment = { horizontal: 'center' }
  sheet.getRow(1).height = 32

  sheet.mergeCells(2, 1, 2, snapshot.columns.length)
  sheet.getCell('A2').value = `统计周期：${snapshot.period}　单位：分　导出时间：${snapshot.exportedAt.toLocaleString('zh-CN')}`

  const isMonthly = snapshot.columns.some(([key]) => key === 'month_score')
  const headerStartRow = 4
  const headerEndRow = isMonthly ? 5 : 4
  const columnCount = snapshot.columns.length

  if (isMonthly) {
    // 分组名称、组内字段及其显示名称。
    // 字段顺序需要与 createScoreSnapshot() 中的列顺序保持一致。
    const groups = [
      {
        title: '工作项',
        fields: ['month_score', 'calculate_score', 'deducted_score'],
        labels: ['基础得分', '计算得分', '进度扣分'],
      },
      {
        title: '技术提升',
        fields: ['patent_score', 'knowledge_score', 'train_score'],
        labels: ['专利', '知识库', '培训'],
      },
      {
        title: '日常管理',
        fields: [
          'deduct_score',
          'quality_event_score',
          'carrier_inspection_score',
        ],
        labels: ['扣分', '质量事件', '载体检查'],
      },
    ]

    // 收集所有分组字段，用于识别不需要分组的列。
    const groupedFields = new Set(
      groups.flatMap(group => group.fields)
    )

    // 工号、人员、技术成长分、计算总分、折算总分、等级：
    snapshot.columns.forEach(([key, label], index) => {
      if (groupedFields.has(key)) return

      const column = index + 1

      sheet.mergeCells(
        headerStartRow,
        column,
        headerEndRow,
        column
      )

      sheet.getCell(headerStartRow, column).value = label
    })

    // 工作项、技术提升、日常管理：
    // 第4行横向合并为分组标题，第5行填写具体列名。
    groups.forEach(group => {
      const firstIndex = snapshot.columns.findIndex(
        ([key]) => key === group.fields[0]
      )

      // 检查分组字段是否齐全且连续，防止后续调整列时合并错位。
      const valid = firstIndex >= 0 && group.fields.every(
        (key, offset) => snapshot.columns[firstIndex + offset]?.[0] === key
      )

      if (!valid) {
        throw new Error(`“${group.title}”导出字段缺失或顺序不正确`)
      }

      const startColumn = firstIndex + 1
      const endColumn = startColumn + group.fields.length - 1

      sheet.mergeCells(
        headerStartRow,
        startColumn,
        headerStartRow,
        endColumn
      )

      sheet.getCell(headerStartRow, startColumn).value = group.title

      group.labels.forEach((label, index) => {
        sheet.getCell(
          headerEndRow,
          startColumn + index
        ).value = label
      })
    })
  } else {
    // 季度、年度仍然使用单行表头。
    sheet.getRow(headerStartRow).values =
      snapshot.columns.map(([, label]) => label)
  }

  // 统一设置表头样式：浅灰背景、深色加粗字体、居中和细边框。
  // 显式遍历所有表头位置，包括被合并覆盖的单元格。
  for (let rowNumber = headerStartRow; rowNumber <= headerEndRow; rowNumber++) {
    const row = sheet.getRow(rowNumber)
    row.height = 30

    for (let column = 1; column <= columnCount; column++) {
      const cell = row.getCell(column)

      cell.font = {
        name: '微软雅黑',
        size: 11,
        bold: true,
        color: { argb: 'FF334155' },
      }

      cell.fill = {
        type: 'pattern',
        pattern: 'solid',
        fgColor: { argb: 'FFF8FAFC' },
      }

      cell.alignment = {
        horizontal: 'center',
        vertical: 'middle',
        wrapText: true,
      }

      cell.border = {
        top: { style: 'thin', color: { argb: 'FFE2E8F0' } },
        bottom: { style: 'thin', color: { argb: 'FFE2E8F0' } },
        left: { style: 'thin', color: { argb: 'FFE2E8F0' } },
        right: { style: 'thin', color: { argb: 'FFE2E8F0' } },
      }
    }
  }
  snapshot.rows.forEach(values => {
    const row = sheet.addRow(values)
    row.height = 23
    snapshot.columns.forEach(([, , type], index) => {
      const cell = row.getCell(index + 1)
      cell.numFmt = type === 'text' ? '@' : '#,##0.00;[Red]-#,##0.00'
      cell.alignment = { horizontal: type === 'text' ? 'left' : 'right', vertical: 'middle' }
    })
  })

  sheet.views = [{ state: 'frozen', xSplit: 2, ySplit: headerEndRow }]
  // 月度使用合并分组表头，不添加筛选下拉按钮。
  // 季度和年度仍然使用普通单行表头，可以继续筛选。
  if (!isMonthly) {
    sheet.autoFilter = {
      from: {row: headerStartRow, column: 1},
      to: {row: headerEndRow + snapshot.rows.length, column: columnCount},
    }
  }
  return workbook
}

export async function downloadScoreExcel(snapshot) {
  // 生成 .xlsx 文件，触发浏览器下载
  const workbook = await createScoreWorkbook(snapshot)
  const buffer = await workbook.xlsx.writeBuffer()
  const url = URL.createObjectURL(new Blob([buffer], {
    type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  }))
  const link = document.createElement('a')
  try {
    link.href = url
    link.download = `所有人员积分_${snapshot.period.replace(/[\\/:*?"<>|]/g, '-')}.xlsx`
    document.body.appendChild(link)
    link.click()
  } finally {
    link.remove()
    // 稍后释放地址，留出浏览器接收下载的时间。
    setTimeout(() => URL.revokeObjectURL(url), 30000)
  }
}
