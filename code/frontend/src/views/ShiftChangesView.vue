<template>
  <el-card>
    <template #header>
      <div style="display:flex;justify-content:space-between;align-items:center;">
        <span>换班记录</span>
        <el-button type="primary" @click="openCreate">手工换班</el-button>
      </div>
    </template>

    <el-table :data="rows" border>
      <el-table-column prop="duty_date" label="日期" width="130" />
      <el-table-column prop="old_person_name" label="原值班人" width="140" />
      <el-table-column prop="new_person_name" label="新值班人" width="140" />
      <el-table-column prop="reason" label="原因" />
      <el-table-column prop="requested_by" label="操作人" width="120" />
      <el-table-column prop="source" label="来源" width="120" />
      <el-table-column prop="created_at" label="时间" width="180" />
    </el-table>

    <el-dialog v-model="visible" title="手工换班" width="520px">
      <el-form label-width="100px">
        <el-form-item label="日期">
          <el-date-picker v-model="form.duty_date" type="date" value-format="YYYY-MM-DD" style="width:100%" />
        </el-form-item>
        <el-form-item label="新值班人">
          <el-input v-model="form.new_person_name" />
        </el-form-item>
        <el-form-item label="原因">
          <el-input v-model="form.reason" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="visible = false">取消</el-button>
        <el-button type="primary" @click="submit">确认换班</el-button>
      </template>
    </el-dialog>
  </el-card>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import http from '../api/http'

const rows = ref([])
const visible = ref(false)
const form = reactive({
  duty_date: '',
  new_person_name: '',
  reason: '',
})

const load = async () => {
  const { data } = await http.get('/shift-changes')
  rows.value = data
}

const openCreate = () => {
  form.duty_date = ''
  form.new_person_name = ''
  form.reason = ''
  visible.value = true
}

const submit = async () => {
  if (!form.duty_date || !form.new_person_name) {
    ElMessage.warning('日期和新值班人必填')
    return
  }

  await http.post('/shift-changes', {
    duty_date: form.duty_date,
    new_person_name: form.new_person_name,
    reason: form.reason,
    requested_by: 'manual',
    source: 'manual',
  })
  ElMessage.success('换班成功并已记录')
  visible.value = false
  load()
}

onMounted(load)
</script>
