import { useEffect, useState } from 'react'
import { Bell } from 'lucide-react'
import { fetchNotifications } from '../api'

/**
 * Notification bell icon with badge count.
 * Displays pending drafts and anomaly alerts.
 */
export default function NotificationBell() {
  const [notifications, setNotifications] = useState([])
  const [open, setOpen] = useState(false)

  useEffect(() => {
    fetchNotifications()
      .then(setNotifications)
      .catch(() => setNotifications([]))
  }, [])

  const count = notifications.length

  return (
    <div className="relative">
      <button
        onClick={() => setOpen(!open)}
        className="relative p-2 rounded-lg hover:bg-gray-100 transition-colors"
      >
        <Bell size={18} />
        {count > 0 && (
          <span className="absolute -top-0.5 -right-0.5 w-4 h-4 rounded-full bg-red-500 text-white text-[10px] flex items-center justify-center font-bold">
            {count > 9 ? '9+' : count}
          </span>
        )}
      </button>

      {open && (
        <div className="absolute right-0 mt-2 w-80 bg-white rounded-xl shadow-xl border border-gray-200 z-50 max-h-96 overflow-y-auto">
          <div className="px-4 py-3 border-b border-gray-100 font-semibold text-sm">
            Notifications ({count})
          </div>
          {notifications.length === 0 && (
            <div className="px-4 py-6 text-center text-sm text-gray-400">All clear!</div>
          )}
          {notifications.map((n, i) => (
            <div
              key={i}
              className={`px-4 py-3 border-b border-gray-50 text-sm ${
                n.severity === 'error' ? 'bg-red-50' : 'bg-yellow-50'
              }`}
            >
              <span
                className={`inline-block w-2 h-2 rounded-full mr-2 ${
                  n.severity === 'error' ? 'bg-red-500' : 'bg-yellow-500'
                }`}
              />
              {n.message}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
