'use client'

import { useState } from 'react'
import { Send, CheckCircle } from 'lucide-react'
import { API_ENDPOINTS } from '@/lib/config'

// Available categories from taxonomy
const CATEGORIES = [
  'ATM/Cash',
  'Automotive',
  'Bills',
  'Charity & Donations',
  'Education',
  'Electronics & Technology',
  'Entertainment',
  'Fees & Charges',
  'Food & Dining',
  'Fraud & Security',
  'Fuel',
  'Gifts & Special Occasions',
  'Groceries',
  'Health',
  'Home Improvement',
  'Income/Salary',
  'Insurance',
  'Investments',
  'Kids & Family',
  'Other',
  'Personal Care',
  'Pets',
  'Professional Services',
  'Rent',
  'Shopping',
  'Subscriptions & Memberships',
  'Taxes & Government',
  'Transfers/UPI',
  'Transport',
  'Travel',
]

export default function FeedbackForm() {
  const [formData, setFormData] = useState({
    transaction_text: '',
    predicted_category: '',
    correct_category: '',
    notes: ''
  })
  const [submitted, setSubmitted] = useState(false)
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)

    try {
      const response = await fetch(API_ENDPOINTS.feedback, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      })

      if (response.ok) {
        setSubmitted(true)
        setTimeout(() => {
          setSubmitted(false)
          setFormData({
            transaction_text: '',
            predicted_category: '',
            correct_category: '',
            notes: ''
          })
        }, 3000)
      }
    } catch (error) {
      console.error('Error:', error)
    } finally {
      setLoading(false)
    }
  }

  if (submitted) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <CheckCircle className="h-16 w-16 text-green-500 mb-4" />
        <h3 className="text-2xl font-bold text-slate-900 dark:text-white mb-2">
          Thank You!
        </h3>
        <p className="text-slate-600 dark:text-slate-400">
          Your feedback has been submitted and will help improve the system.
        </p>
      </div>
    )
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-slate-700 dark:to-slate-800 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">
          Submit Feedback
        </h3>
        <p className="text-sm text-slate-600 dark:text-slate-400 mb-6">
          Help us improve by reporting incorrect categorizations. Your feedback trains the system!
        </p>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
              Transaction Text
            </label>
            <input
              type="text"
              value={formData.transaction_text}
              onChange={(e) => setFormData({ ...formData, transaction_text: e.target.value })}
              required
              placeholder="e.g., STARBUCKS COFFEE"
              className="w-full rounded-lg border border-slate-300 dark:border-slate-600 px-4 py-2 text-slate-900 dark:text-white bg-white dark:bg-slate-700"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                Predicted Category
              </label>
              <select
                value={formData.predicted_category}
                onChange={(e) => setFormData({ ...formData, predicted_category: e.target.value })}
                required
                className="w-full rounded-lg border border-slate-300 dark:border-slate-600 px-4 py-2 text-slate-900 dark:text-white bg-white dark:bg-slate-700"
              >
                <option value="">Select category...</option>
                {CATEGORIES.map((category) => (
                  <option key={category} value={category}>
                    {category}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                Correct Category
              </label>
              <select
                value={formData.correct_category}
                onChange={(e) => setFormData({ ...formData, correct_category: e.target.value })}
                required
                className="w-full rounded-lg border border-slate-300 dark:border-slate-600 px-4 py-2 text-slate-900 dark:text-white bg-white dark:bg-slate-700"
              >
                <option value="">Select category...</option>
                {CATEGORIES.map((category) => (
                  <option key={category} value={category}>
                    {category}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
              Notes (Optional)
            </label>
            <textarea
              value={formData.notes}
              onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
              rows={3}
              placeholder="Additional context about why this was miscategorized..."
              className="w-full rounded-lg border border-slate-300 dark:border-slate-600 px-4 py-2 text-slate-900 dark:text-white bg-white dark:bg-slate-700"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full inline-flex items-center justify-center px-6 py-3 border border-transparent text-base font-medium rounded-lg shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
          >
            <Send className="h-5 w-5 mr-2" />
            Submit Feedback
          </button>
        </div>
      </div>
    </form>
  )
}
