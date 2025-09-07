export interface SendResult {
  status_code: number
  snippet: string
}

export interface SynochatTestRequest {
  webhook: string
  verify_ssl: boolean
}

export interface SynochatState {
  config: {
    webhook: string
    verifySsl: boolean
  }
  loading: boolean
  testing: boolean
  lastTestResult?: SendResult
  lastTestTime?: number
  error?: string
}