import { FileText, CheckCircle, AlertTriangle, BarChart3 } from 'lucide-react'

export default function ReportsViewer() {
  return (
    <div className="space-y-6">
      <div className="glass dark:glass-dark rounded-2xl p-6 premium-shadow premium-border">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-bold text-slate-800 dark:text-slate-100 flex items-center">
            <FileText className="w-6 h-6 mr-2 text-blue-500" />
            Fairness & Bias Evaluation
          </h2>
          <span className="text-xs font-medium px-3 py-1 rounded-full bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400 border border-green-200 dark:border-green-800">
            Pass
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-slate-50 dark:bg-slate-800/50 rounded-xl p-4 border border-slate-100 dark:border-slate-700">
            <div className="text-sm text-slate-500 dark:text-slate-400 mb-1">Overall Accuracy</div>
            <div className="text-2xl font-bold text-slate-900 dark:text-white">92.4%</div>
            <div className="text-xs text-green-600 mt-1 flex items-center">
              <CheckCircle className="w-3 h-3 mr-1" /> Target > 90% Met
            </div>
          </div>
          
          <div className="bg-slate-50 dark:bg-slate-800/50 rounded-xl p-4 border border-slate-100 dark:border-slate-700">
            <div className="text-sm text-slate-500 dark:text-slate-400 mb-1">Max Disparity</div>
            <div className="text-2xl font-bold text-slate-900 dark:text-white">1.2%</div>
            <div className="text-xs text-green-600 mt-1 flex items-center">
              <CheckCircle className="w-3 h-3 mr-1" /> Low Bias (&lt; 5%)
            </div>
          </div>

          <div className="bg-slate-50 dark:bg-slate-800/50 rounded-xl p-4 border border-slate-100 dark:border-slate-700">
            <div className="text-sm text-slate-500 dark:text-slate-400 mb-1">Minority Class Acc.</div>
            <div className="text-2xl font-bold text-slate-900 dark:text-white">88.7%</div>
            <div className="text-xs text-yellow-600 mt-1 flex items-center">
              <AlertTriangle className="w-3 h-3 mr-1" /> Monitoring
            </div>
          </div>
        </div>

        <h3 className="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-4 flex items-center">
          <BarChart3 className="w-4 h-4 mr-2" />
          Performance by Transaction Amount
        </h3>
        
        <div className="overflow-hidden rounded-xl border border-slate-200 dark:border-slate-700">
          <table className="min-w-full divide-y divide-slate-200 dark:divide-slate-700">
            <thead className="bg-slate-50 dark:bg-slate-800">
              <tr>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">Amount Range</th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">Sample Size</th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">Accuracy</th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">Status</th>
              </tr>
            </thead>
            <tbody className="bg-white dark:bg-slate-900 divide-y divide-slate-200 dark:divide-slate-800">
              <tr>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-900 dark:text-slate-100">Small (&lt;100)</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-500 dark:text-slate-400">4,250</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-900 dark:text-slate-100">91.8%</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-green-600"><span className="px-2 py-1 rounded-full bg-green-100 dark:bg-green-900/30 text-xs font-medium">Optimal</span></td>
              </tr>
              <tr>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-900 dark:text-slate-100">Medium (100-1000)</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-500 dark:text-slate-400">8,120</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-900 dark:text-slate-100">93.0%</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-green-600"><span className="px-2 py-1 rounded-full bg-green-100 dark:bg-green-900/30 text-xs font-medium">Optimal</span></td>
              </tr>
              <tr>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-900 dark:text-slate-100">Large (&gt;1000)</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-500 dark:text-slate-400">1,890</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-900 dark:text-slate-100">92.5%</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-green-600"><span className="px-2 py-1 rounded-full bg-green-100 dark:bg-green-900/30 text-xs font-medium">Optimal</span></td>
              </tr>
            </tbody>
          </table>
        </div>
        
        <div className="mt-6 text-xs text-slate-400 dark:text-slate-500 text-center">
          Report generated automatically on model training. Metrics based on holdout test set.
        </div>
      </div>
    </div>
  )
}
