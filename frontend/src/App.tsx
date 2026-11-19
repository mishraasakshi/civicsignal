import { useAuth } from './auth/context'
import { Logo } from './components/Logo'
import { LoginPage } from './pages/LoginPage'
import { StudentHome } from './pages/StudentHome'
import { SupervisorDashboard } from './pages/SupervisorDashboard'

function App() {
  const { user, loading, logout } = useAuth()

  if (loading) return <p className="center-note">Loading…</p>
  if (!user) return <LoginPage />

  const isSupervisor = user.role === 'supervisor'

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand small">
          <Logo size={26} />
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
        {isSupervisor ? <SupervisorDashboard /> : <StudentHome />}
      </main>
    </div>
  )
}

export default App
