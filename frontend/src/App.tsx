import { useAuth } from './auth/context'
import { LoginPage } from './pages/LoginPage'

function App() {
  const { user, loading, logout } = useAuth()

  if (loading) return <p className="center-note">Loading…</p>
  if (!user) return <LoginPage />

  const isSupervisor = user.role === 'supervisor'

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand small">
          <span className="brand-mark" aria-hidden="true">◉</span>
          <span>CivicSignal</span>
        </div>
        <div className="who">
          <span className={isSupervisor ? 'badge supervisor' : 'badge'}>
            {isSupervisor ? 'Supervisor' : 'Student'}
          </span>
          <span className="email">{user.email}</span>
          <button type="button" className="ghost" onClick={logout}>
            Log out
          </button>
        </div>
      </header>

      <main className="content">
        <h1>Welcome 👋</h1>
        <p>
          You're logged in as <strong>{user.email}</strong>.
        </p>
        <p className="muted">
          {isSupervisor
            ? 'Next step: the supervisor dashboard (review queue, filters, status updates).'
            : 'Next step: submit a complaint and track its status.'}
        </p>
      </main>
    </div>
  )
}

export default App
