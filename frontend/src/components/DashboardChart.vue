<!--- 数据看板图表组件 --->
<template>
  <div ref="host" class="dashboard-chart" role="img" :aria-label="label"></div>
</template>
<script setup>
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import * as echarts from 'echarts'
const props = defineProps({ option: Object, label: String })
const host = ref(null)
let chart, observer
// 图表随卡片、侧栏和放大窗口尺寸变化；离开页面及时释放实例。
onMounted(() => {
  chart = echarts.init(host.value)
  chart.setOption(props.option, true)
  // 仅横坐标标签显示全文，数值仍由看板的“显示详细数据”按钮控制。
  chart.on('mouseover', params => {
    if (host.value) host.value.title = params.componentType === 'xAxis' ? String(params.value ?? '') : ''
  })
  chart.on('mouseout', () => { if (host.value) host.value.removeAttribute('title') })
  chart.getZr().on('globalout', () => { if (host.value) host.value.removeAttribute('title') })
  observer = new ResizeObserver(() => chart?.resize())
  observer.observe(host.value)
})
watch(() => props.option, option => chart?.setOption(option, true), { deep: true })
// 导出当前图表（包含当前缩放范围和图例选择），不重新请求统计数据。
function exportImage(filename = '统计图') {
  if (!chart || chart.isDisposed() || !host.value?.clientWidth || !host.value?.clientHeight) return false
  const imageUrl = chart.getDataURL({
    type: 'png',
    pixelRatio: 2, // 两倍像素，方便保存和插入报告。
    backgroundColor: '#fff',
    excludeComponents: ['toolbox']
  })
  // 创建临时链接
  const link = document.createElement('a')
  link.href = imageUrl
  // 文件名替换系统不允许的字符；链接用完立即移除。
  link.download = `${filename.replace(/[\\/:*?"<>|\x00-\x1f]/g, '_')}.png`

  document.body.appendChild(link)

  try { link.click() } finally { link.remove() }
  return true
}
// 父页面通过组件 ref 调用，ECharts 实例仍封装在本组件内。
defineExpose({ exportImage })
onBeforeUnmount(() => { observer?.disconnect(); chart?.dispose(); chart = null })
</script>
<style scoped>.dashboard-chart { width: 100%; height: 360px; min-width: 0; }</style>
