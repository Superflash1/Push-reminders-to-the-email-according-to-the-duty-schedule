<template>
  <el-card>
    <template #header>
      <div style="display:flex;flex-direction:column;gap:12px;">
        <div style="display:flex;justify-content:space-between;align-items:center;">
          <span>值班表管理</span>
          <div style="display:flex;gap:8px;">
            <el-button
              type="danger"
              plain
              :disabled="!hasActiveFilter || filteredRows.length === 0"
              @click="removeFiltered"
            >
              删除当前筛选（{{ filteredRows.length }}）
            </el-button>
            <el-button type="danger" plain :disabled="selectedRows.length === 0" @click="removeSelected">
              删除已选（{{ selectedRows.length }}）
            </el-button>
            <el-button type="primary" @click="openCreate">手工新增</el-button>
            <el-upload :auto-upload="false" :show-file-list="false" :on-change="onFileChange">
              <el-button type="primary" plain>导入Excel</el-button>
            </el-upload>
          </div>
        </div>

        <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap;">
          <el-input
            v-model="filters.keyword"
            clearable
            placeholder="按值班人/星期/来源筛选"
            style="width:260px"
          />
          <el-date-picker
            v-model="filters.dateRange"
            type="daterange"
            value-format="YYYY-MM-DD"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            range-separator="至"
            style="width:320px"
          />
          <el-button link @click="resetFilters" :disabled="!hasActiveFilter">清空筛选</el-button>
        </div>
      </div>
    </template>

    <el-table :data="filteredRows" border @selection-change="onSelectionChange">
      <el-table-column type="selection" width="55" />
      <el-table-column prop="duty_date" label="日期" width="140" />
      <el-table-column prop="weekday_text" label="星期" width="100" />
      <el-table-column prop="duty_person_name" label="值班人" />
      <el-table-column prop="source_sheet" label="来源Sheet" />
      <el-table-column label="操作" width="180">
        <template #default="{ row }">
          <el-button size="small" @click="openEdit(row)">编辑</el-button>
          <el-button size="small" type="danger" @click="remove(row.id)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="visible" title="编辑值班记录" width="520px">
      <el-form label-width="90px">
        <el-form-item label="日期">
          <el-date-picker v-model="form.duty_date" type="date" value-format="YYYY-MM-DD" style="width:100%" />
        </el-form-item>
        <el-form-item label="星期"><el-input v-model="form.weekday_text" /></el-form-item>
        <el-form-item label="值班人"><el-input v-model="form.duty_person_name" /></el-form-item>
        <el-form-item label="来源Sheet"><el-input v-model="form.source_sheet" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="visible=false">取消</el-button>
        <el-button type="primary" @click="save">保存</el-button>
      </template>
    </el-dialog>
  </el-card>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import http from '../api/http'

const rows = ref([])
const selectedRows = ref([])
const visible = ref(false)
const form = reactive({ id: null, duty_date: '', weekday_text: '', duty_person_name: '', source_sheet: '' })
const filters = reactive({
  keyword: '',
  dateRange: [],
})

const hasActiveFilter = computed(() => {
  return Boolean(filters.keyword?.trim()) || (filters.dateRange?.length === 2)
})

const filteredRows = computed(() => {
  const keyword = (filters.keyword || '').trim().toLowerCase()
  const [start, end] = filters.dateRange || []

  return rows.value.filter((row) => {
    if (keyword) {
      const text = `${row.duty_person_name || ''} ${row.weekday_text || ''} ${row.source_sheet || ''}`.toLowerCase()
      if (!text.includes(keyword)) return false
    }

    if (start && row.duty_date < start) return false
    if (end && row.duty_date > end) return false

    return true
  })
})

const load = async () => {
  const { data } = await http.get('/schedule')
  rows.value = data
}

const onFileChange = async (file) => {
  const formData = new FormData()
  formData.append('file', file.raw)
  const { data } = await http.post('/schedule/import', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  ElMessage.success(`导入完成：新增${data.imported}，更新${data.updated}，跳过${data.skipped || 0}`)
  if (data.skipped_details?.length) {
    console.table(data.skipped_details)
  }
  load()
}

const openCreate = () => {
  Object.assign(form, { id: null, duty_date: '', weekday_text: '', duty_person_name: '', source_sheet: 'manual' })
  visible.value = true
}

const openEdit = (row) => {
  Object.assign(form, row)
  visible.value = true
}

const save = async () => {
  if (!form.duty_date || !form.duty_person_name) {
    ElMessage.warning('日期和值班人必填')
    return
  }

  const payload = {
    duty_date: form.duty_date,
    weekday_text: form.weekday_text,
    duty_person_name: form.duty_person_name,
    source_sheet: form.source_sheet,
  }

  if (form.id) {
    await http.put(`/schedule/${form.id}`, payload)
    ElMessage.success('更新成功')
  } else {
    await http.post('/schedule', payload)
    ElMessage.success('创建成功')
  }

  visible.value = false
  load()
}

const onSelectionChange = (list) => {
  selectedRows.value = list
}

const removeSelected = async () => {
  if (!selectedRows.value.length) return

  await ElMessageBox.confirm(
    `确认删除当前选中的 ${selectedRows.value.length} 条记录吗？此操作不可恢复。`,
    '删除确认',
    {
      type: 'warning',
      confirmButtonText: '确认删除',
      cancelButtonText: '取消',
    },
  )

  const ids = selectedRows.value.map((x) => x.id)
  const { data } = await http.post('/schedule/batch-delete', { ids })
  ElMessage.success(`已删除 ${data.deleted} 条记录`)
  selectedRows.value = []
  load()
}

const remove = async (id) => {
  await http.delete(`/schedule/${id}`)
  ElMessage.success('删除成功')
  load()
}

onMounted(load)
</script>