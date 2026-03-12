import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard,
  Users,
  FileInput,
  FileText,
  BarChart3,
  Settings,
  MessageSquare,
  ShieldCheck,
  LogOut,
} from 'lucide-react'
import clsx from 'clsx'
import { useAuth } from '../auth/AuthContext'

const links = [
  { to: '/',         label: 'Dashboard', icon: LayoutDashboard },
  { to: '/clients',  label: 'Clients',   icon: Users },
  { to: '/inputs',   label: 'Inputs',    icon: FileInput },
  { to: '/drafts',   label: 'Drafts',    icon: FileText },
  { to: '/chat',     label: 'Chat',      icon: MessageSquare, perm: 'can_chat' },
  { to: '/reports',  label: 'Reports',   icon: BarChart3 },
  { to: '/users',    label: 'Users',     icon: ShieldCheck, perm: 'can_manage_users' },
  { to: '/settings', label: 'Settings',  icon: Settings },
]

/**
 * Sidebar -- persistent navigation column with role-based visibility.
 */
export default function Sidebar() {
  const { user, can, logout } = useAuth()

  return (
    <aside className="flex flex-col w-60 min-h-screen bg-brand-950 text-white">
      {/* Brand */}
      <div className="flex items-center gap-2 px-5 py-6 border-b border-brand-800">
        <div className="w-8 h-8 rounded-lg bg-brand-500 flex items-center justify-center font-bold text-sm">
          AE
        </div>
        <span className="text-lg font-semibold tracking-tight">Autify Engine</span>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-1">
        {links
          .filter((l) => !l.perm || can(l.perm))
          .map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) =>
              clsx(
                'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors',
                isActive
                  ? 'bg-brand-700 text-white'
                  : 'text-brand-200 hover:bg-brand-800 hover:text-white',
              )
            }
          >
            <Icon size={18} />
            {label}
          </NavLink>
        ))}
      </nav>

      {/* User + Logout */}
      {user && (
        <div className="px-4 py-3 border-t border-brand-800">
          <div className="flex items-center gap-2 mb-2">
            <div className="w-7 h-7 rounded-full bg-brand-600 flex items-center justify-center text-xs font-bold">
              {(user.display_name || user.username || 'U')[0].toUpperCase()}
            </div>
            <div className="text-xs">
              <div className="font-medium truncate max-w-[130px]">{user.display_name || user.username}</div>
              <div className="text-brand-400">{user.role}</div>
            </div>
          </div>
          <button
            onClick={logout}
            className="flex items-center gap-2 w-full px-3 py-1.5 text-xs rounded-lg text-brand-300 hover:bg-brand-800 hover:text-white transition-colors"
          >
            <LogOut size={14} /> Sign Out
          </button>
        </div>
      )}

      {/* Footer */}
      <div className="px-5 py-4 text-xs text-brand-400 border-t border-brand-800">
        Autify Engine V1 &middot; Zero-Cloud
      </div>
    </aside>
  )
}
