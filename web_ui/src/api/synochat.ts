import http from './http'
import type { SendResult } from '@/types/synochat'

export interface SynochatConfig {
  webhook: string
  verifySsl: boolean
}

export const getSynochatConfig = async (): Promise<SynochatConfig> => {
  try {
    const [webhookRes, verifySslRes] = await Promise.all([
      http.get<string>('/wx/configs/notify.synochat.webhook'),
      http.get<string>('/wx/configs/notify.synochat.verify_ssl')
    ])
    
    return {
      webhook: webhookRes.data || '',
      verifySsl: verifySslRes.data?.toLowerCase() === 'true'
    }
  } catch (error) {
    console.error('Failed to fetch Synochat config:', error)
    return {
      webhook: '',
      verifySsl: true
    }
  }
}

export const updateSynochatConfig = async (config: Partial<SynochatConfig>): Promise<void> => {
  const updates: Promise<any>[] = []
  
  if (config.webhook !== undefined) {
    updates.push(
      http.put('/wx/configs/notify.synochat.webhook', {
        config_value: config.webhook
      })
    )
  }
  
  if (config.verifySsl !== undefined) {
    updates.push(
      http.put('/wx/configs/notify.synochat.verify_ssl', {
        config_value: config.verifySsl.toString()
      })
    )
  }
  
  await Promise.all(updates)
}

export const testSynochatConnection = async (webhook: string, verifySsl: boolean = true): Promise<SendResult> => {
  try {
    const response = await http.post<SendResult>('/wx/synochat/test', {
      webhook,
      verify_ssl: verifySsl
    })
    
    return response.data
  } catch (error: any) {
    if (error.response?.data) {
      throw error.response.data
    }
    throw {
      status_code: 0,
      snippet: error.message || 'Network error'
    }
  }
}