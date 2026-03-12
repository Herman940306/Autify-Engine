import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  LineChart, Line, PieChart, Pie, Cell,
} from 'recharts'

const COLORS = ['#3388ff', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6']

/**
 * KPIBarChart — vertical bar chart of KPI key-value pairs.
 * @param {Object} kpis – e.g. { revenue_sum: 50000, orders_mean: 12.5 }
 */
export function KPIBarChart({ kpis }) {
  const data = Object.entries(kpis || {}).map(([key, value]) => ({
    name: key.replace(/_/g, ' '),
    value: Number(value) || 0,
  }))

  if (data.length === 0) return <p className="text-gray-400 text-sm">No KPI data yet.</p>

  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="name" tick={{ fontSize: 11 }} />
        <YAxis tick={{ fontSize: 11 }} />
        <Tooltip />
        <Bar dataKey="value" fill="#3388ff" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  )
}

/**
 * TrendLineChart — time-series line chart.
 * @param {Array} data – [{ label, value }, ...]
 */
export function TrendLineChart({ data }) {
  if (!data || data.length === 0) return <p className="text-gray-400 text-sm">No trend data yet.</p>

  return (
    <ResponsiveContainer width="100%" height={280}>
      <LineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="label" tick={{ fontSize: 11 }} />
        <YAxis tick={{ fontSize: 11 }} />
        <Tooltip />
        <Line type="monotone" dataKey="value" stroke="#1354e1" strokeWidth={2} dot={{ r: 3 }} />
      </LineChart>
    </ResponsiveContainer>
  )
}

/**
 * DraftStatusPie — pie chart of approved vs pending drafts.
 * @param {number} approved
 * @param {number} pending
 */
export function DraftStatusPie({ approved = 0, pending = 0 }) {
  const data = [
    { name: 'Approved', value: approved },
    { name: 'Pending',  value: pending },
  ]

  return (
    <ResponsiveContainer width="100%" height={220}>
      <PieChart>
        <Pie data={data} cx="50%" cy="50%" outerRadius={80} dataKey="value" label>
          {data.map((_, i) => (
            <Cell key={i} fill={COLORS[i % COLORS.length]} />
          ))}
        </Pie>
        <Tooltip />
      </PieChart>
    </ResponsiveContainer>
  )
}
