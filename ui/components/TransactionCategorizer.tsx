'use client'

import { useState } from 'react'
import { Send, Sparkles, Loader2, ThumbsUp, ThumbsDown, X } from 'lucide-react'
import { API_ENDPOINTS } from '@/lib/config'

interface CategorizedResult {
  original_text: string
  category: string
  subcategory?: string
  confidence: number
  method: string
  explanations: string[]
  requires_review: boolean
  record_id?: number
  ensemble_votes?: {
    rule: { category: string; confidence: number }
    ml: { category: string; confidence: number }
    llm: { category: string; confidence: number }
    agreement_count: number
    total_methods: number
  }
}

export default function TransactionCategorizer() {
  const [transaction, setTransaction] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<CategorizedResult | null>(null)
  const [showFeedback, setShowFeedback] = useState(false)
  const [feedbackCategory, setFeedbackCategory] = useState('')
  const [feedbackNotes, setFeedbackNotes] = useState('')
  const [submittingFeedback, setSubmittingFeedback] = useState(false)
  const [feedbackSubmitted, setFeedbackSubmitted] = useState(false)

  const handleCategorize = async () => {
    if (!transaction.trim()) return

    setLoading(true)
    setShowFeedback(false)
    setFeedbackSubmitted(false) // Reset feedback status for new categorization
    try {
      const response = await fetch(API_ENDPOINTS.categorize, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ text: transaction }),
      })

      const data = await response.json()
      setResult(data)
    } catch (error) {
      console.error('Error:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleAccept = async () => {
    if (!result) return

    setSubmittingFeedback(true)
    try {
      const response = await fetch(API_ENDPOINTS.feedback, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          transaction_text: result.original_text,
          predicted_category: result.category,
          correct_category: result.category, // Same as predicted = accepted
          notes: 'User accepted the classification'
        }),
      })

      if (response.ok) {
        setFeedbackSubmitted(true)
        setShowFeedback(false)
      }
    } catch (error) {
      console.error('Error submitting feedback:', error)
      alert('Failed to submit feedback')
    } finally {
      setSubmittingFeedback(false)
    }
  }

  const handleReject = () => {
    setShowFeedback(true)
    setFeedbackCategory('')
    setFeedbackNotes('')
  }

  const handleSubmitFeedback = async () => {
    if (!result) return

    setSubmittingFeedback(true)
    try {
      const response = await fetch(API_ENDPOINTS.feedback, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          transaction_text: result.original_text,
          predicted_category: result.category,
          correct_category: feedbackCategory || result.category,
          notes: feedbackNotes || 'Rejected classification'
        }),
      })

      if (response.ok) {
        setFeedbackSubmitted(true)
        setShowFeedback(false)
      }
    } catch (error) {
      console.error('Error submitting feedback:', error)
      alert('Failed to submit feedback')
    } finally {
      setSubmittingFeedback(false)
    }
  }

  const handleSkipFeedback = async () => {
    if (!result) return

    setSubmittingFeedback(true)
    try {
      const response = await fetch(API_ENDPOINTS.feedback, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          transaction_text: result.original_text,
          predicted_category: result.category,
          correct_category: result.category, // Keep same if user doesn't provide correction
          notes: 'User rejected but did not provide correct category'
        }),
      })

      if (response.ok) {
        setFeedbackSubmitted(true)
        setShowFeedback(false)
      }
    } catch (error) {
      console.error('Error submitting feedback:', error)
    } finally {
      setSubmittingFeedback(false)
    }
  }

  return (
    <div className="space-y-8">
      {/* Premium Input Section */}
      <div className="space-y-4">
        <label className="block text-sm font-bold text-slate-800 dark:text-slate-200 mb-3">
          Transaction Description
        </label>
        <div className="flex space-x-3">
          <div className="relative flex-1">
            <input
              type="text"
              value={transaction}
              onChange={(e) => setTransaction(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleCategorize()}
              placeholder="Enter transaction description..."
              className="w-full rounded-2xl border-2 border-slate-200 dark:border-slate-600 px-6 py-4 text-slate-900 dark:text-white bg-white/80 dark:bg-slate-700/80 backdrop-blur-sm focus:border-purple-500 dark:focus:border-purple-400 focus:ring-4 focus:ring-purple-500/20 outline-none transition-all duration-200 font-medium placeholder:text-slate-400"
            />
            <div className="absolute inset-0 rounded-2xl bg-gradient-to-r from-blue-500/5 to-purple-500/5 pointer-events-none"></div>
          </div>
          <button
            onClick={handleCategorize}
            disabled={loading || !transaction.trim()}
            className="relative inline-flex items-center px-8 py-4 border-2 border-transparent text-base font-bold rounded-2xl text-white bg-gradient-to-r from-blue-600 via-purple-600 to-purple-700 hover:from-blue-700 hover:via-purple-700 hover:to-purple-800 focus:outline-none focus:ring-4 focus:ring-purple-500/50 disabled:opacity-50 disabled:cursor-not-allowed transform hover:scale-105 transition-all duration-200 shadow-lg shadow-purple-500/25 hover:shadow-xl hover:shadow-purple-500/40"
          >
            {loading ? (
              <Loader2 className="h-6 w-6 animate-spin" />
            ) : (
              <>
                <Send className="h-5 w-5 mr-2" />
                Categorize
              </>
            )}
          </button>
        </div>
      </div>

      {/* Premium Results */}
      {result && (
        <div className="relative overflow-hidden rounded-2xl border-2 border-purple-200/50 dark:border-purple-800/50 animate-slide-up">
          <div className="absolute inset-0 bg-gradient-to-br from-blue-500/10 via-purple-500/10 to-pink-500/10"></div>
          <div className="relative glass dark:glass-dark p-8 space-y-6 backdrop-blur-xl">
            <div className="flex items-center justify-between">
              <h3 className="text-xl font-black gradient-text flex items-center">
                <Sparkles className="h-6 w-6 mr-3 text-purple-500 animate-pulse" />
                AI Classification Results
              </h3>
              {result.requires_review && (
                <span className="inline-flex items-center px-4 py-2 rounded-xl text-xs font-bold bg-gradient-to-r from-amber-100 to-orange-100 text-amber-800 dark:from-amber-900/40 dark:to-orange-900/40 dark:text-amber-200 border border-amber-300 dark:border-amber-700 shadow-lg">
                  ⚠️ Requires Review
                </span>
              )}
            </div>

            <div className="grid grid-cols-2 gap-6">
              <div className="bg-white/50 dark:bg-slate-800/50 rounded-2xl p-5 border border-slate-200 dark:border-slate-700 premium-shadow">
                <p className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-2">Category</p>
                <p className="text-3xl font-black bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">{result.category}</p>
                {result.subcategory && (
                  <p className="text-sm font-semibold text-slate-600 dark:text-slate-400 mt-1">{result.subcategory}</p>
                )}
              </div>
              <div className="bg-white/50 dark:bg-slate-800/50 rounded-2xl p-5 border border-slate-200 dark:border-slate-700 premium-shadow">
                <p className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-2">Confidence Score</p>
                <div className="space-y-3">
                  <p className="text-3xl font-black bg-gradient-to-r from-green-600 to-emerald-600 bg-clip-text text-transparent">
                    {(result.confidence * 100).toFixed(1)}%
                  </p>
                  <div className="relative w-full bg-slate-200 dark:bg-slate-700 rounded-full h-3 overflow-hidden">
                    <div
                      className={`absolute h-3 rounded-full transition-all duration-500 ${
                        result.confidence >= 0.8
                          ? 'bg-gradient-to-r from-green-500 to-emerald-500 shadow-lg shadow-green-500/50'
                          : result.confidence >= 0.6
                          ? 'bg-gradient-to-r from-amber-500 to-orange-500 shadow-lg shadow-amber-500/50'
                          : 'bg-gradient-to-r from-red-500 to-rose-500 shadow-lg shadow-red-500/50'
                      }`}
                      style={{ width: `${result.confidence * 100}%` }}
                    />
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-white/50 dark:bg-slate-800/50 rounded-2xl p-5 border border-slate-200 dark:border-slate-700">
              <p className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-3">Classification Method</p>
              <span className="inline-flex items-center px-4 py-2 rounded-xl text-sm font-bold bg-gradient-to-r from-blue-100 to-purple-100 text-blue-800 dark:from-blue-900/40 dark:to-purple-900/40 dark:text-blue-200 border border-blue-200 dark:border-blue-800 shadow-md">
                ⚡ {result.method}
              </span>
            </div>

            {/* Premium Explanations */}
            <div className="bg-white/50 dark:bg-slate-800/50 rounded-2xl p-5 border border-slate-200 dark:border-slate-700">
              <p className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-3">AI Reasoning</p>
              <ul className="space-y-2">
                {result.explanations.map((exp, idx) => (
                  <li key={idx} className="flex items-start group">
                    <span className="flex-shrink-0 w-6 h-6 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center text-white text-xs font-bold mr-3 shadow-md group-hover:scale-110 transition-transform">
                      {idx + 1}
                    </span>
                    <span className="text-sm font-medium text-slate-700 dark:text-slate-300 leading-relaxed">{exp}</span>
                  </li>
                ))}
              </ul>
            </div>

            {result.record_id && (
              <div className="flex items-center justify-center px-4 py-2 bg-gradient-to-r from-green-50 to-emerald-50 dark:from-green-900/20 dark:to-emerald-900/20 rounded-xl border border-green-200 dark:border-green-800">
                <p className="text-xs font-bold text-green-700 dark:text-green-300">
                  ✓ Record ID: {result.record_id} • Successfully stored in database
                </p>
              </div>
            )}

          {/* Premium Accept/Reject Buttons */}
          {result.confidence < 0.8 && !showFeedback && !feedbackSubmitted && (
            <div className="pt-6 border-t-2 border-dashed border-slate-300 dark:border-slate-600">
              <p className="text-sm font-bold text-slate-700 dark:text-slate-300 mb-4 text-center">
                How accurate is this classification?
              </p>
              <div className="grid grid-cols-2 gap-4">
                <button
                  onClick={handleAccept}
                  disabled={submittingFeedback}
                  className="group relative inline-flex items-center justify-center px-6 py-4 border-2 border-transparent text-base font-bold rounded-2xl text-white bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 focus:outline-none focus:ring-4 focus:ring-green-500/50 disabled:opacity-50 transform hover:scale-105 transition-all duration-200 shadow-lg shadow-green-500/25 hover:shadow-xl hover:shadow-green-500/40"
                >
                  {submittingFeedback ? (
                    <Loader2 className="h-5 w-5 animate-spin mr-2" />
                  ) : (
                    <ThumbsUp className="h-5 w-5 mr-2 group-hover:scale-110 transition-transform" />
                  )}
                  Accurate
                </button>
                <button
                  onClick={handleReject}
                  disabled={submittingFeedback}
                  className="group relative inline-flex items-center justify-center px-6 py-4 border-2 border-transparent text-base font-bold rounded-2xl text-white bg-gradient-to-r from-red-600 to-rose-600 hover:from-red-700 hover:to-rose-700 focus:outline-none focus:ring-4 focus:ring-red-500/50 disabled:opacity-50 transform hover:scale-105 transition-all duration-200 shadow-lg shadow-red-500/25 hover:shadow-xl hover:shadow-red-500/40"
                >
                  <ThumbsDown className="h-5 w-5 mr-2 group-hover:scale-110 transition-transform" />
                  Incorrect
                </button>
              </div>
            </div>
          )}

          {/* Premium Feedback Submitted Message */}
          {feedbackSubmitted && (
            <div className="pt-6 border-t-2 border-dashed border-slate-300 dark:border-slate-600">
              <div className="flex items-center justify-center px-6 py-4 bg-gradient-to-r from-green-50 to-emerald-50 dark:from-green-900/30 dark:to-emerald-900/30 rounded-2xl border-2 border-green-200 dark:border-green-800 shadow-lg">
                <ThumbsUp className="h-6 w-6 text-green-600 dark:text-green-400 mr-3 animate-bounce" />
                <p className="text-sm font-bold text-green-800 dark:text-green-300">
                  Feedback recorded! Your input helps train our AI system.
                </p>
              </div>
            </div>
          )}

          {/* Optional Feedback Form */}
          {showFeedback && (
            <div className="pt-4 border-t border-slate-200 dark:border-slate-600">
              <div className="flex items-center justify-between mb-3">
                <p className="text-sm font-medium text-slate-700 dark:text-slate-300">
                  Provide Correct Classification (Optional)
                </p>
                <button
                  onClick={() => setShowFeedback(false)}
                  className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>

              <div className="space-y-3">
                <div>
                  <label className="block text-xs text-slate-600 dark:text-slate-400 mb-1">
                    Correct Category (optional)
                  </label>
                  <input
                    type="text"
                    value={feedbackCategory}
                    onChange={(e) => setFeedbackCategory(e.target.value)}
                    placeholder="e.g., Food & Dining"
                    className="w-full rounded-lg border border-slate-300 dark:border-slate-600 px-3 py-2 text-sm text-slate-900 dark:text-white bg-white dark:bg-slate-700 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none"
                  />
                </div>

                <div>
                  <label className="block text-xs text-slate-600 dark:text-slate-400 mb-1">
                    Additional Notes (optional)
                  </label>
                  <textarea
                    value={feedbackNotes}
                    onChange={(e) => setFeedbackNotes(e.target.value)}
                    placeholder="Any additional context..."
                    rows={2}
                    className="w-full rounded-lg border border-slate-300 dark:border-slate-600 px-3 py-2 text-sm text-slate-900 dark:text-white bg-white dark:bg-slate-700 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none"
                  />
                </div>

                <div className="flex space-x-2">
                  <button
                    onClick={handleSubmitFeedback}
                    disabled={submittingFeedback}
                    className="flex-1 inline-flex items-center justify-center px-4 py-2 border border-transparent text-sm font-medium rounded-lg shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
                  >
                    {submittingFeedback ? (
                      <Loader2 className="h-4 w-4 animate-spin mr-2" />
                    ) : (
                      <Send className="h-4 w-4 mr-2" />
                    )}
                    Submit Feedback
                  </button>
                  <button
                    onClick={handleSkipFeedback}
                    className="px-4 py-2 border border-slate-300 dark:border-slate-600 text-sm font-medium rounded-lg text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-slate-500"
                  >
                    Skip
                  </button>
                </div>
              </div>
            </div>
          )}
          </div>
        </div>
      )}
    </div>
  )
}
