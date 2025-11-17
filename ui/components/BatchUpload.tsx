'use client'

import { useState, useRef } from 'react'
import { Upload, FileText, Loader2, Download, CheckCircle2, XCircle, AlertCircle } from 'lucide-react'
import { API_ENDPOINTS } from '@/lib/config'

interface BatchResult {
  transaction: string
  category: string
  subcategory?: string
  confidence: number
  method: string
  status: 'success' | 'error'
  error_message?: string
}

export default function BatchUpload() {
  const [transactions, setTransactions] = useState<string>('')
  const [file, setFile] = useState<File | null>(null)
  const [loading, setLoading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [results, setResults] = useState<BatchResult[]>([])
  const [uploadMethod, setUploadMethod] = useState<'paste' | 'file'>('paste')
  const [detectedFormat, setDetectedFormat] = useState<'txt' | 'csv' | 'json' | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const parseTransactions = (content: string, fileName?: string): string[] => {
    const trimmed = content.trim()

    // Auto-detect format from file extension or content
    let format: 'txt' | 'csv' | 'json' = 'txt'

    if (fileName) {
      if (fileName.endsWith('.json')) format = 'json'
      else if (fileName.endsWith('.csv')) format = 'csv'
      else format = 'txt'
    } else {
      // Auto-detect from content
      if (trimmed.startsWith('[') || trimmed.startsWith('{')) format = 'json'
      else if (trimmed.includes(',') && trimmed.split('\n').length > 1) format = 'csv'
      else format = 'txt'
    }

    setDetectedFormat(format)

    try {
      switch (format) {
        case 'json':
          const jsonData = JSON.parse(trimmed)
          // Handle different JSON structures
          if (Array.isArray(jsonData)) {
            // Array of strings or objects
            return jsonData.map(item => {
              if (typeof item === 'string') return item
              if (typeof item === 'object' && item !== null) {
                // Look for common transaction text fields
                return item.text || item.transaction || item.description || item.name || JSON.stringify(item)
              }
              return String(item)
            }).filter(t => t.length > 0)
          } else if (typeof jsonData === 'object' && jsonData !== null) {
            // Single object or object with transactions array
            if (jsonData.transactions && Array.isArray(jsonData.transactions)) {
              return jsonData.transactions.map((t: any) =>
                typeof t === 'string' ? t : (t.text || t.transaction || t.description || JSON.stringify(t))
              ).filter((t: string) => t.length > 0)
            }
            // Single transaction object
            return [jsonData.text || jsonData.transaction || jsonData.description || JSON.stringify(jsonData)]
          }
          return []

        case 'csv':
          const lines = trimmed.split('\n')
          const transactions: string[] = []

          for (let i = 0; i < lines.length; i++) {
            const line = lines[i].trim()
            if (!line) continue

            // Skip header row if it looks like a header
            if (i === 0 && (
              line.toLowerCase().includes('transaction') ||
              line.toLowerCase().includes('description') ||
              line.toLowerCase().includes('text')
            )) {
              continue
            }

            // Parse CSV line (handle quoted fields)
            const fields = line.match(/(".*?"|[^",\s]+)(?=\s*,|\s*$)/g) || [line]
            const firstField = fields[0].replace(/^"|"$/g, '').trim()

            if (firstField.length > 0) {
              transactions.push(firstField)
            }
          }
          return transactions

        case 'txt':
        default:
          return trimmed
            .split('\n')
            .map(t => t.trim())
            .filter(t => t.length > 0)
      }
    } catch (error) {
      console.error('Error parsing transactions:', error)
      // Fallback to line-by-line parsing
      return trimmed
        .split('\n')
        .map(t => t.trim())
        .filter(t => t.length > 0)
    }
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0]
    if (selectedFile) {
      setFile(selectedFile)
      // Read file content
      const reader = new FileReader()
      reader.onload = (event) => {
        const content = event.target?.result as string
        setTransactions(content)
        // Parse to show preview
        const parsed = parseTransactions(content, selectedFile.name)
        console.log(`Detected format: ${detectedFormat}, Parsed ${parsed.length} transactions`)
      }
      reader.readAsText(selectedFile)
    }
  }

  const handleBatchCategorize = async () => {
    if (!transactions.trim()) {
      alert('Please enter or upload transactions')
      return
    }

    setLoading(true)
    setProgress(0)
    setResults([])

    try {
      // Parse transactions using smart parser
      const transactionList = parseTransactions(transactions, file?.name)

      if (transactionList.length === 0) {
        alert('No valid transactions found. Please check your input format.')
        setLoading(false)
        return
      }

      console.log(`Processing ${transactionList.length} transactions in ${detectedFormat} format`)

      // Call batch API with 5-minute timeout
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 5 * 60 * 1000) // 5 minutes

      const response = await fetch(API_ENDPOINTS.batchCategorize, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ transactions: transactionList }),
        signal: controller.signal,
      })

      clearTimeout(timeoutId)

      if (!response.ok) {
        throw new Error(`Server error: ${response.status}`)
      }

      const data = await response.json()
      setResults(data.results || [])
      setProgress(100)
    } catch (error: any) {
      if (error.name === 'AbortError') {
        alert('Request timed out after 5 minutes. Please try with fewer transactions.')
      } else {
        console.error('Error:', error)
        alert('Failed to process batch: ' + error.message)
      }
    } finally {
      setLoading(false)
    }
  }

  const handleDownloadResults = () => {
    if (results.length === 0) return

    // Create CSV content
    const headers = ['Transaction', 'Category', 'Subcategory', 'Confidence', 'Method', 'Status', 'Error']
    const rows = results.map(r => [
      r.transaction,
      r.category,
      r.subcategory || '',
      (r.confidence * 100).toFixed(1) + '%',
      r.method,
      r.status,
      r.error_message || ''
    ])

    const csvContent = [
      headers.join(','),
      ...rows.map(row => row.map(cell => `"${cell}"`).join(','))
    ].join('\n')

    // Download file
    const blob = new Blob([csvContent], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `batch_categorization_${Date.now()}.csv`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  const successCount = results.filter(r => r.status === 'success').length
  const errorCount = results.filter(r => r.status === 'error').length

  return (
    <div className="space-y-8">
      {/* Upload Method Selector */}
      <div className="flex items-center justify-center space-x-4">
        <button
          onClick={() => setUploadMethod('paste')}
          className={`px-6 py-3 rounded-xl font-bold text-sm transition-all duration-200 ${
            uploadMethod === 'paste'
              ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-lg'
              : 'bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-600'
          }`}
        >
          <FileText className="inline h-4 w-4 mr-2" />
          Paste Text
        </button>
        <button
          onClick={() => setUploadMethod('file')}
          className={`px-6 py-3 rounded-xl font-bold text-sm transition-all duration-200 ${
            uploadMethod === 'file'
              ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-lg'
              : 'bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-600'
          }`}
        >
          <Upload className="inline h-4 w-4 mr-2" />
          Upload File
        </button>
      </div>

      {/* Input Section */}
      <div className="space-y-4">
        {uploadMethod === 'paste' ? (
          <div>
            <div className="flex items-center justify-between mb-3">
              <label className="block text-sm font-bold text-slate-800 dark:text-slate-200">
                Paste Transactions (TXT, CSV, or JSON)
              </label>
              {transactions && detectedFormat && (
                <span className="inline-flex items-center px-3 py-1 rounded-lg text-xs font-bold bg-gradient-to-r from-green-100 to-emerald-100 dark:from-green-900/40 dark:to-emerald-900/40 text-green-700 dark:text-green-300 border border-green-200 dark:border-green-800">
                  ✓ Detected: {detectedFormat.toUpperCase()}
                </span>
              )}
            </div>
            <textarea
              value={transactions}
              onChange={(e) => {
                setTransactions(e.target.value)
                // Auto-detect format on paste
                if (e.target.value.trim()) {
                  parseTransactions(e.target.value)
                }
              }}
              placeholder={`TXT Format:\nSTARBUCKS COFFEE #12345\nNETFLIX SUBSCRIPTION\n\nCSV Format:\ntransaction,amount,date\n"STARBUCKS",12.50,2024-01-01\n\nJSON Format:\n["STARBUCKS","NETFLIX"]\nor\n{"transactions": ["STARBUCKS","NETFLIX"]}`}
              rows={12}
              className="w-full rounded-2xl border-2 border-slate-200 dark:border-slate-600 px-6 py-4 text-slate-900 dark:text-white bg-white/80 dark:bg-slate-700/80 backdrop-blur-sm focus:border-purple-500 dark:focus:border-purple-400 focus:ring-4 focus:ring-purple-500/20 outline-none transition-all duration-200 font-mono text-sm placeholder:text-slate-400"
            />
            <div className="mt-2 flex items-center space-x-4 text-xs text-slate-500 dark:text-slate-400">
              <span>💡 <strong>Tip:</strong> Paste TXT (one per line), CSV (first column), or JSON array</span>
            </div>
          </div>
        ) : (
          <div>
            <label className="block text-sm font-bold text-slate-800 dark:text-slate-200 mb-3">
              Upload File (TXT, CSV, JSON)
            </label>
            <div
              onClick={() => fileInputRef.current?.click()}
              className="relative cursor-pointer rounded-2xl border-2 border-dashed border-slate-300 dark:border-slate-600 p-12 text-center hover:border-purple-500 dark:hover:border-purple-400 transition-all duration-200 bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-800 dark:to-slate-900 group"
            >
              <Upload className="mx-auto h-12 w-12 text-slate-400 group-hover:text-purple-500 transition-colors mb-4" />
              <p className="text-sm font-bold text-slate-700 dark:text-slate-300">
                {file ? (
                  <span className="flex items-center justify-center space-x-2">
                    <span>{file.name}</span>
                    {detectedFormat && (
                      <span className="inline-flex items-center px-2 py-1 rounded-lg text-xs font-bold bg-purple-100 dark:bg-purple-900/40 text-purple-700 dark:text-purple-300 border border-purple-200 dark:border-purple-800">
                        {detectedFormat.toUpperCase()}
                      </span>
                    )}
                  </span>
                ) : (
                  'Click to browse or drag and drop'
                )}
              </p>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-2">
                Supports TXT, CSV, or JSON files
              </p>
              <div className="mt-3 flex items-center justify-center space-x-2 text-xs text-slate-400">
                <span>📄 TXT: One per line</span>
                <span>•</span>
                <span>📊 CSV: First column</span>
                <span>•</span>
                <span>🔧 JSON: Array or object</span>
              </div>
              <input
                ref={fileInputRef}
                type="file"
                accept=".txt,.csv,.json"
                onChange={handleFileChange}
                className="hidden"
              />
            </div>
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex space-x-3">
          <button
            onClick={handleBatchCategorize}
            disabled={loading || !transactions.trim()}
            className="flex-1 inline-flex items-center justify-center px-8 py-4 border-2 border-transparent text-base font-bold rounded-2xl text-white bg-gradient-to-r from-blue-600 via-purple-600 to-purple-700 hover:from-blue-700 hover:via-purple-700 hover:to-purple-800 focus:outline-none focus:ring-4 focus:ring-purple-500/50 disabled:opacity-50 disabled:cursor-not-allowed transform hover:scale-105 transition-all duration-200 shadow-lg shadow-purple-500/25 hover:shadow-xl hover:shadow-purple-500/40"
          >
            {loading ? (
              <>
                <Loader2 className="h-6 w-6 animate-spin mr-2" />
                Processing...
              </>
            ) : (
              <>
                <Upload className="h-5 w-5 mr-2" />
                Categorize Batch
              </>
            )}
          </button>
          {results.length > 0 && (
            <button
              onClick={handleDownloadResults}
              className="inline-flex items-center px-8 py-4 border-2 border-slate-300 dark:border-slate-600 text-base font-bold rounded-2xl text-slate-700 dark:text-slate-300 bg-white dark:bg-slate-800 hover:bg-slate-50 dark:hover:bg-slate-700 focus:outline-none focus:ring-4 focus:ring-slate-500/50 transform hover:scale-105 transition-all duration-200 shadow-lg"
            >
              <Download className="h-5 w-5 mr-2" />
              Download CSV
            </button>
          )}
        </div>
      </div>

      {/* Progress */}
      {loading && (
        <div className="space-y-3">
          <div className="flex items-center justify-between text-sm font-bold">
            <span className="text-slate-700 dark:text-slate-300">Processing transactions...</span>
            <span className="text-purple-600 dark:text-purple-400">{progress}%</span>
          </div>
          <div className="relative w-full bg-slate-200 dark:bg-slate-700 rounded-full h-3 overflow-hidden">
            <div
              className="absolute h-3 rounded-full bg-gradient-to-r from-blue-500 to-purple-500 shadow-lg shadow-purple-500/50 transition-all duration-300"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      )}

      {/* Results Summary */}
      {results.length > 0 && (
        <div className="grid grid-cols-3 gap-4">
          <div className="bg-white/50 dark:bg-slate-800/50 rounded-2xl p-5 border border-slate-200 dark:border-slate-700 premium-shadow">
            <p className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-2">Total</p>
            <p className="text-3xl font-black bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
              {results.length}
            </p>
          </div>
          <div className="bg-white/50 dark:bg-slate-800/50 rounded-2xl p-5 border border-slate-200 dark:border-slate-700 premium-shadow">
            <p className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-2">Successful</p>
            <p className="text-3xl font-black bg-gradient-to-r from-green-600 to-emerald-600 bg-clip-text text-transparent">
              {successCount}
            </p>
          </div>
          <div className="bg-white/50 dark:bg-slate-800/50 rounded-2xl p-5 border border-slate-200 dark:border-slate-700 premium-shadow">
            <p className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-2">Errors</p>
            <p className="text-3xl font-black bg-gradient-to-r from-red-600 to-rose-600 bg-clip-text text-transparent">
              {errorCount}
            </p>
          </div>
        </div>
      )}

      {/* Results Table */}
      {results.length > 0 && (
        <div className="relative overflow-hidden rounded-2xl border-2 border-purple-200/50 dark:border-purple-800/50">
          <div className="absolute inset-0 bg-gradient-to-br from-blue-500/10 via-purple-500/10 to-pink-500/10"></div>
          <div className="relative glass dark:glass-dark backdrop-blur-xl overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gradient-to-r from-slate-50/50 to-slate-100/50 dark:from-slate-800/50 dark:to-slate-900/50 border-b-2 border-slate-200 dark:border-slate-700">
                <tr>
                  <th className="px-6 py-4 text-left text-xs font-bold text-slate-600 dark:text-slate-300 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-bold text-slate-600 dark:text-slate-300 uppercase tracking-wider">
                    Transaction
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-bold text-slate-600 dark:text-slate-300 uppercase tracking-wider">
                    Category
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-bold text-slate-600 dark:text-slate-300 uppercase tracking-wider">
                    Confidence
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-bold text-slate-600 dark:text-slate-300 uppercase tracking-wider">
                    Method
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 dark:divide-slate-700">
                {results.map((result, idx) => (
                  <tr
                    key={idx}
                    className="hover:bg-slate-50/50 dark:hover:bg-slate-800/50 transition-colors"
                  >
                    <td className="px-6 py-4 whitespace-nowrap">
                      {result.status === 'success' ? (
                        <CheckCircle2 className="h-5 w-5 text-green-500" />
                      ) : (
                        <XCircle className="h-5 w-5 text-red-500" />
                      )}
                    </td>
                    <td className="px-6 py-4 font-medium text-slate-900 dark:text-white max-w-xs truncate">
                      {result.transaction}
                    </td>
                    <td className="px-6 py-4">
                      <span className="inline-flex items-center px-3 py-1 rounded-xl text-xs font-bold bg-gradient-to-r from-blue-100 to-purple-100 text-blue-800 dark:from-blue-900/40 dark:to-purple-900/40 dark:text-blue-200 border border-blue-200 dark:border-blue-800">
                        {result.category}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center space-x-2">
                        <span className="text-sm font-bold text-slate-700 dark:text-slate-300">
                          {(result.confidence * 100).toFixed(1)}%
                        </span>
                        <div className="w-16 bg-slate-200 dark:bg-slate-700 rounded-full h-2">
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
                    </td>
                    <td className="px-6 py-4 text-xs font-medium text-slate-600 dark:text-slate-400">
                      {result.method}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
