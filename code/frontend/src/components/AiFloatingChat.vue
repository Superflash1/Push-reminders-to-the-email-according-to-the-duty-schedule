<template>
  <div class="ai-entry-wrap" v-show="!visible">
    <button class="ai-entry" type="button" @click="openPanel">
      <span class="icon">⌕</span>
      <span class="text">问 AI：查询值班 / 执行换班</span>
      <span class="tag">点击展开</span>
    </button>
  </div>

  <el-drawer
    v-model="visible"
    :append-to-body="true"
    :modal="false"
    :with-header="false"
    direction="btt"
    size="78%"
    class="ai-drawer"
  >
    <div class="ai-panel">
      <div class="panel-header">
        <div>
          <div class="title">智能助手</div>
          <div class="subtitle">自然语言查值班、换班并自动记录</div>
        </div>
        <el-button text @click="visible = false">收起</el-button>
      </div>

      <div class="messages" ref="listRef">
        <div v-for="(m, idx) in messages" :key="idx" :class="['msg', m.role]">
          <div class="bubble">{{ m.content }}</div>
        </div>
      </div>

      <div class="quick">
        <el-button size="small" @click="prefill('这周谁值班？')">本周值班</el-button>
        <el-button size="small" @click="prefill('明天谁值班？')">明天值班</el-button>
        <el-button size="small" @click="prefill('把 2026-03-28 的值班人换成张三，原因是出差')">换班示例</el-button>
      </div>

      <div class="input-row">
        <el-input
          ref="inputRef"
          v-model="input"
          size="large"
          placeholder="请输入你的问题或换班指令..."
          @keyup.enter="send"
        />
        <el-button type="primary" size="large" :loading="loading" @click="send">发送</el-button>
      </div>
    </div>
  </el-drawer>
</template>

<script setup>
import { nextTick, ref } from 'vue'
import http from '../api/http'

const visible = ref(false)
const loading = ref(false)
const input = ref('')
const listRef = ref(null)
const inputRef = ref(null)

const messages = ref([
  { role: 'assistant', content: '你好，我可以帮你查询值班数据，也可以直接执行换班并记录换班日志。' },
])

const scrollToBottom = async () => {
  await nextTick()
  if (listRef.value) listRef.value.scrollTop = listRef.value.scrollHeight
}

const openPanel = async () => {
  visible.value = true
  await nextTick()
  inputRef.value?.focus?.()
  await scrollToBottom()
}

const prefill = (text) => {
  input.value = text
  inputRef.value?.focus?.()
}

const send = async () => {
  const text = input.value.trim()
  if (!text || loading.value) return

  messages.value.push({ role: 'user', content: text })
  input.value = ''
  await scrollToBottom()
  loading.value = true

  try {
    const { data } = await http.post('/ai/chat', {
      message: text,
      history: messages.value.slice(-20),
    })
    messages.value.push({ role: 'assistant', content: data.reply || '未收到回复' })
    await scrollToBottom()
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.ai-entry-wrap {
  position: fixed;
  left: 50%;
  bottom: 18px;
  transform: translateX(-50%);
  z-index: 2600;
  width: min(980px, calc(100vw - 28px));
}

.ai-entry {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 10px;
  border: 1px solid #cbd5e1;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.96);
  padding: 12px 16px;
  cursor: pointer;
  box-shadow: 0 10px 24px rgba(15, 23, 42, 0.12);
  text-align: left;
}

.ai-entry:hover {
  border-color: #93c5fd;
  box-shadow: 0 14px 28px rgba(37, 99, 235, 0.2);
}

.icon { color: #1d4ed8; }
.text { flex: 1; color: #334155; }
.tag {
  font-size: 12px;
  color: #1d4ed8;
  background: #eff6ff;
  border: 1px solid #bfdbfe;
  border-radius: 999px;
  padding: 4px 10px;
}

.ai-panel {
  height: 100%;
  display: grid;
  grid-template-rows: auto 1fr auto auto;
  gap: 10px;
  padding: 14px;
  background: #fff;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.title { font-size: 18px; font-weight: 700; color: #0f172a; }
.subtitle { font-size: 12px; color: #64748b; margin-top: 2px; }

.messages {
  overflow-y: auto;
  border: 1px solid #e2e8f0;
  border-radius: 14px;
  background: linear-gradient(180deg, #f8fafc, #f1f5f9);
  padding: 10px;
}

.msg { display: flex; margin-bottom: 10px; }
.msg.user { justify-content: flex-end; }
.msg.assistant { justify-content: flex-start; }

.bubble {
  max-width: 80%;
  padding: 10px 12px;
  border-radius: 12px;
  line-height: 1.55;
  white-space: pre-wrap;
  word-break: break-word;
}

.msg.user .bubble { background: #2563eb; color: #fff; }
.msg.assistant .bubble { background: #e2e8f0; color: #0f172a; }

.quick { display: flex; gap: 8px; flex-wrap: wrap; }
.input-row { display: grid; grid-template-columns: 1fr auto; gap: 8px; }
</style>
