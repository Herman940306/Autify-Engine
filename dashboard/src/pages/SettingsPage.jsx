import { useEffect, useState } from 'react'
import { healthCheck } from '../api'

/**
 * SettingsPage — system health, license info, and configuration.
 */
export default function SettingsPage() {
  const [health, setHealth] = useState(null)

  useEffect(() => { healthCheck().then(setHealth).catch(() => {}) }, [])

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Settings</h1>

      <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm max-w-xl space-y-4">
        <h3 className="font-semibold text-sm">System Health</h3>
        {health ? (
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-full bg-green-500" />
            <span className="text-sm text-gray-700">{health.engine} — {health.status}</span>
          </div>
        ) : (
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-full bg-red-500" />
            <span className="text-sm text-gray-500">Backend unreachable</span>
          </div>
        )}

        <hr className="border-gray-100" />

        <h3 className="font-semibold text-sm">License</h3>
        <p className="text-sm text-gray-500">
          Hardware-bound activation enforced. Contact your administrator to manage reactivations
          (up to 2 per 12-month period).
        </p>

        <hr className="border-gray-100" />

        <h3 className="font-semibold text-sm">Zero-Cloud Compliance</h3>
        <p className="text-sm text-gray-500">
          All data processing occurs locally. No operational data is transmitted externally.
          Optional anonymized telemetry can be enabled below (off by default).
        </p>
        <label className="flex items-center gap-2 text-sm">
          <input type="checkbox" className="rounded" disabled />
          <span className="text-gray-400">Enable anonymized telemetry (coming soon)</span>
        </label>
      </div>
    </div>
  )
}
