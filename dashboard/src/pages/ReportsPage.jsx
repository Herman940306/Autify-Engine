import { useEffect, useState } from 'react'
import { fetchAnalytics } from '../api'
import { KPIBarChart, TrendLineChart } from '../components/Charts'

/**
 * ReportsPage — detailed analysis results and historical KPI charts.
 */
export default function ReportsPage() {
  const [analytics, setAnalytics] = useState([])
  useEffect(() => { fetchAnalytics().then(setAnalytics).catch(() => {}) }, [])

  // Merge all KPI summaries
  const merged = analytics.reduce((acc, a) => {
    if (a.kpi_summary) {
      Object.entries(a.kpi_summary).forEach(([k, v]) => {
        acc[k] = (acc[k] || 0) + v
      })
    }
    return acc
  }, {})

  const trend = analytics
    .filter((a) => a.kpi_summary)
    .map((a) => ({
      label: a.timestamp ? new Date(a.timestamp).toLocaleDateString() : '?',
      value: Object.values(a.kpi_summary).reduce((s, v) => s + v, 0),
    }))
    .reverse()

  // Unique anomalies
  const anomalies = analytics.flatMap((a) =>
    (a.anomalies || []).map((an) => ({ ...an, result_id: a.result_id })),
  )

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Reports</h1>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
          <h3 className="text-sm font-semibold mb-3">Cumulative KPIs</h3>
          <KPIBarChart kpis={merged} />
        </div>
        <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
          <h3 className="text-sm font-semibold mb-3">Trend Over Time</h3>
          <TrendLineChart data={trend} />
        </div>
      </div>

      {/* Anomaly table */}
      <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
        <h3 className="text-sm font-semibold mb-3">Detected Anomalies</h3>
        {anomalies.length === 0 ? (
          <p className="text-gray-400 text-sm">No anomalies detected.</p>
        ) : (
          <table className="min-w-full text-sm">
            <thead>
              <tr className="text-left text-xs uppercase text-gray-500">
                <th className="px-3 py-2">Column</th>
                <th className="px-3 py-2">Value</th>
                <th className="px-3 py-2">Reason</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {anomalies.map((an, i) => (
                <tr key={i} className="bg-red-50">
                  <td className="px-3 py-2 font-mono text-xs">{an.column}</td>
                  <td className="px-3 py-2">{an.value}</td>
                  <td className="px-3 py-2 text-gray-600">{an.reason}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
