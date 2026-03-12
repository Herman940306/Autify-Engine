import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './auth/AuthContext'
import LoginPage from './auth/LoginPage'
import ChangePasswordModal from './auth/ChangePasswordModal'
import Layout from './components/Layout'
import DashboardPage from './pages/DashboardPage'
import ClientsPage from './pages/ClientsPage'
import InputsPage from './pages/InputsPage'
import DraftsPage from './pages/DraftsPage'
import ReportsPage from './pages/ReportsPage'
import SettingsPage from './pages/SettingsPage'
import ChatPage from './pages/ChatPage'
import UsersPage from './pages/UsersPage'

function AppRoutes() {
  const { user, loading, checkAuth } = useAuth()

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="w-10 h-10 rounded-lg bg-brand-600 text-white flex items-center justify-center text-lg font-bold mx-auto mb-3 animate-pulse">
            AE
          </div>
          <p className="text-sm text-gray-400">Loading...</p>
        </div>
      </div>
    )
  }

  if (!user) {
    return (
      <Routes>
        <Route path="*" element={<LoginPage />} />
      </Routes>
    )
  }

  // Force password change on first login
  if (user.must_change_password) {
    return (
      <>
        <ChangePasswordModal
          forced
          onDone={() => checkAuth()}
        />
        <Routes>
          <Route path="*" element={<LoginPage />} />
        </Routes>
      </>
    )
  }

  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<DashboardPage />} />
        <Route path="clients" element={<ClientsPage />} />
        <Route path="inputs" element={<InputsPage />} />
        <Route path="drafts" element={<DraftsPage />} />
        <Route path="chat" element={<ChatPage />} />
        <Route path="reports" element={<ReportsPage />} />
        <Route path="users" element={<UsersPage />} />
        <Route path="settings" element={<SettingsPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  )
}
