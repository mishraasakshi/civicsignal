import { useState, type FormEvent } from 'react'
import { ApiError } from '../api'
import { useAuth } from '../auth/context'
import { Logo } from '../components/Logo'

type Mode = 'login' | 'register'

export function LoginPage() {
  const { login, register } = useAuth()
  const [mode, setMode] = useState<Mode>('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [alreadyRegistered, setAlreadyRegistered] = useState(false)
  const [showPassword, setShowPassword] = useState(false)
  const [busy, setBusy] = useState(false)

  function switchMode(next: Mode) {
    setMode(next)
    setError(null)
    setAlreadyRegistered(false)
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault() // stop the browser from reloading the page
    setError(null)
    setAlreadyRegistered(false)

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
      else if (err instanceof ApiError && err.status === 409) {
        setError('This email is already registered.')
        setAlreadyRegistered(true)
      }
      else if (err instanceof ApiError) setError(err.message)
      else setError('Something went wrong. Please try again.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <main className="auth-page">
      <section className="auth-hero" aria-label="About CivicSignal">
        <div className="brand hero-brand">
          <Logo size={34} />
          <span>CivicSignal</span>
        </div>

        <h1 className="hero-title">
          Campus problems,
          <br />
          <span className="hero-accent">heard and fixed.</span>
        </h1>
        <p className="hero-sub">
          Report a broken geyser, slow Wi-Fi or bad mess food in your own words. AI sorts it to the right team,
          and you can follow it until it's resolved.
        </p>

        <ul className="hero-features">
          <li>
            <span className="feature-icon" aria-hidden="true">
              <svg viewBox="0 0 24 24"><path d="M4 5h16v11H8l-4 4z" /></svg>
            </span>
            <div>
              <strong>Write it your way</strong>
              <span>English, Hindi or Hinglish</span>
            </div>
          </li>
          <li>
            <span className="feature-icon" aria-hidden="true">
              <svg viewBox="0 0 24 24"><path d="M12 3l2.2 5.8L20 11l-5.8 2.2L12 19l-2.2-5.8L4 11l5.8-2.2z" /></svg>
            </span>
            <div>
              <strong>Sorted instantly</strong>
              <span>A multilingual AI model picks the category</span>
            </div>
          </li>
          <li>
            <span className="feature-icon" aria-hidden="true">
              <svg viewBox="0 0 24 24"><path d="M4 12l5 5L20 6" /></svg>
            </span>
            <div>
              <strong>Tracked until fixed</strong>
              <span>Submitted → Assigned → In Progress → Resolved</span>
            </div>
          </li>
        </ul>

        <div className="demo-card" aria-hidden="true">
          <p className="demo-text">“B block geyser kharab hai, garam paani nahi aa raha”</p>
          <div className="demo-result">
            <span className="demo-chip">Water &amp; plumbing</span>
            <span className="demo-arrow">AI sorted · Assigned to maintenance</span>
          </div>
        </div>
      </section>

      <div className="auth-card">
        <div className="brand mobile-only">
          <Logo size={30} />
          <span>CivicSignal</span>
        </div>
        <h2 className="auth-title">{mode === 'login' ? 'Welcome back' : 'Create your account'}</h2>
        <p className="tagline">
          {mode === 'login'
            ? 'Log in to report a problem or check on one.'
            : 'Students can sign up with their email in seconds.'}
        </p>

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
            <div className="password-box">
              <input
                type={showPassword ? 'text' : 'password'}
                autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder={mode === 'register' ? 'At least 8 characters' : ''}
              />
              <button
                type="button"
                className="show-btn"
                onClick={() => setShowPassword((v) => !v)}
                aria-label={showPassword ? 'Hide password' : 'Show password'}
              >
                {showPassword ? 'Hide' : 'Show'}
              </button>
            </div>
          </label>

          {error && (
            <p className="error" role="alert">
              {error}{' '}
              {alreadyRegistered && (
                <button type="button" className="link-btn" onClick={() => switchMode('login')}>
                  Log in instead →
                </button>
              )}
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
