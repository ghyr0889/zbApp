<!-- 历史积分补录组件 -->
<template>
  <el-button type="primary" plain @click="open">补录历史积分</el-button>
  <el-dialog v-model="visible" title="历史月度积分补录" width="min(1000px, 94vw)" draggable append-to-body :close-on-click-modal="false" :show-close="!busy">
    <el-alert :closable="false" type="info" :title="`仅可补录 ${startMonth || '启用月份'} 之前的月份。先保存草稿，再核对入账；入账后不可修改，不触发自评。`" />
    <el-form label-position="top" :disabled="busy || locked" style="margin-top: 20px">
      <div class="history-fields">
        <el-form-item label="人员（必填）"><el-select v-model="form.user_id" filterable><el-option v-for="p in people" :key="p.user_id" :value="p.user_id" :label="`${p.username}（${p.user_id}）`" /></el-select></el-form-item>
        <el-form-item label="月份（必填）"><el-date-picker v-model="form.month" type="month" value-format="YYYY-MM" /></el-form-item>
        <el-form-item v-for="[key, label] in fields" :key="key" :label="label + '（必填）'"><el-input-number v-model="form[key]" :precision="2" :controls="false" /></el-form-item>
        <el-form-item label="历史等级（必填）"><el-select v-model="form.grade"><el-option v-for="g in ['S','A','B','C','D']" :key="g" :value="g" :label="g" /></el-select></el-form-item>
      </div>
      <el-form-item label="补录说明／数据来源（必填）"><el-input v-model="form.reason" type="textarea" :rows="3" maxlength="2000" show-word-limit /></el-form-item>
    </el-form>
    <el-alert v-if="formulaWarning" :title="formulaWarning" type="warning" :closable="false" />
    <p>历史分数按原台账保存，不用当前公式覆盖；仅有汇总数据，不生成工作项明细。</p>
    <el-button :disabled="busy" @click="reset">新建／清空表单</el-button>
    <el-button v-if="!locked" type="primary" :loading="busy" @click="save">保存草稿</el-button>
    <h3>已保存记录（点击核对后才能入账）</h3>
    <el-table :data="drafts" border max-height="300">
      <el-table-column prop="month" label="月份" width="110" />
      <el-table-column prop="snapshot.username" label="人员" />
      <el-table-column prop="snapshot.total_calculated" label="计算总分" />
      <el-table-column prop="snapshot.converted_score" label="折算总分" />
      <el-table-column prop="snapshot.grade" label="等级" width="70" />
      <el-table-column label="状态"><template #default="{row}">{{ row.status === 'DRAFT' ? '草稿' : '已入账锁定' }}</template></el-table-column>
      <el-table-column label="操作" width="180">
        <template #default="{row}">
          <el-button link type="primary" :disabled="busy" @click="inspect(row)">查看／核对</el-button>
          <el-button v-if="row.status === 'DRAFT'" link type="primary" :disabled="busy" @click="publish(row)">正式入账</el-button>
        </template>
      </el-table-column>
    </el-table>
    <template #footer><el-button :disabled="busy" @click="visible = false">关闭</el-button></template>
  </el-dialog>
</template>
<script setup>
import {computed, ref} from 'vue'
import {ElMessage, ElMessageBox} from 'element-plus'
import {getHistoricalScoreDraftsApi, saveHistoricalScoreDraftApi, publishHistoricalScoreDraftApi} from '../api'
const visible=ref(false), busy=ref(false), locked=ref(false), startMonth=ref(''), people=ref([]), drafts=ref([]), form=ref({}), inspected=ref(null)
const fields=[['month_score','工作项基础得分'],['calculate_score','工作项计算得分'],['deducted_score','进度扣分'],['tech_improve','技术提升合计'],['daily_manage','日常管理合计'],['tech_growth_score','技术成长分'],['total_calculated','计算总分'],['converted_score','折算总分']]
function reset(){form.value={user_id:'',month:'',grade:'',reason:'',...Object.fromEntries(fields.map(([k])=>[k,undefined]))};locked.value=false;inspected.value=null}
const formulaWarning=computed(()=>{
 const f=form.value
 if(fields.some(([k])=>!Number.isFinite(f[k])))return ''
 return Math.abs(f.total_calculated-(f.calculate_score+f.tech_improve+f.daily_manage-f.deducted_score))>0.011 || Math.abs(f.tech_growth_score-(f.calculate_score-f.month_score+f.tech_improve))>0.011 ? '历史汇总与当前公式不一致，请核实并在补录说明中说明原因。仍按输入值保存。' : ''
})
async function load(){const {data}=await getHistoricalScoreDraftsApi();startMonth.value=data.data.start_month;people.value=data.data.people;drafts.value=data.data.drafts}
async function open(){visible.value=true;reset();busy.value=true;try{await load()}catch(e){ElMessage.error(e.response?.data?.detail||'加载失败')}finally{busy.value=false}}
function inspect(row){form.value={...row.snapshot,user_id:row.user_id,month:row.month,reason:row.reason};locked.value=row.status!=='DRAFT';inspected.value=row.id}
async function save(){
 const f=form.value
 if(!f.user_id||!f.month||!f.grade||!f.reason.trim()||fields.some(([k])=>!Number.isFinite(f[k])))return ElMessage.warning('请填写所有必填项')
 if(!startMonth.value||f.month>=startMonth.value)return ElMessage.warning('只能补录启用月份之前的月份')
 busy.value=true
 try{await saveHistoricalScoreDraftApi(Object.fromEntries(['user_id','month','grade','reason',...fields.map(([k])=>k)].map(k=>[k,f[k]])));await load();inspected.value=null;ElMessage.success('草稿已保存，请核对后入账')}catch(e){ElMessage.error(e.response?.data?.detail||'保存失败')}finally{busy.value=false}
}
async function publish(row){
 inspect(row)
 try{await ElMessageBox.confirm(`${row.month} · ${row.snapshot.username}：计算总分 ${row.snapshot.total_calculated}，折算总分 ${row.snapshot.converted_score}，等级 ${row.snapshot.grade}。请先核对表单全部字段。入账将采用已保存草稿，且不可修改。`, '核对历史积分并正式入账', {confirmButtonText:'确认入账',cancelButtonText:'返回核对',draggable:true})}catch{return}
 busy.value=true
 try{await publishHistoricalScoreDraftApi(row.id,row.fingerprint);await load();locked.value=true;ElMessage.success('已入账并锁定');window.dispatchEvent(new Event('monthly-score-confirmed'))}catch(e){ElMessage.error(e.response?.data?.detail||'入账失败')}finally{busy.value=false}
}
</script>
<style scoped>
.history-fields{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:0 20px}
.history-fields :deep(.el-input-number),.history-fields :deep(.el-select),.history-fields :deep(.el-date-editor){width:100%}
@media(max-width:700px){.history-fields{grid-template-columns:1fr}}
</style>
