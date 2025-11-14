'use client'

import { useState, useEffect } from 'react'
import { TrendingUp, Clock, CheckCircle, AlertCircle } from 'lucide-react'

export default function StatsCards() {
  const [stats, setStats] = useState({
    totalProcessed: 0,
    avgLatency: 0,
    accuracy: 0,
    reviewRate: 0
  })

  useEffect(() => {
    // Fetch live stats from API
    const fetchStats = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/stats')
        if (response.ok) {
          const data = await response.json()
          setStats({
            totalProcessed: data.total_processed || 0,
            avgLatency: Math.round(data.avg_latency_ms || 0),
            accuracy: parseFloat((data.accuracy * 100).toFixed(1)) || 0,
            reviewRate: parseFloat((data.review_rate * 100).toFixed(1)) || 0
          })
        }
      } catch (error) {
        console.error('Failed to fetch stats:', error)
      }
    }

    // Fetch initial stats
    fetchStats()

    // Poll for updates every 5 seconds
    const interval = setInterval(fetchStats, 5000)

    return () => clearInterval(interval)
  }, [])

  const cards = [
    {
      title: 'Total Processed',
      value: stats.totalProcessed,
      suffix: '',
      icon: TrendingUp,
      color: 'blue',
      change: '+12%'
    },
    {
      title: 'Avg Latency',
      value: stats.avgLatency,
      suffix: 'ms',
      icon: Clock,
      color: 'green',
      change: '-5%'
    },
    {
      title: 'Accuracy',
      value: stats.accuracy,
      suffix: '%',
      icon: CheckCircle,
      color: 'purple',
      change: '+2.3%'
    },
    {
      title: 'Review Rate',
      value: stats.reviewRate,
      suffix: '%',
      icon: AlertCircle,
      color: 'amber',
      change: '0%'
    },
  ]

  const colorClasses = {
    blue: 'bg-blue-100 text-blue-600 dark:bg-blue-900 dark:text-blue-300',
    green: 'bg-green-100 text-green-600 dark:bg-green-900 dark:text-green-300',
    purple: 'bg-purple-100 text-purple-600 dark:bg-purple-900 dark:text-purple-300',
    amber: 'bg-amber-100 text-amber-600 dark:bg-amber-900 dark:text-amber-300',
  }

  return (
    <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
      {cards.map((card) => {
        const Icon = card.icon
        return (
          <div
            key={card.title}
            className="relative overflow-hidden rounded-lg bg-white dark:bg-slate-800 px-4 pb-12 pt-5 shadow-lg sm:px-6 sm:pt-6"
          >
            <dt>
              <div className={`absolute rounded-md p-3 ${colorClasses[card.color as keyof typeof colorClasses]}`}>
                <Icon className="h-6 w-6" aria-hidden="true" />
              </div>
              <p className="ml-16 truncate text-sm font-medium text-slate-500 dark:text-slate-400">
                {card.title}
              </p>
            </dt>
            <dd className="ml-16 flex items-baseline pb-6 sm:pb-7">
              <p className="text-2xl font-semibold text-slate-900 dark:text-white">
                {card.value}{card.suffix}
              </p>
              <p className={`ml-2 flex items-baseline text-sm font-semibold ${
                card.change.startsWith('+') ? 'text-green-600' :
                card.change.startsWith('-') ? 'text-red-600' :
                'text-slate-500'
              }`}>
                {card.change}
              </p>
            </dd>
          </div>
        )
      })}
    </div>
  )
}
