<template>
  <el-card>
    <template #header>
      <div style="display:flex;justify-content:space-between;align-items:center;">
        <span>发送日志</span>
        <el-space>
          <el-button @click="exportCsv">导出CSV</el-button>
          <el-button @click="load">刷新</el-button>
        </el-space>
      </div>
    </template>

    <el-form inline style="margin-bottom: 12px">
      <el-form-item label="状态">
        <el-select v-model="filters.status" clearable style="width:120px">
          <el-option label="SUCCESS" value="SUCCESS" />
          <el-option label="FAILED" value="FAILED" />
          <el-option label="SKIPPED" value="SKIPPED" />
        </el-select>
      </el-form-item>
      <el-form-item label="目标">
        <el-select v-model="filters.target_type" clearable style="width:120px">
          <el-option label="DUTY" value="DUTY" />
          <el-option label="ADMIN" value="ADMIN" />
        </el-select>
      </el-form-item>
      <el-form-item label="业务日期">
        <el-date-picker v-model="filters.biz_date" type="date" value-format="YYYY-MM-DD" clearable />
      </el-form-item>
      <el-form-item>
        <el-button @click="reset">重置</el-button>
      </el-form-item>
    </el-form>

    <el-table :data="filteredRows" border>
      <el-table-column prop="created_at" label="时间" width="180" />
      <el-table-column prop="biz_date" label="业务日期" width="120" />
      <el-table-column prop="target_type" label="目标" width="100" />
      <el-table-column prop="to_email" label="收件人" width="220" />
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="row.status === 'SUCCESS' ? 'success' : 'danger'">{{ row.status }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="subject" label="标题" />
      <el-table-column prop="error_message" label="错误信息" />
    </el-table>
  </el-card>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import http from '../api/http'

const rows = ref([])
const filters = reactive({
  status: '',
  target_type: '',
  biz_date: '',
})

const filteredRows = computed(() => {
  return rows.value.filter((r) => {
    if (filters.status && r.status !== filters.status) return false
    if (filters.target_type && r.target_type !== filters.target_type) return false
    if (filters.biz_date && r.biz_date !== filters.biz_date) return false
    return true
  })
})

const load = async () => {
  const { data } = await http.get('/send-logs')
  rows.value = data
}

const reset = () => {
  filters.status = ''
  filters.target_type = ''
  filters.biz_date = ''
}

const exportCsv = () => {
  const headers = ['created_at', 'biz_date', 'target_type', 'to_email', 'status', 'subject', 'error_message']
  const rowsText = filteredRows.value.map((r) => {
    const vals = headers.map((h) => {
      const text = (r[h] ?? '').toString().replaceAll('"', '""')
      return `"${text}"`
    })
    return vals.join(',')
  })

  const csv = [headers.join(','), ...rowsText].join('\n')
  const blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `send_logs_${new Date().toISOString().slice(0, 10)}.csv`
  a.click()
  URL.revokeObjectURL(url)
}

onMounted(load)
</script>