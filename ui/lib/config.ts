// API Configuration
// Direct API calls to avoid Next.js proxy timeout issues with long-running batch requests
// For single requests, the proxy works fine, but batch operations can take 30+ seconds
export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export const API_ENDPOINTS = {
  categorize: `${API_BASE_URL}/categorize`,
  batchCategorize: `${API_BASE_URL}/batch-categorize`,
  feedback: `${API_BASE_URL}/feedback`,
  stats: `${API_BASE_URL}/stats`,
  health: `${API_BASE_URL}/health`,
}
