<template>
  <el-card>
    <template #header>
      <div style="display:flex;justify-content:space-between;align-items:center;">
        <span>邮件模板管理</span>
      </div>
    </template>

    <el-tabs v-model="active">
      <el-tab-pane label="正常提醒模板" name="DUTY_REMINDER" />
      <el-tab-pane label="管理员兜底模板" name="ADMIN_FALLBACK" />
    </el-tabs>

    <el-row :gutter="20">
      <el-col :span="16">
        <el-form label-width="100px">
          <el-form-item label="启用"><el-switch v-model="current.enabled" /></el-form-item>
          <el-form-item label="邮件标题"><el-input ref="subjectRef" v-model="current.subject_template" @focus="activeInsertTarget = 'subject'" /></el-form-item>
          <el-form-item label="邮件正文">
            <el-input ref="bodyRef" v-model="current.body_template" type="textarea" :rows="12" @focus="activeInsertTarget = 'body'" />
          </el-form-item>
        </el-form>
        <el-button type="primary" @click="save">保存模板</el-button>
        <el-button @click="preview">预览</el-button>
      </el-col>

      <el-col :span="8">
        <el-card>
          <template #header>变量说明（点击可复制）</template>
          <div v-for="v in vars" :key="v" style="margin-bottom:8px; cursor:pointer" @click="copy(v)">{{ v }}</div>
        </el-card>

        <el-card style="margin-top: 16px">
          <template #header>预览结果</template>
          <div><b>Subject:</b> {{ previewData.subject }}</div>
          <pre style="white-space:pre-wrap">{{ previewData.body }}</pre>
        </el-card>
      </el-col>
    </el-row>
  </el-card>
</template>

<script setup>
import { computed, nextTick, onMounted, reactive, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import http from '../api/http'

const active = ref('DUTY_REMINDER')
const templates = ref([])
const previewData = reactive({ subject: '', body: '' })
const subjectRef = ref()
const bodyRef = ref()
const activeInsertTarget = ref('body')

const vars = [
  '{{duty_date}}','{{weekday}}','{{duty_person_name}}','{{duty_person_email}}',
  '{{rule_day_label}}','{{rule_time}}','{{now}}','{{admin_emails}}','{{missing_reason}}'
]

const current = computed(() => templates.value.find(x => x.template_type === active.value) || {
  template_type: active.value,
  subject_template: '',
  body_template: '',
  enabled: true,
})

const load = async () => {
  const { data } = await http.get('/mail-templates')
  templates.value = data
}

const save = async () => {
  if (!current.value.subject_template?.trim()) {
    ElMessage.warning('邮件标题不能为空')
    return
  }
  if (!current.value.body_template?.trim()) {
    ElMessage.warning('邮件正文不能为空')
    return
  }

  await http.put(`/mail-templates/${active.value}`, {
    subject_template: current.value.subject_template,
    body_template: current.value.body_template,
    enabled: current.value.enabled,
  })
  ElMessage.success('模板已保存')
}

const preview = async () => {
  const { data } = await http.post('/mail-templates/preview', {
    subject_template: current.value.subject_template,
    body_template: current.value.body_template,
    variables: {
      duty_date: '2026-03-26',
      weekday: '周四',
      duty_person_name: '张三',
      duty_person_email: 'zhangsan@example.com',
      rule_day_label: '当天',
      rule_time: '09:00',
      now: '2026-03-26 09:00:00',
      admin_emails: 'admin@example.com',
      missing_reason: '未配置邮箱或邮箱已禁用',
    },
  })
  previewData.subject = data.subject
  previewData.body = data.body
}

const copy = async (v) => {
  const target = activeInsertTarget.value === 'subject' ? subjectRef.value?.input : bodyRef.value?.textarea
  if (target) {
    const start = target.selectionStart ?? target.value.length
    const end = target.selectionEnd ?? target.value.length
    const oldText = target.value || ''
    const newText = oldText.slice(0, start) + v + oldText.slice(end)

    if (activeInsertTarget.value === 'subject') {
      current.value.subject_template = newText
    } else {
      current.value.body_template = newText
    }

    await nextTick()
    const pos = start + v.length
    target.focus()
    target.setSelectionRange(pos, pos)
    ElMessage.success('已插入变量')
  } else {
    await navigator.clipboard.writeText(v)
    ElMessage.success('已复制变量')
  }
}

onMounted(load)
watch(active, () => { previewData.subject = ''; previewData.body = '' })
</script>