<template>
  <el-card>
    <template #header>
      <div style="display:flex;justify-content:space-between;align-items:center;">
        <span>系统设置</span>
      </div>
    </template>

    <el-form label-width="140px" style="max-width: 820px">
      <el-form-item label="管理员邮箱">
        <el-select v-model="adminEmailList" multiple filterable allow-create default-first-option style="width:100%" placeholder="输入后回车，可添加多个">
          <el-option v-for="item in adminEmailList" :key="item" :label="item" :value="item" />
        </el-select>
      </el-form-item>
      <el-form-item label="时区">
        <el-input v-model="form.timezone" />
      </el-form-item>
      <el-form-item label="SMTP Host">
        <el-input v-model="form.mail_host" />
      </el-form-item>
      <el-form-item label="SMTP Port">
        <el-input-number v-model="form.mail_port" :min="1" :max="65535" />
      </el-form-item>
      <el-form-item label="SMTP User">
        <el-input v-model="form.mail_user" />
      </el-form-item>
      <el-form-item label="SMTP Password">
        <el-input v-model="form.mail_password" show-password />
      </el-form-item>
      <el-form-item label="Mail From">
        <el-input v-model="form.mail_from" />
      </el-form-item>

      <el-divider>AI（OpenAI兼容）</el-divider>

      <el-form-item label="启用AI">
        <el-switch v-model="form.ai_enabled" />
      </el-form-item>
      <el-form-item label="Base URL">
        <el-input v-model="form.ai_base_url" placeholder="例如：https://api.openai.com/v1" />
      </el-form-item>
      <el-form-item label="API Key">
        <el-input v-model="form.ai_api_key" show-password placeholder="sk-..." />
      </el-form-item>
      <el-form-item label="模型名称">
        <el-input v-model="form.ai_model" placeholder="例如：gpt-4o-mini" />
      </el-form-item>
      <el-form-item label="温度(0~1)">
        <el-slider v-model="form.ai_temperature" :min="0" :max="1" :step="0.05" style="width: 360px" />
      </el-form-item>
    </el-form>

    <el-space>
      <el-button type="primary" @click="save">保存设置</el-button>
      <el-input v-model="testMail" placeholder="测试收件邮箱" style="width:260px" />
      <el-button @click="sendTest">测试发信</el-button>
      <el-button type="success" @click="runOnce">手动执行提醒</el-button>
    </el-space>
  </el-card>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import http from '../api/http'

const adminEmailList = ref([])

const form = reactive({
  admin_emails: '',
  timezone: 'Asia/Shanghai',
  mail_host: '',
  mail_port: 465,
  mail_user: '',
  mail_password: '',
  mail_from: '',
  ai_enabled: false,
  ai_base_url: '',
  ai_api_key: '',
  ai_model: '',
  ai_temperature: 0.2,
})

const testMail = ref('')

const load = async () => {
  const { data } = await http.get('/settings')
  Object.assign(form, data)
  adminEmailList.value = (data.admin_emails || '').split(',').map((x) => x.trim()).filter(Boolean)
}

const save = async () => {
  const payload = {
    ...form,
    admin_emails: adminEmailList.value.join(','),
  }
  await http.put('/settings', payload)
  ElMessage.success('设置已保存')
}

const sendTest = async () => {
  if (!testMail.value) return ElMessage.warning('请输入测试收件邮箱')
  await http.post('/settings/test-mail', { to_email: testMail.value })
  ElMessage.success('测试邮件已发送')
}

const runOnce = async () => {
  const { data } = await http.post('/reminders/run-once')
  ElMessage.success(`执行完成，处理 ${data.processed_rules} 条`)
}

onMounted(load)
</script>
