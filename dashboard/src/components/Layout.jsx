import { Outlet } from 'react-router-dom'
import Sidebar from './Sidebar'
import NotificationBell from './NotificationBell'
import { useAuth } from '../auth/AuthContext'

/**
 * Root layout: sidebar + top bar + page content.
 */
export default function Layout() {
  const { user } = useAuth()

  return (
    <div className="flex min-h-screen">
      <Sidebar />

      <div className="flex-1 flex flex-col">
        {/* Top bar */}
        <header className="flex items-center justify-between px-6 py-3 bg-white border-b border-gray-200">
          <h2 className="text-sm font-medium text-gray-500">
            Local Deployment &middot; Draft-Only Workflow
          </h2>
          <div className="flex items-center gap-4">
            <NotificationBell />
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-full bg-brand-100 text-brand-700 flex items-center justify-center text-xs font-bold">
                {(user?.display_name || user?.username || 'A')[0].toUpperCase()}
              </div>
              {user && (
                <span className="text-xs text-gray-500 hidden sm:inline">
                  {user.display_name || user.username}
                </span>
              )}
            </div>
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 p-6 overflow-y-auto">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
