'use client'

import { useState, useEffect } from 'react'
import { Activity, CheckCircle, XCircle, RefreshCw } from 'lucide-react'
import { API_ENDPOINTS } from '@/lib/config'

export default function HealthDashboard() {
  const [health, setHealth] = useState<any>(null)
  const [loading, setLoading] = useState(false)

  const fetchHealth = async () => {
    setLoading(true)
    try {
      const response = await fetch(API_ENDPOINTS.health)
      const data = await response.json()
      setHealth(data)
    } catch (error) {
      console.error('Error:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchHealth()
    const interval = setInterval(fetchHealth, 10000) // Refresh every 10s
    return () => clearInterval(interval)
  }, [])

  if (!health) {
    return (
      <div className="flex items-center justify-center py-12">
        <RefreshCw className="h-8 w-8 animate-spin text-slate-400" />
      </div>
    )
  }

  const components = health.components || {}
  const allHealthy = Object.values(components).every((status) => status === 'healthy')

  return (
    <div className="space-y-6">
      {/* Overall Status */}
      <div className={`rounded-lg p-6 ${
        allHealthy
          ? 'bg-gradient-to-br from-green-50 to-emerald-50 dark:from-green-900/20 dark:to-emerald-900/20'
          : 'bg-gradient-to-br from-red-50 to-orange-50 dark:from-red-900/20 dark:to-orange-900/20'
      }`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <Activity className={`h-8 w-8 ${allHealthy ? 'text-green-500' : 'text-red-500'}`} />
            <div>
              <h2 className="text-2xl font-bold text-slate-900 dark:text-white">
                System {health.status === 'healthy' ? 'Healthy' : 'Degraded'}
              </h2>
              <p className="text-sm text-slate-600 dark:text-slate-400">
                Last updated: {new Date(health.timestamp).toLocaleTimeString()}
              </p>
            </div>
          </div>
          <button
            onClick={fetchHealth}
            disabled={loading}
            className="p-2 rounded-lg hover:bg-white/50 dark:hover:bg-slate-800/50"
          >
            <RefreshCw className={`h-5 w-5 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Component Status Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {Object.entries(components).map(([name, status]) => {
          const isHealthy = status === 'healthy'
          return (
            <div
              key={name}
              className={`rounded-lg p-4 border-2 ${
                isHealthy
                  ? 'border-green-200 bg-green-50 dark:border-green-800 dark:bg-green-900/20'
                  : 'border-red-200 bg-red-50 dark:border-red-800 dark:bg-red-900/20'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-slate-900 dark:text-white capitalize">
                  {name.replace(/_/g, ' ')}
                </span>
                {isHealthy ? (
                  <CheckCircle className="h-5 w-5 text-green-500" />
                ) : (
                  <XCircle className="h-5 w-5 text-red-500" />
                )}
              </div>
              <p className={`text-xs font-medium ${
                isHealthy ? 'text-green-700 dark:text-green-300' : 'text-red-700 dark:text-red-300'
              }`}>
                {status}
              </p>
            </div>
          )
        })}
      </div>

      {/* System Info */}
      <div className="bg-white dark:bg-slate-800 rounded-lg p-6 border border-slate-200 dark:border-slate-700">
        <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">
          System Information
        </h3>
        <dl className="grid grid-cols-2 gap-4">
          <div>
            <dt className="text-sm text-slate-600 dark:text-slate-400">Version</dt>
            <dd className="text-base font-semibold text-slate-900 dark:text-white">{health.version}</dd>
          </div>
          <div>
            <dt className="text-sm text-slate-600 dark:text-slate-400">Status</dt>
            <dd className="text-base font-semibold text-slate-900 dark:text-white capitalize">{health.status}</dd>
          </div>
        </dl>
      </div>
    </div>
  )
}
