import { motion } from 'framer-motion'

/**
 * KPICard — animated card displaying a single KPI metric.
 * @param {string} title   – KPI label
 * @param {string|number} value – metric value
 * @param {JSX.Element} icon  – lucide icon element
 * @param {string} color   – Tailwind color class prefix (e.g. 'blue', 'green')
 */
export default function KPICard({ title, value, icon: Icon, color = 'brand' }) {
  const bg = {
    brand:  'bg-brand-50  text-brand-700',
    green:  'bg-green-50  text-green-700',
    amber:  'bg-amber-50  text-amber-700',
    red:    'bg-red-50    text-red-700',
    purple: 'bg-purple-50 text-purple-700',
  }[color] || 'bg-gray-50 text-gray-700'

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="bg-white rounded-xl border border-gray-200 p-5 flex items-start gap-4 shadow-sm"
    >
      <div className={`p-3 rounded-lg ${bg}`}>
        {Icon && <Icon size={22} />}
      </div>
      <div>
        <p className="text-sm text-gray-500">{title}</p>
        <p className="text-2xl font-bold mt-0.5">{value ?? '—'}</p>
      </div>
    </motion.div>
  )
}
