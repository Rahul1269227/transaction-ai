'use client'

import { useState, useEffect } from 'react'
import { Activity, TrendingUp, Zap, Database, Brain, CheckCircle2, AlertCircle, Upload } from 'lucide-react'
import TransactionCategorizer from '@/components/TransactionCategorizer'
import EnsembleVoting from '@/components/EnsembleVoting'
import HealthDashboard from '@/components/HealthDashboard'
import FeedbackForm from '@/components/FeedbackForm'
import StatsCards from '@/components/StatsCards'
import BatchUpload from '@/components/BatchUpload'

export default function Dashboard() {
  const [activeTab, setActiveTab] = useState('demo')

  return (
    <div className="min-h-screen">
      {/* Premium Header with Glassmorphism */}
      <header className="glass dark:glass-dark border-b premium-border sticky top-0 z-50 backdrop-blur-xl">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="relative">
                <div className="absolute inset-0 bg-gradient-to-br from-blue-500 to-purple-600 rounded-2xl blur-md opacity-75 animate-glow"></div>
                <div className="relative w-14 h-14 bg-gradient-to-br from-blue-500 via-purple-500 to-purple-600 rounded-2xl flex items-center justify-center transform hover:scale-105 transition-transform duration-200">
                  <Brain className="w-7 h-7 text-white drop-shadow-lg" />
                </div>
              </div>
              <div>
                <h1 className="text-3xl font-black gradient-text tracking-tight">
                  Transaction AI
                </h1>
                <p className="text-sm text-slate-600 dark:text-slate-400 font-medium mt-0.5">
                  Enterprise-Grade Ensemble Categorization
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-3">
              <div className="glass dark:glass-dark px-4 py-2 rounded-xl premium-border">
                <span className="inline-flex items-center text-sm font-semibold bg-gradient-to-r from-green-600 to-emerald-600 bg-clip-text text-transparent">
                  <span className="w-2.5 h-2.5 bg-gradient-to-r from-green-500 to-emerald-500 rounded-full mr-2 animate-pulse shadow-lg shadow-green-500/50"></span>
                  System Online
                </span>
              </div>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats Cards */}
        <StatsCards />

        {/* Premium Tabs */}
        <div className="mt-8 glass dark:glass-dark rounded-2xl premium-shadow-lg overflow-hidden premium-border animate-slide-up">
          <div className="border-b premium-border bg-gradient-to-r from-slate-50/50 to-slate-100/50 dark:from-slate-800/50 dark:to-slate-900/50">
            <nav className="-mb-px flex space-x-1 px-6 py-2" aria-label="Tabs">
              {[
                { id: 'demo', name: 'Categorize', icon: Zap },
                { id: 'batch', name: 'Batch Upload', icon: Upload },
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
                        ? 'bg-white dark:bg-slate-700 shadow-md premium-shadow text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-purple-600'
                        : 'text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-200 hover:bg-white/50 dark:hover:bg-slate-700/50'
                    }
                    group inline-flex items-center py-3 px-4 rounded-xl font-semibold text-sm transition-all duration-200 transform hover:scale-105
                  `}
                >
                  <tab.icon className={`
                    ${activeTab === tab.id ? 'text-purple-500' : 'text-slate-400 dark:text-slate-500 group-hover:text-slate-600 dark:group-hover:text-slate-300'}
                    -ml-0.5 mr-2 h-5 w-5 transition-colors
                  `} />
                  <span className={activeTab === tab.id ? 'font-bold' : ''}>{tab.name}</span>
                </button>
              ))}
            </nav>
          </div>

          {/* Tab Content */}
          <div className="p-8 backdrop-blur-sm">
            {activeTab === 'demo' && <TransactionCategorizer />}
            {activeTab === 'batch' && <BatchUpload />}
            {activeTab === 'ensemble' && <EnsembleVoting />}
            {activeTab === 'health' && <HealthDashboard />}
            {activeTab === 'feedback' && <FeedbackForm />}
          </div>
        </div>

        {/* Premium Footer */}
        <div className="mt-12 text-center pb-8">
          <div className="glass dark:glass-dark rounded-2xl px-8 py-6 premium-shadow inline-block premium-border">
            <p className="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2">
              Powered by <span className="gradient-text font-bold">Hybrid AI Architecture</span>
            </p>
            <div className="flex items-center justify-center space-x-3 text-xs text-slate-600 dark:text-slate-400">
              <span className="inline-flex items-center px-3 py-1 rounded-full bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-900/20 dark:to-purple-900/20 border border-blue-200 dark:border-blue-800">
                Rule Engine
              </span>
              <span className="text-slate-400">+</span>
              <span className="inline-flex items-center px-3 py-1 rounded-full bg-gradient-to-r from-purple-50 to-pink-50 dark:from-purple-900/20 dark:to-pink-900/20 border border-purple-200 dark:border-purple-800">
                ML Embeddings
              </span>
              <span className="text-slate-400">+</span>
              <span className="inline-flex items-center px-3 py-1 rounded-full bg-gradient-to-r from-pink-50 to-rose-50 dark:from-pink-900/20 dark:to-rose-900/20 border border-pink-200 dark:border-pink-800">
                LLM Reasoning
              </span>
            </div>
            <p className="text-xs text-slate-500 dark:text-slate-500 mt-3 font-medium">
              🔒 100% Local • 🚀 Zero External APIs • 🛡️ Privacy-First Architecture
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
