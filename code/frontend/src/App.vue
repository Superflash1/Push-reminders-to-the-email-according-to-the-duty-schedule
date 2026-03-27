<template>
  <el-container style="height: 100vh">
    <el-aside width="220px" style="background: #0f172a; color: #fff">
      <div style="padding: 20px; font-weight: 700">值班提醒系统</div>
      <el-menu
        router
        background-color="#0f172a"
        text-color="#cbd5e1"
        active-text-color="#60a5fa"
      >
        <el-menu-item index="/schedule">值班表</el-menu-item>
        <el-menu-item index="/contacts">人员邮箱</el-menu-item>
        <el-menu-item index="/rules">提醒规则</el-menu-item>
        <el-menu-item index="/templates">邮件模板</el-menu-item>
        <el-menu-item index="/settings">系统设置</el-menu-item>
        <el-menu-item index="/logs">发送日志</el-menu-item>
        <el-menu-item index="/shift-changes">换班记录</el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header style="border-bottom: 1px solid #e5e7eb; display:flex; align-items:center; justify-content: space-between;">
        <span style="font-weight: 600">管理后台</span>
      </el-header>
      <el-main style="background: #f8fafc">
        <router-view />
      </el-main>
    </el-container>
  </el-container>

  <AiFloatingChat />
</template>

<script setup>
import AiFloatingChat from './components/AiFloatingChat.vue'
</script>
