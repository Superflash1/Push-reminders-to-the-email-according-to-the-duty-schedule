<template>
  <el-card>
    <template #header>
      <div style="display:flex;justify-content:space-between;align-items:center;">
        <span>提醒规则（支持多个提醒点）</span>
        <el-button type="primary" @click="addRule">+ 新增提醒</el-button>
      </div>
    </template>

    <el-table :data="rows" border>
      <el-table-column label="相对日" width="140">
        <template #default="{ row }">
          <el-select v-model="row.offset_day" style="width:100%" @change="save(row)">
            <el-option :value="-1" label="前一天" />
            <el-option :value="0" label="当天" />
          </el-select>
        </template>
      </el-table-column>

      <el-table-column label="提醒时间" width="180">
        <template #default="{ row }">
          <el-time-select
            v-model="row.trigger_time"
            start="00:00"
            end="23:59"
            step="00:05"
            @change="save(row)"
          />
        </template>
      </el-table-column>

      <el-table-column label="启用" width="100">
        <template #default="{ row }">
          <el-switch v-model="row.enabled" @change="save(row)" />
        </template>
      </el-table-column>

      <el-table-column label="排序" width="120">
        <template #default="{ row }">
          <el-input-number v-model="row.sort_order" :min="0" @change="save(row)" />
        </template>
      </el-table-column>

      <el-table-column label="操作" width="100">
        <template #default="{ row }">
          <el-button type="danger" size="small" @click="remove(row.id)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
  </el-card>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import http from '../api/http'

const rows = ref([])

const load = async () => {
  const { data } = await http.get('/reminder-rules')
  rows.value = data
}

const addRule = async () => {
  await http.post('/reminder-rules', {
    offset_day: 0,
    trigger_time: '09:00',
    enabled: true,
    sort_order: rows.value.length + 1,
  })
  ElMessage.success('已新增提醒规则')
  load()
}

const timeRegex = /^([01]\d|2[0-3]):[0-5]\d$/

const save = async (row) => {
  if (!timeRegex.test(row.trigger_time)) {
    ElMessage.warning('提醒时间格式必须是 HH:mm')
    return
  }

  await http.put(`/reminder-rules/${row.id}`, {
    offset_day: row.offset_day,
    trigger_time: row.trigger_time,
    enabled: row.enabled,
    sort_order: row.sort_order,
  })
}

const remove = async (id) => {
  await http.delete(`/reminder-rules/${id}`)
  ElMessage.success('删除成功')
  load()
}

onMounted(load)
</script>