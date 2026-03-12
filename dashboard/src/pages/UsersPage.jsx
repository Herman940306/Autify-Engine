import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { UserPlus, Shield, Trash2 } from 'lucide-react'
import { authListUsers, authRegister, authDeleteUser } from '../api'
import { useAuth } from '../auth/AuthContext'

/**
 * UsersPage - admin-only user management.
 */
export default function UsersPage() {
  const { can } = useAuth()
  const [users, setUsers] = useState([])
  const [form, setForm] = useState({ username: '', password: '', role: 'user', display_name: '' })
  const [showForm, setShowForm] = useState(false)
  const [error, setError] = useState('')

  const load = () => authListUsers().then(setUsers).catch(() => {})
  useEffect(() => { load() }, [])

  const handleCreate = async (e) => {
    e.preventDefault()
    setError('')
    try {
      await authRegister(form)
      setForm({ username: '', password: '', role: 'user', display_name: '' })
      setShowForm(false)
      load()
    } catch (err) {
      setError(err.message)
    }
  }

  const handleDelete = async (id, name) => {
    if (!confirm(`Deactivate user "${name}"?`)) return
    try {
      await authDeleteUser(id)
      load()
    } catch (err) {
      alert(err.message)
    }
  }

  if (!can('can_manage_users')) {
    return (
      <div className="text-center py-20 text-gray-400">
        <Shield size={48} className="mx-auto mb-3 opacity-50" />
        <p className="font-medium">Admin access required</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">User Management</h1>
        <button
          onClick={() => setShowForm(!showForm)}
          className="inline-flex items-center gap-1.5 px-4 py-2 text-sm font-medium rounded-lg bg-brand-600 text-white hover:bg-brand-700 transition-colors"
        >
          <UserPlus size={15} /> Add User
        </button>
      </div>

      {/* Create user form */}
      {showForm && (
        <form onSubmit={handleCreate} className="flex flex-wrap gap-3 items-end bg-white p-4 rounded-xl border border-gray-200 shadow-sm">
          <div>
            <label className="block text-xs text-gray-500 mb-1">Username</label>
            <input
              className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-brand-400 outline-none"
              value={form.username}
              onChange={(e) => setForm({ ...form, username: e.target.value })}
              required
            />
          </div>
          <div>
            <label className="block text-xs text-gray-500 mb-1">Password</label>
            <input
              type="password"
              className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-brand-400 outline-none"
              value={form.password}
              onChange={(e) => setForm({ ...form, password: e.target.value })}
              required
            />
          </div>
          <div>
            <label className="block text-xs text-gray-500 mb-1">Display Name</label>
            <input
              className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-brand-400 outline-none"
              value={form.display_name}
              onChange={(e) => setForm({ ...form, display_name: e.target.value })}
            />
          </div>
          <div>
            <label className="block text-xs text-gray-500 mb-1">Role</label>
            <select
              className="border border-gray-300 rounded-lg px-3 py-2 text-sm"
              value={form.role}
              onChange={(e) => setForm({ ...form, role: e.target.value })}
            >
              <option value="user">User</option>
              <option value="admin">Admin</option>
            </select>
          </div>
          <button type="submit" className="px-4 py-2 text-sm font-medium rounded-lg bg-green-600 text-white hover:bg-green-700 transition-colors">
            Create
          </button>
          {error && <span className="text-red-600 text-sm">{error}</span>}
        </form>
      )}

      {/* User table */}
      <div className="overflow-x-auto rounded-xl border border-gray-200 bg-white shadow-sm">
        <table className="min-w-full text-sm">
          <thead>
            <tr className="bg-gray-50 text-left text-xs uppercase tracking-wider text-gray-500">
              <th className="px-4 py-3">ID</th>
              <th className="px-4 py-3">Username</th>
              <th className="px-4 py-3">Display Name</th>
              <th className="px-4 py-3">Role</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Last Login</th>
              <th className="px-4 py-3 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {users.map((u) => (
              <motion.tr key={u.user_id} initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
                <td className="px-4 py-3 font-mono text-xs">#{u.user_id}</td>
                <td className="px-4 py-3 font-medium">{u.username}</td>
                <td className="px-4 py-3">{u.display_name || '-'}</td>
                <td className="px-4 py-3">
                  <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${
                    u.role === 'admin' ? 'bg-purple-100 text-purple-700' : 'bg-blue-100 text-blue-700'
                  }`}>
                    {u.role === 'admin' && <Shield size={10} />}
                    {u.role}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <span className={`w-2 h-2 rounded-full inline-block mr-1.5 ${u.is_active ? 'bg-green-500' : 'bg-red-400'}`} />
                  {u.is_active ? 'Active' : 'Inactive'}
                </td>
                <td className="px-4 py-3 text-gray-500 text-xs">
                  {u.last_login ? new Date(u.last_login).toLocaleString() : 'Never'}
                </td>
                <td className="px-4 py-3 text-right">
                  {u.is_active && u.role !== 'admin' && (
                    <button
                      onClick={() => handleDelete(u.user_id, u.username)}
                      className="inline-flex items-center gap-1 px-3 py-1 text-xs rounded-lg text-red-600 hover:bg-red-50 transition-colors"
                    >
                      <Trash2 size={12} /> Deactivate
                    </button>
                  )}
                </td>
              </motion.tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
