import { useState } from 'react'
import { authChangePass } from '../api'

/**
 * ChangePasswordModal - forces or allows password change.
 * Props: onDone (callback after success), forced (bool - cannot dismiss)
 */
export default function ChangePasswordModal({ onDone, forced = false }) {
  const [oldPw, setOldPw] = useState('')
  const [newPw, setNewPw] = useState('')
  const [confirmPw, setConfirmPw] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    if (newPw.length < 6) {
      setError('Password must be at least 6 characters')
      return
    }
    if (newPw !== confirmPw) {
      setError('Passwords do not match')
      return
    }
    setLoading(true)
    try {
      await authChangePass({ old_password: oldPw, new_password: newPw })
      onDone()
    } catch (err) {
      setError(err.message || 'Failed to change password')
    }
    setLoading(false)
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
      <div className="bg-white rounded-2xl shadow-2xl p-8 w-full max-w-sm">
        <h2 className="text-lg font-bold mb-1">Change Password</h2>
        {forced && (
          <p className="text-sm text-amber-600 mb-4">
            You must change your default password before continuing.
          </p>
        )}

        <form onSubmit={handleSubmit} className="space-y-3">
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Current Password</label>
            <input
              type="password"
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-brand-500 outline-none"
              value={oldPw}
              onChange={(e) => setOldPw(e.target.value)}
              required
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">New Password</label>
            <input
              type="password"
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-brand-500 outline-none"
              value={newPw}
              onChange={(e) => setNewPw(e.target.value)}
              required
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Confirm New Password</label>
            <input
              type="password"
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-brand-500 outline-none"
              value={confirmPw}
              onChange={(e) => setConfirmPw(e.target.value)}
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
            {loading ? 'Changing...' : 'Update Password'}
          </button>
        </form>
      </div>
    </div>
  )
}
