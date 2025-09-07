import { ref, reactive } from 'vue'
import { getSynochatConfig, updateSynochatConfig, testSynochatConnection } from '@/api/synochat'
import type { SynochatState, SendResult } from '@/types/synochat'

const COOLING_PERIOD = 10000 // 10 seconds

export const useSynochat = () => {
  const state = reactive<SynochatState>({
    config: {
      webhook: '',
      verifySsl: true
    },
    loading: false,
    testing: false,
    lastTestResult: undefined,
    lastTestTime: undefined,
    error: undefined
  })

  const loadConfig = async () => {
    state.loading = true
    state.error = undefined
    
    try {
      const config = await getSynochatConfig()
      state.config = config
    } catch (error: any) {
      state.error = error.message || 'Failed to load configuration'
      console.error('Failed to load Synochat config:', error)
    } finally {
      state.loading = false
    }
  }

  const saveConfig = async (): Promise<boolean> => {
    state.loading = true
    state.error = undefined
    
    try {
      await updateSynochatConfig(state.config)
      return true
    } catch (error: any) {
      state.error = error.message || 'Failed to save configuration'
      console.error('Failed to save Synochat config:', error)
      return false
    } finally {
      state.loading = false
    }
  }

  const testConnection = async (): Promise<SendResult | null> => {
    const now = Date.now()
    if (state.lastTestTime && now - state.lastTestTime < COOLING_PERIOD) {
      state.error = '请等待10秒后再试'
      return null
    }

    if (!state.config.webhook.trim()) {
      state.error = 'Webhook地址不能为空'
      return null
    }

    state.testing = true
    state.error = undefined
    
    try {
      const result = await testSynochatConnection(state.config.webhook, state.config.verifySsl)
      state.lastTestResult = result
      state.lastTestTime = now
      
      if (result.status_code >= 400) {
        state.error = `测试失败: ${result.snippet}`
      }
      
      return result
    } catch (error: any) {
      const result: SendResult = {
        status_code: error.status_code || 0,
        snippet: error.snippet || error.message || '未知错误'
      }
      
      state.lastTestResult = result
      state.lastTestTime = now
      state.error = `测试失败: ${result.snippet}`
      
      return result
    } finally {
      state.testing = false
    }
  }

  const clearError = () => {
    state.error = undefined
  }

  const clearTestResult = () => {
    state.lastTestResult = undefined
    state.lastTestTime = undefined
  }

  return {
    state,
    loadConfig,
    saveConfig,
    testConnection,
    clearError,
    clearTestResult
  }
}