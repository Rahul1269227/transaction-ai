'use client'

import { useState } from 'react'
import { Send, Sparkles, Loader2, ThumbsUp, ThumbsDown, X } from 'lucide-react'

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

export default function CategorizationDemo() {
  const [transaction, setTransaction] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<CategorizedResult | null>(null)
  const [showFeedback, setShowFeedback] = useState(false)
  const [feedbackCategory, setFeedbackCategory] = useState('')
  const [feedbackNotes, setFeedbackNotes] = useState('')
  const [submittingFeedback, setSubmittingFeedback] = useState(false)
  const [feedbackSubmitted, setFeedbackSubmitted] = useState(false)

  const examples = [
    'STARBUCKS COFFEE #12345',
    'NETFLIX SUBSCRIPTION',
    'UBER RIDE TO AIRPORT',
    'AMAZON PURCHASE ELECTRONICS',
    'GROCERY STORE BIG BAZAAR'
  ]

  const handleCategorize = async () => {
    if (!transaction.trim()) return

    setLoading(true)
    setShowFeedback(false)
    setFeedbackSubmitted(false) // Reset feedback status for new categorization
    try {
      const response = await fetch('/api/categorize', {
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
      const response = await fetch('http://localhost:8000/feedback', {
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
      const response = await fetch('http://localhost:8000/feedback', {
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
      const response = await fetch('http://localhost:8000/feedback', {
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
    <div className="space-y-6">
      {/* Input Section */}
      <div>
        <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
          Transaction Description
        </label>
        <div className="flex space-x-3">
          <input
            type="text"
            value={transaction}
            onChange={(e) => setTransaction(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleCategorize()}
            placeholder="Enter transaction description..."
            className="flex-1 rounded-lg border border-slate-300 dark:border-slate-600 px-4 py-3 text-slate-900 dark:text-white bg-white dark:bg-slate-700 focus:border-blue-500 focus:ring-2 focus:ring-blue-500 outline-none"
          />
          <button
            onClick={handleCategorize}
            disabled={loading || !transaction.trim()}
            className="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-lg shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? (
              <Loader2 className="h-5 w-5 animate-spin" />
            ) : (
              <>
                <Send className="h-5 w-5 mr-2" />
                Categorize
              </>
            )}
          </button>
        </div>

        {/* Examples */}
        <div className="mt-3 flex flex-wrap gap-2">
          <span className="text-xs text-slate-500 dark:text-slate-400">Try:</span>
          {examples.map((ex, idx) => (
            <button
              key={idx}
              onClick={() => setTransaction(ex)}
              className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-600"
            >
              {ex}
            </button>
          ))}
        </div>
      </div>

      {/* Results */}
      {result && (
        <div className="bg-gradient-to-br from-blue-50 to-purple-50 dark:from-slate-700 dark:to-slate-800 rounded-lg p-6 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-slate-900 dark:text-white flex items-center">
              <Sparkles className="h-5 w-5 mr-2 text-purple-500" />
              Categorization Result
            </h3>
            {result.requires_review && (
              <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-200">
                Requires Review
              </span>
            )}
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-slate-600 dark:text-slate-400">Category</p>
              <p className="text-2xl font-bold text-slate-900 dark:text-white">{result.category}</p>
              {result.subcategory && (
                <p className="text-sm text-slate-600 dark:text-slate-400">{result.subcategory}</p>
              )}
            </div>
            <div>
              <p className="text-sm text-slate-600 dark:text-slate-400">Confidence</p>
              <div className="flex items-baseline space-x-2">
                <p className="text-2xl font-bold text-slate-900 dark:text-white">
                  {(result.confidence * 100).toFixed(1)}%
                </p>
                <div className="flex-1 bg-slate-200 dark:bg-slate-600 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full ${
                      result.confidence >= 0.8
                        ? 'bg-green-500'
                        : result.confidence >= 0.6
                        ? 'bg-amber-500'
                        : 'bg-red-500'
                    }`}
                    style={{ width: `${result.confidence * 100}%` }}
                  />
                </div>
              </div>
            </div>
          </div>

          <div>
            <p className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">Method</p>
            <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200">
              {result.method}
            </span>
          </div>

          {/* Explanations */}
          <div>
            <p className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">Explanations</p>
            <ul className="space-y-1">
              {result.explanations.map((exp, idx) => (
                <li key={idx} className="text-sm text-slate-600 dark:text-slate-400 flex items-start">
                  <span className="text-purple-500 mr-2">•</span>
                  {exp}
                </li>
              ))}
            </ul>
          </div>

          {result.record_id && (
            <div className="text-xs text-slate-500 dark:text-slate-400">
              Record ID: {result.record_id} | Stored in database ✓
            </div>
          )}

          {/* Accept/Reject Buttons - Show when confidence is low and feedback not yet submitted */}
          {result.confidence < 0.8 && !showFeedback && !feedbackSubmitted && (
            <div className="pt-4 border-t border-slate-200 dark:border-slate-600">
              <p className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-3">
                Is this classification correct?
              </p>
              <div className="flex space-x-3">
                <button
                  onClick={handleAccept}
                  disabled={submittingFeedback}
                  className="flex-1 inline-flex items-center justify-center px-4 py-2 border border-transparent text-sm font-medium rounded-lg shadow-sm text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:opacity-50"
                >
                  {submittingFeedback ? (
                    <Loader2 className="h-4 w-4 animate-spin mr-2" />
                  ) : (
                    <ThumbsUp className="h-4 w-4 mr-2" />
                  )}
                  Accept
                </button>
                <button
                  onClick={handleReject}
                  disabled={submittingFeedback}
                  className="flex-1 inline-flex items-center justify-center px-4 py-2 border border-transparent text-sm font-medium rounded-lg shadow-sm text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:opacity-50"
                >
                  <ThumbsDown className="h-4 w-4 mr-2" />
                  Reject
                </button>
              </div>
            </div>
          )}

          {/* Feedback Submitted Message */}
          {feedbackSubmitted && (
            <div className="pt-4 border-t border-slate-200 dark:border-slate-600">
              <div className="flex items-center justify-center px-4 py-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
                <ThumbsUp className="h-5 w-5 text-green-600 dark:text-green-400 mr-2" />
                <p className="text-sm font-medium text-green-800 dark:text-green-300">
                  Thank you! Your feedback has been recorded and will help improve the system.
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
      )}
    </div>
  )
}
