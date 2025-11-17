// API Configuration
export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export const API_ENDPOINTS = {
  categorize: `${API_BASE_URL}/categorize`,
  batchCategorize: `${API_BASE_URL}/api/batch-categorize`,
  feedback: `${API_BASE_URL}/feedback`,
  stats: `${API_BASE_URL}/api/stats`,
  health: `${API_BASE_URL}/health`,
}
