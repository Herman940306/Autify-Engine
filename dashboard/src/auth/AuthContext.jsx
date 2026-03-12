import { createContext, useContext, useState, useEffect, useCallback } from 'react'
import { authLogin, authLogout, authMe, setAuthToken, getAuthToken } from '../api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  const checkAuth = useCallback(async () => {
    const token = getAuthToken()
    if (!token) {
      setUser(null)
      setLoading(false)
      return
    }
    try {
      const me = await authMe()
      setUser(me)
    } catch {
      setAuthToken(null)
      setUser(null)
    }
    setLoading(false)
  }, [])

  useEffect(() => {
    checkAuth()
    const handler = () => { setUser(null); setLoading(false) }
    window.addEventListener('autify:logout', handler)
    return () => window.removeEventListener('autify:logout', handler)
  }, [checkAuth])

  const login = async (username, password) => {
    const res = await authLogin({ username, password })
    setAuthToken(res.token)
    setUser({ ...res.user, permissions: (await authMe()).permissions })
    return res.user
  }

  const logout = async () => {
    try { await authLogout() } catch {}
    setAuthToken(null)
    setUser(null)
  }

  const can = (action) => user?.permissions?.[action] ?? false

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, can, checkAuth }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be inside AuthProvider')
  return ctx
}
