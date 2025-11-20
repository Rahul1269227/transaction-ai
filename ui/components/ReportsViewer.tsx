'use client'

import { useState, useEffect } from 'react'
import { FileText, CheckCircle, AlertTriangle, BarChart3, TrendingUp, Target, Award, Download } from 'lucide-react'

interface EvaluationReport {
  model: string
  test_data: string
  samples: number
  date: string
  requirement: string
  status: string
  metrics: {
    accuracy: number
    macro_f1: number
    macro_precision: number
    macro_recall: number
    weighted_f1: number
    avg_confidence: number
  }
  requirement_met: boolean
  per_class_metrics: {
    [key: string]: {
      precision: number
      recall: number
      f1_score: number
      support: number
    }
  }
  misclassifications?: Array<{
    category: string
    total: number
    correct: number
    incorrect: number
    accuracy: number
  }>
}

export default function ReportsViewer() {
  const [report, setReport] = useState<EvaluationReport | null>(null)
  const [loading, setLoading] = useState(true)
  const [activeView, setActiveView] = useState<'overview' | 'detailed' | 'errors'>('overview')

  useEffect(() => {
    // Load the evaluation report
    fetch('/api/reports/evaluation')
      .then(res => res.json())
      .then(data => {
        setReport(data)
        setLoading(false)
      })
      .catch(err => {
        console.error('Error loading report:', err)
        setLoading(false)
      })
  }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500"></div>
      </div>
    )
  }

  if (!report) {
    return (
      <div className="text-center py-12 text-slate-500">
        <FileText className="w-12 h-12 mx-auto mb-3 opacity-50" />
        <p>No evaluation reports available</p>
      </div>
    )
  }

  const formatPercent = (val: number) => `${(val * 100).toFixed(2)}%`
  const topPerformers = Object.entries(report.per_class_metrics)
    .sort((a, b) => b[1].f1_score - a[1].f1_score)
    .slice(0, 5)

  const bottomPerformers = Object.entries(report.per_class_metrics)
    .sort((a, b) => a[1].f1_score - b[1].f1_score)
    .slice(0, 5)

  return (
    <div className="space-y-6">
      {/* Header Stats */}
      <div className="glass dark:glass-dark rounded-2xl p-6 premium-shadow premium-border">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-bold text-slate-800 dark:text-slate-100 flex items-center">
            <Award className="w-6 h-6 mr-2 text-purple-500" />
            Model Evaluation Report
          </h2>
          <div className="flex items-center space-x-3">
            <span className={`text-xs font-semibold px-4 py-2 rounded-full ${
              report.requirement_met
                ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400 border border-green-200 dark:border-green-800'
                : 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400 border border-red-200 dark:border-red-800'
            }`}>
              {report.status}
            </span>
            <button className="p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors">
              <Download className="w-5 h-5 text-slate-600 dark:text-slate-400" />
            </button>
          </div>
        </div>

        {/* Key Metrics Grid */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-gradient-to-br from-green-50 to-emerald-50 dark:from-green-900/20 dark:to-emerald-900/20 rounded-xl p-4 border border-green-200 dark:border-green-800">
            <div className="flex items-center justify-between mb-2">
              <div className="text-sm font-medium text-green-700 dark:text-green-400">Accuracy</div>
              <Target className="w-4 h-4 text-green-500" />
            </div>
            <div className="text-3xl font-black text-green-900 dark:text-green-100">
              {formatPercent(report.metrics.accuracy)}
            </div>
            <div className="text-xs text-green-600 dark:text-green-400 mt-1 flex items-center">
              <CheckCircle className="w-3 h-3 mr-1" /> Exceptional
            </div>
          </div>

          <div className={`bg-gradient-to-br ${
            report.metrics.macro_f1 >= 0.90
              ? 'from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 border-blue-200 dark:border-blue-800'
              : 'from-yellow-50 to-orange-50 dark:from-yellow-900/20 dark:to-orange-900/20 border-yellow-200 dark:border-yellow-800'
          } rounded-xl p-4 border`}>
            <div className="flex items-center justify-between mb-2">
              <div className={`text-sm font-medium ${
                report.metrics.macro_f1 >= 0.90
                  ? 'text-blue-700 dark:text-blue-400'
                  : 'text-yellow-700 dark:text-yellow-400'
              }`}>Macro F1-Score</div>
              <TrendingUp className={`w-4 h-4 ${
                report.metrics.macro_f1 >= 0.90 ? 'text-blue-500' : 'text-yellow-500'
              }`} />
            </div>
            <div className={`text-3xl font-black ${
              report.metrics.macro_f1 >= 0.90
                ? 'text-blue-900 dark:text-blue-100'
                : 'text-yellow-900 dark:text-yellow-100'
            }`}>
              {report.metrics.macro_f1.toFixed(4)}
            </div>
            <div className={`text-xs mt-1 flex items-center ${
              report.metrics.macro_f1 >= 0.90
                ? 'text-blue-600 dark:text-blue-400'
                : 'text-yellow-600 dark:text-yellow-400'
            }`}>
              {report.metrics.macro_f1 >= 0.90 ? (
                <><CheckCircle className="w-3 h-3 mr-1" /> Target ≥ 0.90 Met</>
              ) : (
                <><AlertTriangle className="w-3 h-3 mr-1" /> Below Target</>
              )}
            </div>
          </div>

          <div className="bg-gradient-to-br from-purple-50 to-pink-50 dark:from-purple-900/20 dark:to-pink-900/20 rounded-xl p-4 border border-purple-200 dark:border-purple-800">
            <div className="flex items-center justify-between mb-2">
              <div className="text-sm font-medium text-purple-700 dark:text-purple-400">Weighted F1</div>
              <BarChart3 className="w-4 h-4 text-purple-500" />
            </div>
            <div className="text-3xl font-black text-purple-900 dark:text-purple-100">
              {report.metrics.weighted_f1.toFixed(4)}
            </div>
            <div className="text-xs text-purple-600 dark:text-purple-400 mt-1">
              By class support
            </div>
          </div>

          <div className="bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-800/50 dark:to-slate-900/50 rounded-xl p-4 border border-slate-200 dark:border-slate-700">
            <div className="flex items-center justify-between mb-2">
              <div className="text-sm font-medium text-slate-700 dark:text-slate-400">Avg Confidence</div>
              <FileText className="w-4 h-4 text-slate-500" />
            </div>
            <div className="text-3xl font-black text-slate-900 dark:text-slate-100">
              {formatPercent(report.metrics.avg_confidence)}
            </div>
            <div className="text-xs text-slate-600 dark:text-slate-400 mt-1">
              {report.samples.toLocaleString()} samples
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex space-x-2 mb-6 border-b border-slate-200 dark:border-slate-700">
          {['overview', 'detailed', 'errors'].map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveView(tab as typeof activeView)}
              className={`px-4 py-2 text-sm font-semibold transition-all ${
                activeView === tab
                  ? 'text-purple-600 border-b-2 border-purple-600'
                  : 'text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200'
              }`}
            >
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </div>

        {/* Overview View */}
        {activeView === 'overview' && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Top Performers */}
              <div className="bg-slate-50 dark:bg-slate-800/50 rounded-xl p-4 border border-slate-200 dark:border-slate-700">
                <h3 className="text-sm font-bold text-slate-700 dark:text-slate-300 mb-3 flex items-center">
                  <Award className="w-4 h-4 mr-2 text-green-500" />
                  Top 5 Categories
                </h3>
                <div className="space-y-2">
                  {topPerformers.map(([category, metrics]) => (
                    <div key={category} className="flex items-center justify-between">
                      <span className="text-sm text-slate-700 dark:text-slate-300">{category}</span>
                      <div className="flex items-center space-x-2">
                        <div className="w-24 bg-slate-200 dark:bg-slate-700 rounded-full h-2">
                          <div
                            className="bg-gradient-to-r from-green-500 to-emerald-500 h-2 rounded-full"
                            style={{ width: `${metrics.f1_score * 100}%` }}
                          />
                        </div>
                        <span className="text-xs font-semibold text-slate-600 dark:text-slate-400 w-14 text-right">
                          {formatPercent(metrics.f1_score)}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Bottom Performers */}
              <div className="bg-slate-50 dark:bg-slate-800/50 rounded-xl p-4 border border-slate-200 dark:border-slate-700">
                <h3 className="text-sm font-bold text-slate-700 dark:text-slate-300 mb-3 flex items-center">
                  <AlertTriangle className="w-4 h-4 mr-2 text-yellow-500" />
                  Needs Attention
                </h3>
                <div className="space-y-2">
                  {bottomPerformers.map(([category, metrics]) => (
                    <div key={category} className="flex items-center justify-between">
                      <span className="text-sm text-slate-700 dark:text-slate-300">{category}</span>
                      <div className="flex items-center space-x-2">
                        <div className="w-24 bg-slate-200 dark:bg-slate-700 rounded-full h-2">
                          <div
                            className="bg-gradient-to-r from-yellow-500 to-orange-500 h-2 rounded-full"
                            style={{ width: `${metrics.f1_score * 100}%` }}
                          />
                        </div>
                        <span className="text-xs font-semibold text-slate-600 dark:text-slate-400 w-14 text-right">
                          {formatPercent(metrics.f1_score)}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-xl p-4">
              <h3 className="text-sm font-bold text-blue-900 dark:text-blue-100 mb-2">Summary</h3>
              <ul className="space-y-1 text-sm text-blue-800 dark:text-blue-200">
                <li>• {Object.keys(report.per_class_metrics).length} categories evaluated</li>
                <li>• {Object.values(report.per_class_metrics).filter(m => m.f1_score === 1.0).length} categories with perfect F1 (100%)</li>
                <li>• {Object.values(report.per_class_metrics).filter(m => m.f1_score >= 0.99).length} categories above 99% F1</li>
                <li>• Average support per category: {Math.round(report.samples / Object.keys(report.per_class_metrics).length)}</li>
              </ul>
            </div>
          </div>
        )}

        {/* Detailed View */}
        {activeView === 'detailed' && (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 dark:divide-slate-700">
              <thead className="bg-slate-50 dark:bg-slate-800">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 dark:text-slate-300">Category</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold text-slate-600 dark:text-slate-300">Precision</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold text-slate-600 dark:text-slate-300">Recall</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold text-slate-600 dark:text-slate-300">F1-Score</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold text-slate-600 dark:text-slate-300">Support</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 dark:divide-slate-800">
                {Object.entries(report.per_class_metrics)
                  .sort((a, b) => b[1].f1_score - a[1].f1_score)
                  .map(([category, metrics]) => (
                    <tr key={category} className="hover:bg-slate-50 dark:hover:bg-slate-800/50">
                      <td className="px-4 py-3 text-sm font-medium text-slate-900 dark:text-slate-100">{category}</td>
                      <td className="px-4 py-3 text-sm text-right text-slate-700 dark:text-slate-300">{formatPercent(metrics.precision)}</td>
                      <td className="px-4 py-3 text-sm text-right text-slate-700 dark:text-slate-300">{formatPercent(metrics.recall)}</td>
                      <td className="px-4 py-3 text-sm text-right">
                        <span className={`font-semibold ${
                          metrics.f1_score === 1.0 ? 'text-green-600 dark:text-green-400' :
                          metrics.f1_score >= 0.99 ? 'text-blue-600 dark:text-blue-400' :
                          metrics.f1_score >= 0.95 ? 'text-purple-600 dark:text-purple-400' :
                          'text-yellow-600 dark:text-yellow-400'
                        }`}>
                          {formatPercent(metrics.f1_score)}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-sm text-right text-slate-500 dark:text-slate-400">{metrics.support}</td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Errors View */}
        {activeView === 'errors' && report.misclassifications && (
          <div className="space-y-4">
            <p className="text-sm text-slate-600 dark:text-slate-400 mb-4">
              Categories with misclassifications (total errors: {report.misclassifications.reduce((sum, m) => sum + m.incorrect, 0)})
            </p>
            <div className="space-y-3">
              {report.misclassifications.map((item) => (
                <div key={item.category} className="bg-slate-50 dark:bg-slate-800/50 rounded-lg p-4 border border-slate-200 dark:border-slate-700">
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="text-sm font-semibold text-slate-800 dark:text-slate-200">{item.category}</h4>
                    <span className="text-xs font-medium px-2 py-1 rounded-full bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400">
                      {formatPercent(item.accuracy)} accurate
                    </span>
                  </div>
                  <div className="flex items-center space-x-4 text-sm text-slate-600 dark:text-slate-400">
                    <span>{item.correct} correct</span>
                    <span>•</span>
                    <span className="text-red-600 dark:text-red-400">{item.incorrect} incorrect</span>
                    <span>•</span>
                    <span>{item.total} total</span>
                  </div>
                  <div className="mt-2 w-full bg-slate-200 dark:bg-slate-700 rounded-full h-2">
                    <div
                      className="bg-gradient-to-r from-green-500 to-emerald-500 h-2 rounded-full"
                      style={{ width: `${item.accuracy * 100}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Footer Info */}
      <div className="text-center text-xs text-slate-500 dark:text-slate-400">
        <p>Report generated: {report.date} • Test dataset: {report.test_data}</p>
        <p className="mt-1">Model: {report.model} • {report.samples.toLocaleString()} samples evaluated</p>
      </div>
    </div>
  )
}
