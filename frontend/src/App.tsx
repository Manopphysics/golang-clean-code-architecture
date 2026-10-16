import { useState } from 'react'
import { auth } from './api'
import AuthPage from './pages/AuthPage'
import Dashboard from './pages/Dashboard'

export default function App() {
  const [loggedIn, setLoggedIn] = useState(auth.isLoggedIn())

  const handleLogin = () => setLoggedIn(true)
  const handleLogout = () => {
    auth.clear()
    setLoggedIn(false)
  }

  return loggedIn ? (
    <Dashboard onLogout={handleLogout} />
  ) : (
    <AuthPage onLogin={handleLogin} />
  )
}
