'use client'

import { useState, useEffect } from 'react'
import { Activity, TrendingUp, Zap, Database, Brain, CheckCircle2, AlertCircle } from 'lucide-react'
import CategorizationDemo from '@/components/CategorizationDemo'
import EnsembleVoting from '@/components/EnsembleVoting'
import HealthDashboard from '@/components/HealthDashboard'
import FeedbackForm from '@/components/FeedbackForm'
import StatsCards from '@/components/StatsCards'

export default function Dashboard() {
  const [activeTab, setActiveTab] = useState('demo')

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
      {/* Header */}
      <header className="bg-white dark:bg-slate-800 shadow-sm border-b border-slate-200 dark:border-slate-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                <Brain className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
                  Transaction AI
                </h1>
                <p className="text-sm text-slate-600 dark:text-slate-400">
                  Ensemble Categorization System
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">
                <span className="w-2 h-2 bg-green-500 rounded-full mr-2 animate-pulse"></span>
                Live
              </span>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats Cards */}
        <StatsCards />

        {/* Tabs */}
        <div className="mt-8 bg-white dark:bg-slate-800 rounded-lg shadow-lg overflow-hidden">
          <div className="border-b border-slate-200 dark:border-slate-700">
            <nav className="-mb-px flex space-x-8 px-6" aria-label="Tabs">
              {[
                { id: 'demo', name: 'Live Demo', icon: Zap },
                { id: 'ensemble', name: 'Ensemble Voting', icon: TrendingUp },
                { id: 'health', name: 'System Health', icon: Activity },
                { id: 'feedback', name: 'Feedback', icon: CheckCircle2 },
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`
                    ${
                      activeTab === tab.id
                        ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                        : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300 dark:text-slate-400 dark:hover:text-slate-300'
                    }
                    group inline-flex items-center py-4 px-1 border-b-2 font-medium text-sm
                  `}
                >
                  <tab.icon className={`
                    ${activeTab === tab.id ? 'text-blue-500 dark:text-blue-400' : 'text-slate-400 dark:text-slate-500'}
                    -ml-0.5 mr-2 h-5 w-5
                  `} />
                  <span>{tab.name}</span>
                </button>
              ))}
            </nav>
          </div>

          {/* Tab Content */}
          <div className="p-6">
            {activeTab === 'demo' && <CategorizationDemo />}
            {activeTab === 'ensemble' && <EnsembleVoting />}
            {activeTab === 'health' && <HealthDashboard />}
            {activeTab === 'feedback' && <FeedbackForm />}
          </div>
        </div>

        {/* Footer Info */}
        <div className="mt-8 text-center">
          <p className="text-sm text-slate-600 dark:text-slate-400">
            Powered by <span className="font-semibold">Rule Engine + ML Embeddings + LLM Reasoning</span>
          </p>
          <p className="text-xs text-slate-500 dark:text-slate-500 mt-1">
            100% Local • No External APIs • Privacy-First
          </p>
        </div>
      </div>
    </div>
  )
}
