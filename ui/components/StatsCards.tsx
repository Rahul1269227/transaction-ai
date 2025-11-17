'use client'

import { useState, useEffect } from 'react'
import { TrendingUp, Clock, CheckCircle, AlertCircle } from 'lucide-react'
import { API_ENDPOINTS } from '@/lib/config'

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
        const response = await fetch(API_ENDPOINTS.stats)
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

    // Poll for updates every 60 seconds (1 minute)
    const interval = setInterval(fetchStats, 60000)

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

  const gradientClasses = {
    blue: 'from-blue-500 to-blue-600',
    green: 'from-green-500 to-emerald-600',
    purple: 'from-purple-500 to-purple-600',
    amber: 'from-amber-500 to-orange-600',
  }

  return (
    <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
      {cards.map((card, index) => {
        const Icon = card.icon
        return (
          <div
            key={card.title}
            className="group relative overflow-hidden rounded-2xl glass dark:glass-dark premium-shadow-lg border premium-border transform hover:scale-105 transition-all duration-300 animate-slide-up"
            style={{ animationDelay: `${index * 100}ms` }}
          >
            {/* Premium gradient background */}
            <div className={`absolute inset-0 bg-gradient-to-br ${gradientClasses[card.color as keyof typeof gradientClasses]} opacity-5 group-hover:opacity-10 transition-opacity`}></div>

            <div className="relative p-6">
              <div className="flex items-center justify-between mb-4">
                <div className={`relative rounded-2xl p-4 bg-gradient-to-br ${gradientClasses[card.color as keyof typeof gradientClasses]} shadow-lg group-hover:scale-110 transition-transform duration-300`}>
                  <div className="absolute inset-0 bg-white dark:bg-slate-900 opacity-0 group-hover:opacity-10 rounded-2xl transition-opacity"></div>
                  <Icon className="h-7 w-7 text-white relative z-10" aria-hidden="true" />
                </div>
                <div className={`flex items-center space-x-1 px-3 py-1.5 rounded-xl text-xs font-bold ${
                  card.change.startsWith('+')
                    ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 border border-green-200 dark:border-green-800'
                    : card.change.startsWith('-')
                    ? 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300 border border-red-200 dark:border-red-800'
                    : 'bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-400 border border-slate-200 dark:border-slate-600'
                }`}>
                  <span>{card.change.startsWith('+') ? '↗' : card.change.startsWith('-') ? '↘' : '→'}</span>
                  <span>{card.change}</span>
                </div>
              </div>

              <div className="space-y-2">
                <p className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                  {card.title}
                </p>
                <p className={`text-4xl font-black bg-gradient-to-br ${gradientClasses[card.color as keyof typeof gradientClasses]} bg-clip-text text-transparent`}>
                  {card.value}{card.suffix}
                </p>
              </div>

              {/* Animated border glow on hover */}
              <div className={`absolute inset-0 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none`}>
                <div className={`absolute inset-0 rounded-2xl bg-gradient-to-br ${gradientClasses[card.color as keyof typeof gradientClasses]} blur-xl opacity-20`}></div>
              </div>
            </div>
          </div>
        )
      })}
    </div>
  )
}
