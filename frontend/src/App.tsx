import { useAuth } from './auth/context'
import { LoginPage } from './pages/LoginPage'
import { StudentHome } from './pages/StudentHome'

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
        {isSupervisor ? (
          <>
            <h1>Supervisor dashboard</h1>
            <p className="muted">Coming next: review queue, filters and status updates.</p>
          </>
        ) : (
          <StudentHome />
        )}
      </main>
    </div>
  )
}

export default App
