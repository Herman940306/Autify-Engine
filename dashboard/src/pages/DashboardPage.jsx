import { useEffect, useState } from 'react'
import { Users, FileInput, FileText, AlertTriangle } from 'lucide-react'
import KPICard from '../components/KPICard'
import { KPIBarChart, TrendLineChart, DraftStatusPie } from '../components/Charts'
import { fetchSummary, fetchAnalytics } from '../api'

/**
 * DashboardPage — main KPI overview with interactive charts.
 */
export default function DashboardPage() {
  const [summary, setSummary] = useState(null)
  const [analytics, setAnalytics] = useState([])

  useEffect(() => {
    fetchSummary().then(setSummary).catch(() => {})
    fetchAnalytics().then(setAnalytics).catch(() => {})
  }, [])

  // Consolidate all KPI summaries into one for the bar chart
  const mergedKpis = analytics.reduce((acc, a) => {
    if (a.kpi_summary) {
      Object.entries(a.kpi_summary).forEach(([k, v]) => {
        acc[k] = (acc[k] || 0) + v
      })
    }
    return acc
  }, {})

  // Build trend data from analysis timestamps
  const trendData = analytics
    .filter((a) => a.kpi_summary)
    .map((a) => ({
      label: a.timestamp ? new Date(a.timestamp).toLocaleDateString() : '?',
      value: Object.values(a.kpi_summary).reduce((s, v) => s + v, 0),
    }))
    .reverse()

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Dashboard</h1>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard title="Total Clients"    value={summary?.total_clients}  icon={Users}          color="brand" />
        <KPICard title="Uploaded Inputs"  value={summary?.total_inputs}   icon={FileInput}      color="green" />
        <KPICard title="Pending Drafts"   value={summary?.pending_drafts} icon={FileText}       color="amber" />
        <KPICard title="Anomalies Found"  value={summary?.total_anomalies} icon={AlertTriangle} color="red" />
      </div>

      {/* Charts row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
          <h3 className="text-sm font-semibold text-gray-700 mb-4">KPI Overview</h3>
          <KPIBarChart kpis={mergedKpis} />
        </div>
        <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
          <h3 className="text-sm font-semibold text-gray-700 mb-4">Draft Status</h3>
          <DraftStatusPie
            approved={summary?.approved_drafts || 0}
            pending={summary?.pending_drafts || 0}
          />
        </div>
      </div>

      {/* Trend chart */}
      <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
        <h3 className="text-sm font-semibold text-gray-700 mb-4">Revenue / Value Trends</h3>
        <TrendLineChart data={trendData} />
      </div>
    </div>
  )
}
