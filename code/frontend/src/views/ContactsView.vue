<template>
  <el-card>
    <template #header>
      <div style="display:flex;justify-content:space-between;align-items:center;">
        <div>
          <span>人员邮箱维护</span>
          <div style="font-size:12px;color:#909399;margin-top:4px;">
            自动从值班表提取姓名；请在此补充/维护邮箱。
          </div>
        </div>
        <el-button type="primary" @click="openCreate">新增</el-button>
      </div>
    </template>

    <el-table :data="rows" border>
      <el-table-column prop="person_name" label="姓名" width="180" />
      <el-table-column prop="email" label="邮箱" />
      <el-table-column label="启用" width="100">
        <template #default="{ row }">
          <el-tag :type="row.enabled ? 'success' : 'info'">{{ row.enabled ? '是' : '否' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="remark" label="备注" />
      <el-table-column label="操作" width="180">
        <template #default="{ row }">
          <el-button size="small" @click="openEdit(row)">编辑</el-button>
          <el-button size="small" type="danger" @click="remove(row.id)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="visible" :title="form.id ? '编辑联系人' : '新增联系人'" width="480px">
      <el-form label-width="90px">
        <el-form-item label="姓名"><el-input v-model="form.person_name" /></el-form-item>
        <el-form-item label="邮箱"><el-input v-model="form.email" /></el-form-item>
        <el-form-item label="启用"><el-switch v-model="form.enabled" /></el-form-item>
        <el-form-item label="备注"><el-input v-model="form.remark" type="textarea" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="visible=false">取消</el-button>
        <el-button type="primary" @click="save">保存</el-button>
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
const form = reactive({ id: null, person_name: '', email: '', enabled: true, remark: '' })

const load = async () => {
  const { data } = await http.get('/contacts')
  rows.value = data
  ElMessage.success(`已同步联系人：${data.length} 人`)
}

const openCreate = () => {
  Object.assign(form, { id: null, person_name: '', email: '', enabled: true, remark: '' })
  visible.value = true
}

const openEdit = (row) => {
  Object.assign(form, row)
  visible.value = true
}

const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

const save = async () => {
  if (!form.person_name?.trim()) {
    ElMessage.warning('姓名必填')
    return
  }

  if (form.email && !emailRegex.test(form.email)) {
    ElMessage.warning('邮箱格式不正确')
    return
  }

  if (form.id) {
    await http.put(`/contacts/${form.id}`, form)
    ElMessage.success('更新成功')
  } else {
    await http.post('/contacts', form)
    ElMessage.success('创建成功')
  }
  visible.value = false
  load()
}

const remove = async (id) => {
  await http.delete(`/contacts/${id}`)
  ElMessage.success('删除成功')
  load()
}

onMounted(load)
</script>