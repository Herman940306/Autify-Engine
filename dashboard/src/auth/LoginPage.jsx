import { useState } from 'react'
import { useAuth } from './AuthContext'

export default function LoginPage() {
  const { login } = useAuth()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await login(username, password)
    } catch (err) {
      setError(err.message || 'Login failed')
    }
    setLoading(false)
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-brand-900 to-brand-950">
      <div className="w-full max-w-sm bg-white rounded-2xl shadow-2xl p-8">
        {/* Brand */}
        <div className="text-center mb-8">
          <div className="w-14 h-14 rounded-xl bg-brand-600 text-white flex items-center justify-center text-xl font-bold mx-auto mb-3">
            AE
          </div>
          <h1 className="text-xl font-bold text-gray-900">Autify Engine V1</h1>
          <p className="text-sm text-gray-500 mt-1">Zero-Cloud | Draft-Only | Secure</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Username</label>
            <input
              type="text"
              className="w-full border border-gray-300 rounded-lg px-3 py-2.5 text-sm focus:ring-2 focus:ring-brand-500 outline-none"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="admin"
              autoFocus
              required
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Password</label>
            <input
              type="password"
              className="w-full border border-gray-300 rounded-lg px-3 py-2.5 text-sm focus:ring-2 focus:ring-brand-500 outline-none"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter password"
              required
            />
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 text-sm rounded-lg px-3 py-2">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full py-2.5 text-sm font-semibold rounded-lg bg-brand-600 text-white hover:bg-brand-700 transition-colors disabled:opacity-50"
          >
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>

        <p className="text-center text-xs text-gray-400 mt-6">
          Default: admin / admin123
        </p>
      </div>
    </div>
  )
}
