// API Configuration
// Use relative URLs to leverage Next.js API proxy (/api/* -> http://localhost:8000/*)
// The proxy is configured in next.config.js
export const API_BASE_URL = '/api'

export const API_ENDPOINTS = {
  categorize: `${API_BASE_URL}/categorize`,
  batchCategorize: `${API_BASE_URL}/batch-categorize`,
  feedback: `${API_BASE_URL}/feedback`,
  stats: `${API_BASE_URL}/stats`,
  health: `${API_BASE_URL}/health`,
}
