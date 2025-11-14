'use client'

import { useState } from 'react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell } from 'recharts'
import { Vote, Send, Loader2 } from 'lucide-react'

export default function EnsembleVoting() {
  const [transaction, setTransaction] = useState('STARBUCKS COFFEE')
  const [loading, setLoading] = useState(false)
  const [votingData, setVotingData] = useState<any>(null)

  const handleAnalyze = async () => {
    setLoading(true)
    try {
      const response = await fetch('/api/categorize', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ text: transaction }),
      })

      const data = await response.json()
      setVotingData(data.ensemble_votes)
    } catch (error) {
      console.error('Error:', error)
    } finally {
      setLoading(false)
    }
  }

  const chartData = votingData ? [
    {
      name: 'Rule Engine',
      confidence: (votingData.rule?.confidence * 100) || 0,
      category: votingData.rule?.category || 'N/A'
    },
    {
      name: 'ML Classifier',
      confidence: (votingData.ml?.confidence * 100) || 0,
      category: votingData.ml?.category || 'N/A'
    },
    {
      name: 'LLM Reasoning',
      confidence: (votingData.llm?.confidence * 100) || 0,
      category: votingData.llm?.category || 'N/A'
    }
  ] : []

  const COLORS = ['#3b82f6', '#8b5cf6', '#ec4899']

  return (
    <div className="space-y-6">
      {/* Input */}
      <div className="flex space-x-3">
        <input
          type="text"
          value={transaction}
          onChange={(e) => setTransaction(e.target.value)}
          placeholder="Enter transaction..."
          className="flex-1 rounded-lg border border-slate-300 dark:border-slate-600 px-4 py-3 text-slate-900 dark:text-white bg-white dark:bg-slate-700"
        />
        <button
          onClick={handleAnalyze}
          disabled={loading}
          className="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-lg shadow-sm text-white bg-purple-600 hover:bg-purple-700 disabled:opacity-50"
        >
          {loading ? <Loader2 className="h-5 w-5 animate-spin" /> : <Send className="h-5 w-5 mr-2" />}
          Analyze
        </button>
      </div>

      {votingData && (
        <div className="space-y-6">
          {/* Voting Summary */}
          <div className="bg-gradient-to-br from-purple-50 to-pink-50 dark:from-slate-700 dark:to-slate-800 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-slate-900 dark:text-white flex items-center mb-4">
              <Vote className="h-5 w-5 mr-2 text-purple-500" />
              Ensemble Voting Breakdown
            </h3>

            <div className="grid grid-cols-3 gap-4 mb-6">
              {chartData.map((method, idx) => (
                <div key={idx} className="bg-white dark:bg-slate-900 rounded-lg p-4">
                  <p className="text-xs text-slate-600 dark:text-slate-400 mb-1">{method.name}</p>
                  <p className="text-sm font-semibold text-slate-900 dark:text-white mb-1">{method.category}</p>
                  <div className="flex items-center">
                    <div className="flex-1 bg-slate-200 dark:bg-slate-600 rounded-full h-2 mr-2">
                      <div
                        className="h-2 rounded-full"
                        style={{ width: `${method.confidence}%`, backgroundColor: COLORS[idx] }}
                      />
                    </div>
                    <span className="text-xs font-medium text-slate-600 dark:text-slate-400">
                      {method.confidence.toFixed(1)}%
                    </span>
                  </div>
                </div>
              ))}
            </div>

            {/* Chart */}
            <div className="bg-white dark:bg-slate-900 rounded-lg p-4">
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip
                    content={({ active, payload }) => {
                      if (active && payload && payload.length) {
                        return (
                          <div className="bg-white dark:bg-slate-800 p-3 rounded-lg shadow-lg border border-slate-200 dark:border-slate-600">
                            <p className="font-semibold text-slate-900 dark:text-white">{payload[0].payload.name}</p>
                            <p className="text-sm text-slate-600 dark:text-slate-400">Category: {payload[0].payload.category}</p>
                            <p className="text-sm font-medium" style={{ color: payload[0].color }}>
                              Confidence: {payload[0].value}%
                            </p>
                          </div>
                        )
                      }
                      return null
                    }}
                  />
                  <Bar dataKey="confidence" radius={[8, 8, 0, 0]}>
                    {chartData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* Agreement Info */}
            <div className="mt-4 flex items-center justify-between p-4 bg-white dark:bg-slate-900 rounded-lg">
              <div>
                <p className="text-sm text-slate-600 dark:text-slate-400">Agreement</p>
                <p className="text-2xl font-bold text-slate-900 dark:text-white">
                  {votingData.agreement_count} / {votingData.total_methods}
                </p>
              </div>
              <div className="text-right">
                <p className="text-sm text-slate-600 dark:text-slate-400">Agreement Rate</p>
                <p className="text-2xl font-bold text-slate-900 dark:text-white">
                  {((votingData.agreement_count / votingData.total_methods) * 100).toFixed(0)}%
                </p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
