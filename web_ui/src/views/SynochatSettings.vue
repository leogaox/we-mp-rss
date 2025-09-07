<script setup lang="ts">
import { onMounted } from 'vue'
import { useSynochat } from '@/composables/useSynochat'
import { Message } from '@arco-design/web-vue'

const { state, loadConfig, saveConfig, testConnection, clearError } = useSynochat()

const handleSave = async () => {
  clearError()
  
  if (!state.config.webhook.trim()) {
    state.error = 'Webhook地址不能为空'
    return
  }

  const success = await saveConfig()
  if (success) {
    Message.success('配置保存成功')
  }
}

const handleTest = async () => {
  clearError()
  const result = await testConnection()
  
  if (result && result.status_code === 200) {
    Message.success('连接测试成功')
  }
}

onMounted(() => {
  loadConfig()
})
</script>

<template>
  <div class="synochat-settings">
    <h2>Synology Chat 配置</h2>
    
    <a-card class="settings-card">
      <a-form :model="state.config" layout="vertical">
        <a-form-item 
          label="Webhook 地址" 
          :validate-status="state.error ? 'error' : ''"
          :help="state.error">
          <a-input
            v-model="state.config.webhook"
            placeholder="请输入 Synology Chat Webhook 地址"
            :disabled="state.loading"
          />
          <div class="help-text">
            <a-link 
              href="https://kb.synology.com/zh-cn/DSM/help/Chat/chat_integration?version=7" 
              target="_blank">
              如何获取 Webhook
            </a-link>
          </div>
        </a-form-item>

        <a-form-item label="SSL 证书验证">
          <a-switch 
            v-model="state.config.verifySsl" 
            :disabled="state.loading"
            checked-text="启用" 
            unchecked-text="禁用" />
          <div class="help-text">
            建议保持启用以确保通信安全
          </div>
        </a-form-item>

        <a-form-item>
          <a-space>
            <a-button 
              type="primary" 
              :loading="state.loading"
              @click="handleSave">
              保存配置
            </a-button>
            
            <a-button 
              :loading="state.testing"
              @click="handleTest"
              :disabled="!state.config.webhook.trim()">
              测试连接
            </a-button>
          </a-space>
        </a-form-item>

        <a-alert 
          v-if="state.lastTestResult"
          :type="state.lastTestResult.status_code === 200 ? 'success' : 'error'">
          <template #title>
            {{ state.lastTestResult.status_code === 200 ? '测试成功' : '测试失败' }}
          </template>
          {{ state.lastTestResult.snippet }}
        </a-alert>
      </a-form>
    </a-card>

    <a-card class="info-card" title="使用说明">
      <p>1. 在 Synology DSM 中创建 Chat 机器人并获取 Webhook URL</p>
      <p>2. 将 Webhook URL 填写到上方输入框中</p>
      <p>3. 点击"测试连接"验证配置是否正确</p>
      <p>4. 点击"保存配置"使设置生效</p>
      
      <a-alert type="info" style="margin-top: 16px">
        注意：Webhook 测试有10秒冷却时间，请勿频繁点击
      </a-alert>
    </a-card>
  </div>
</template>

<style scoped>
.synochat-settings {
  padding: 20px;
  max-width: 800px;
  margin: 0 auto;
}

h2 {
  margin-bottom: 24px;
  color: var(--color-text-1);
}

.settings-card {
  margin-bottom: 24px;
}

.info-card {
  background-color: var(--color-fill-2);
}

.help-text {
  font-size: 12px;
  color: var(--color-text-3);
  margin-top: 4px;
}

.info-card p {
  margin: 8px 0;
  color: var(--color-text-2);
}
</style>