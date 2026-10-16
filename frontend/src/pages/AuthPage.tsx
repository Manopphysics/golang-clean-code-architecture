import { useState } from 'react'
import { apiLogin, apiRegister, auth } from '../api'

const s = {
  page: { minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#0f172a' },
  card: { background: '#1e293b', borderRadius: 12, padding: '2rem', width: '100%', maxWidth: 420, boxShadow: '0 25px 50px rgba(0,0,0,.5)' },
  logo: { textAlign: 'center' as const, marginBottom: '1.5rem' },
  title: { fontSize: '1.5rem', fontWeight: 700, color: '#f8fafc', margin: 0 },
  sub: { color: '#64748b', fontSize: '.875rem', marginTop: 4 },
  tabs: { display: 'flex', gap: 4, marginBottom: '1.5rem', background: '#0f172a', borderRadius: 8, padding: 4 },
  tab: (active: boolean): React.CSSProperties => ({
    flex: 1, padding: '0.5rem', border: 'none', borderRadius: 6, cursor: 'pointer',
    fontWeight: 600, fontSize: '.875rem', transition: 'all .2s',
    background: active ? '#6366f1' : 'transparent',
    color: active ? '#fff' : '#64748b',
  }),
  field: { marginBottom: '1rem' },
  label: { display: 'block', fontSize: '.8rem', color: '#94a3b8', marginBottom: 4, fontWeight: 500 },
  input: { width: '100%', padding: '0.625rem 0.75rem', background: '#0f172a', border: '1px solid #334155', borderRadius: 6, color: '#f1f5f9', fontSize: '.875rem', outline: 'none' },
  row: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' },
  btn: { width: '100%', padding: '0.7rem', background: '#6366f1', color: '#fff', border: 'none', borderRadius: 8, fontWeight: 600, fontSize: '.9rem', cursor: 'pointer', marginTop: '0.5rem' },
  err: { background: '#450a0a', border: '1px solid #dc2626', borderRadius: 6, padding: '0.625rem 0.75rem', color: '#fca5a5', fontSize: '.8rem', marginBottom: '1rem' },
  ok: { background: '#052e16', border: '1px solid #16a34a', borderRadius: 6, padding: '0.625rem 0.75rem', color: '#86efac', fontSize: '.8rem', marginBottom: '1rem' },
} as const

interface Props { onLogin: () => void }

export default function AuthPage({ onLogin }: Props) {
  const [tab, setTab] = useState<'login' | 'register'>('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [firstName, setFirstName] = useState('')
  const [lastName, setLastName] = useState('')
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [loading, setLoading] = useState(false)

  const reset = () => { setError(''); setSuccess('') }

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault(); reset(); setLoading(true)
    try {
      const res = await apiLogin(email, password)
      auth.save(res.token)
      onLogin()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed')
    } finally { setLoading(false) }
  }

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault(); reset(); setLoading(true)
    try {
      await apiRegister(email, password, firstName, lastName)
      setSuccess('Account created! You can now log in.')
      setTab('login')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Registration failed')
    } finally { setLoading(false) }
  }

  return (
    <div style={s.page}>
      <div style={s.card}>
        <div style={s.logo}>
          <h1 style={s.title}>Clean Architecture API</h1>
          <p style={s.sub}>Python · FastAPI · Clean Architecture</p>
        </div>

        <div style={s.tabs}>
          <button style={s.tab(tab === 'login')} onClick={() => { setTab('login'); reset() }}>Login</button>
          <button style={s.tab(tab === 'register')} onClick={() => { setTab('register'); reset() }}>Register</button>
        </div>

        {error && <div style={s.err}>{error}</div>}
        {success && <div style={s.ok}>{success}</div>}

        {tab === 'login' ? (
          <form onSubmit={handleLogin}>
            <div style={s.field}>
              <label style={s.label}>Email</label>
              <input style={s.input} type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="you@example.com" required />
            </div>
            <div style={s.field}>
              <label style={s.label}>Password</label>
              <input style={s.input} type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder="••••••••" required />
            </div>
            <button style={s.btn} type="submit" disabled={loading}>{loading ? 'Signing in…' : 'Sign in'}</button>
          </form>
        ) : (
          <form onSubmit={handleRegister}>
            <div style={s.row}>
              <div style={s.field}>
                <label style={s.label}>First Name</label>
                <input style={s.input} value={firstName} onChange={e => setFirstName(e.target.value)} placeholder="John" required />
              </div>
              <div style={s.field}>
                <label style={s.label}>Last Name</label>
                <input style={s.input} value={lastName} onChange={e => setLastName(e.target.value)} placeholder="Doe" required />
              </div>
            </div>
            <div style={s.field}>
              <label style={s.label}>Email</label>
              <input style={s.input} type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="you@example.com" required />
            </div>
            <div style={s.field}>
              <label style={s.label}>Password</label>
              <input style={s.input} type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder="••••••••" required />
            </div>
            <button style={s.btn} type="submit" disabled={loading}>{loading ? 'Creating…' : 'Create account'}</button>
          </form>
        )}
      </div>
    </div>
  )
}
