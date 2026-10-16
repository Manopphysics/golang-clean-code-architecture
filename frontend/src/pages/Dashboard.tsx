import { useEffect, useState } from 'react'
import { apiLogout, apiProfile, auth, type UserEntity } from '../api'
import CRUDViewer from '../components/CRUDViewer'

const s = {
  layout: { minHeight: '100vh', background: '#0f172a' },
  nav: { background: '#1e293b', borderBottom: '1px solid #334155', padding: '0 2rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between', height: 60 },
  brand: { fontSize: '1rem', fontWeight: 700, color: '#6366f1' },
  navRight: { display: 'flex', alignItems: 'center', gap: '1rem' },
  navUser: { color: '#94a3b8', fontSize: '.875rem' },
  logoutBtn: { padding: '0.375rem 0.875rem', background: 'transparent', border: '1px solid #475569', borderRadius: 6, color: '#94a3b8', cursor: 'pointer', fontSize: '.8rem', fontWeight: 500 },
  main: { maxWidth: 1100, margin: '0 auto', padding: '2rem 1.5rem' },
  grid: { display: 'grid', gridTemplateColumns: '300px 1fr', gap: '1.5rem', alignItems: 'start' },
  card: { background: '#1e293b', borderRadius: 12, padding: '1.5rem', border: '1px solid #334155' },
  cardTitle: { fontSize: '.7rem', textTransform: 'uppercase' as const, letterSpacing: '.1em', color: '#64748b', fontWeight: 600, marginBottom: '1rem' },
  avatar: { width: 64, height: 64, borderRadius: '50%', background: '#6366f1', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1.5rem', fontWeight: 700, color: '#fff', marginBottom: '1rem' },
  name: { fontSize: '1.1rem', fontWeight: 600, color: '#f1f5f9' },
  email: { color: '#64748b', fontSize: '.85rem', marginTop: 2 },
  badge: { display: 'inline-block', marginTop: '0.75rem', padding: '0.25rem 0.625rem', background: '#1d4ed8', borderRadius: 999, fontSize: '.75rem', color: '#bfdbfe', fontWeight: 500 },
  divider: { borderColor: '#334155', margin: '1rem 0' },
  metaRow: { display: 'flex', justifyContent: 'space-between', fontSize: '.8rem', color: '#64748b', marginBottom: 6 },
  metaVal: { color: '#94a3b8' },
  loading: { color: '#64748b', fontSize: '.875rem' },
} as const

interface Props { onLogout: () => void }

export default function Dashboard({ onLogout }: Props) {
  const [user, setUser] = useState<UserEntity | null>(null)
  const [loggingOut, setLoggingOut] = useState(false)

  useEffect(() => {
    apiProfile().then(setUser).catch(() => { auth.clear(); onLogout() })
  }, [onLogout])

  const handleLogout = async () => {
    setLoggingOut(true)
    try {
      const refresh = auth.getRefresh()
      if (refresh) await apiLogout(refresh)
    } catch { /* ignore */ }
    auth.clear()
    onLogout()
  }

  const initials = user ? `${user.first_name[0]}${user.last_name[0]}`.toUpperCase() : '?'
  const fmt = (iso: string) => new Date(iso).toLocaleDateString()

  return (
    <div style={s.layout}>
      <nav style={s.nav}>
        <span style={s.brand}>⚡ Clean Architecture API</span>
        <div style={s.navRight}>
          {user && <span style={s.navUser}>Signed in as {user.email}</span>}
          <button style={s.logoutBtn} onClick={handleLogout} disabled={loggingOut}>
            {loggingOut ? 'Signing out…' : 'Sign out'}
          </button>
        </div>
      </nav>

      <main style={s.main}>
        <div style={s.grid}>
          {/* Profile card */}
          <div style={s.card}>
            <p style={s.cardTitle}>Profile</p>
            {user ? (
              <>
                <div style={s.avatar}>{initials}</div>
                <p style={s.name}>{user.first_name} {user.last_name}</p>
                <p style={s.email}>{user.email}</p>
                <span style={s.badge}>ID #{user.id}</span>
                <hr style={s.divider} />
                <div style={s.metaRow}><span>Member since</span><span style={s.metaVal}>{fmt(user.created_at)}</span></div>
                <div style={s.metaRow}><span>Last updated</span><span style={s.metaVal}>{fmt(user.updated_at)}</span></div>
              </>
            ) : (
              <p style={s.loading}>Loading profile…</p>
            )}
          </div>

          {/* CRUD viewer */}
          <CRUDViewer />
        </div>
      </main>
    </div>
  )
}
