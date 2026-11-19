import { useState, type FormEvent } from 'react'
import { ApiError } from '../api'
import { useAuth } from '../auth/context'

type Mode = 'login' | 'register'

export function LoginPage() {
  const { login, register } = useAuth()
  const [mode, setMode] = useState<Mode>('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  function switchMode(next: Mode) {
    setMode(next)
    setError(null)
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault() // stop the browser from reloading the page
    setError(null)

    if (mode === 'register' && password.length < 8) {
      setError('Password must be at least 8 characters.')
      return
    }

    setBusy(true)
    try {
      if (mode === 'login') await login(email, password)
      else await register(email, password)
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) setError('Wrong email or password.')
      else if (err instanceof ApiError && err.status === 409) setError('This email is already registered. Log in instead.')
      else if (err instanceof ApiError) setError(err.message)
      else setError('Something went wrong. Please try again.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <main className="auth-page">
      <div className="auth-card">
        <div className="brand">
          <span className="brand-mark" aria-hidden="true">◉</span>
          <span>CivicSignal</span>
        </div>
        <p className="tagline">Report campus problems. Track them until they're fixed.</p>

        <div className="tabs" role="tablist">
          <button
            type="button"
            role="tab"
            aria-selected={mode === 'login'}
            className={mode === 'login' ? 'tab active' : 'tab'}
            onClick={() => switchMode('login')}
          >
            Log in
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={mode === 'register'}
            className={mode === 'register' ? 'tab active' : 'tab'}
            onClick={() => switchMode('register')}
          >
            Sign up
          </button>
        </div>

        <form onSubmit={handleSubmit} className="form">
          <label>
            Email
            <input
              type="email"
              autoComplete="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
            />
          </label>

          <label>
            Password
            <input
              type="password"
              autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder={mode === 'register' ? 'At least 8 characters' : ''}
            />
          </label>

          {error && (
            <p className="error" role="alert">
              {error}
            </p>
          )}

          <button type="submit" className="primary" disabled={busy}>
            {busy ? 'Please wait…' : mode === 'login' ? 'Log in' : 'Create student account'}
          </button>
        </form>

        {mode === 'register' && (
          <p className="hint">Sign-up creates a student account. Supervisor accounts are created by the admin.</p>
        )}
      </div>
    </main>
  )
}
