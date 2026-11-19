import { useAuth } from './auth/context'
import { Brand } from './components/Logo'
import { Toast } from './components/Toast'
import { LoginPage } from './pages/LoginPage'
import { StudentHome } from './pages/StudentHome'
import { SupervisorDashboard } from './pages/SupervisorDashboard'

function App() {
  const { user, loading, logout, notice, clearNotice } = useAuth()

  if (loading) return <p className="center-note">Loading…</p>
  if (!user) return <LoginPage />

  const isSupervisor = user.role === 'supervisor'

  return (
    <div className="app">
      {notice && <Toast message={notice} onClose={clearNotice} />}
      <header className="topbar">
        <Brand size={30} />
        <div className="who">
          <span className={isSupervisor ? 'badge supervisor' : 'badge'}>
            {isSupervisor ? 'Supervisor' : 'Student'}
          </span>
          <span className="email">{user.email}</span>
          <button type="button" className="ghost" onClick={() => void logout()}>
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
