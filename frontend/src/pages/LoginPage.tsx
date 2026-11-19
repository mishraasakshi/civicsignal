import { useId, useState, type FormEvent } from 'react'
import { ApiError } from '../api'
import { useAuth } from '../auth/context'
import { Logo } from '../components/Logo'
import { PolicyDialog, type Policy } from '../components/PolicyDialog'

type Mode = 'login' | 'register'
type Field = 'email' | 'password' | 'confirm'
type FieldErrors = Partial<Record<Field, string>>

// Same rules as the backend (backend/app/schemas/auth.py)
const EMAIL_RE = /^[^@\s]+@[^@\s]+\.[^@\s]+$/
const MIN_PASSWORD = 8
const MAX_PASSWORD_BYTES = 72 // bcrypt only uses the first 72 bytes

function passwordBytes(pw: string): number {
  return new TextEncoder().encode(pw).length
}

function validate(mode: Mode, email: string, password: string, confirm: string): FieldErrors {
  const errors: FieldErrors = {}
  if (!email.trim()) errors.email = 'Please enter your email.'
  else if (!EMAIL_RE.test(email.trim())) errors.email = 'This doesn’t look like an email address (e.g. name@example.com).'

  if (!password) errors.password = 'Please enter your password.'
  else if (mode === 'register' && password.length < MIN_PASSWORD)
    errors.password = `Use at least ${MIN_PASSWORD} characters.`
  else if (mode === 'register' && passwordBytes(password) > MAX_PASSWORD_BYTES)
    errors.password = 'This password is too long (max 72 bytes).'

  if (mode === 'register') {
    if (!confirm) errors.confirm = 'Please type your password again.'
    else if (confirm !== password) errors.confirm = 'The passwords don’t match.'
  }
  return errors
}

export function LoginPage() {
  const { login, register } = useAuth()
  const ids = useId()
  const [mode, setMode] = useState<Mode>('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({})
  const [formError, setFormError] = useState<string | null>(null)
  const [alreadyRegistered, setAlreadyRegistered] = useState(false)
  const [showForgot, setShowForgot] = useState(false)
  const [busy, setBusy] = useState(false)
  const [policy, setPolicy] = useState<Policy | null>(null)

  function switchMode(next: Mode) {
    setMode(next)
    setFieldErrors({})
    setFormError(null)
    setAlreadyRegistered(false)
    setShowForgot(false)
    setConfirm('')
  }

  // Clear a field's error as soon as the user starts fixing it
  function clearError(field: Field) {
    if (fieldErrors[field]) setFieldErrors((prev) => ({ ...prev, [field]: undefined }))
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault() // stop the browser from reloading the page
    if (busy) return // no double submits
    setFormError(null)
    setAlreadyRegistered(false)

    const errors = validate(mode, email, password, confirm)
    setFieldErrors(errors)
    if (Object.keys(errors).length > 0) {
      // move keyboard focus to the first field with a problem
      const first = (['email', 'password', 'confirm'] as Field[]).find((f) => errors[f])
      document.getElementById(`${ids}-${first}`)?.focus()
      return
    }

    setBusy(true)
    try {
      if (mode === 'login') await login(email.trim(), password)
      else await register(email.trim(), password)
      // success: the app switches to the logged-in page and shows a success message
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) setFormError('Wrong email or password. Please try again.')
      else if (err instanceof ApiError && err.status === 409) {
        setFormError('This email is already registered.')
        setAlreadyRegistered(true)
      } else if (err instanceof ApiError && err.status === 429)
        setFormError('Too many attempts. Please wait a minute and try again.')
      else if (err instanceof ApiError && err.status === 0) setFormError(err.message)
      else if (err instanceof ApiError && err.status === 422)
        setFormError('Please check your email and password and try again.')
      else setFormError('Something went wrong on our side. Please try again.')
    } finally {
      setBusy(false)
    }
  }

  const isRegister = mode === 'register'
  const pwLongEnough = password.length >= MIN_PASSWORD
  const errId = (f: Field) => `${ids}-${f}-error`

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
          Report a broken geyser, slow Wi-Fi or bad mess food in your own words. AI sorts it to the right team, and
          you can follow it until it’s resolved.
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
              <span>AI categorises the complaint</span>
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

        <figure className="demo-card">
          <figcaption className="demo-label">Example complaint</figcaption>
          <blockquote className="demo-text">“B block geyser kharab hai, garam paani nahi aa raha”</blockquote>
          <div className="demo-result">
            <span className="demo-chip">Water &amp; Plumbing</span>
            <span className="demo-arrow">AI sorted · Assigned to maintenance</span>
          </div>
        </figure>
      </section>

      <div className="auth-column">
        <div className="auth-card">
          <div className="brand mobile-only">
            <Logo size={30} />
            <span>CivicSignal</span>
          </div>
          <h2 className="auth-title">{isRegister ? 'Create your account' : 'Welcome back'}</h2>
          <p className="tagline">
            {isRegister
              ? 'Students can sign up with their email in seconds.'
              : 'Log in to report a problem or check on one.'}
          </p>

          <div className="tabs" role="tablist" aria-label="Log in or sign up">
            <button
              type="button"
              role="tab"
              aria-selected={!isRegister}
              className={!isRegister ? 'tab active' : 'tab'}
              onClick={() => switchMode('login')}
            >
              Log in
            </button>
            <button
              type="button"
              role="tab"
              aria-selected={isRegister}
              className={isRegister ? 'tab active' : 'tab'}
              onClick={() => switchMode('register')}
            >
              Sign up
            </button>
          </div>

          <form onSubmit={handleSubmit} className="form auth-form" noValidate aria-busy={busy}>
            <div className="field">
              <label htmlFor={`${ids}-email`}>Email</label>
              <input
                id={`${ids}-email`}
                type="email"
                inputMode="email"
                autoComplete="email"
                value={email}
                onChange={(e) => {
                  setEmail(e.target.value)
                  clearError('email')
                }}
                placeholder="you@example.com"
                aria-invalid={!!fieldErrors.email}
                aria-describedby={fieldErrors.email ? errId('email') : undefined}
              />
              {fieldErrors.email && (
                <p className="field-error" id={errId('email')}>
                  {fieldErrors.email}
                </p>
              )}
            </div>

            <div className="field">
              <div className="label-row">
                <label htmlFor={`${ids}-password`}>Password</label>
                {!isRegister && (
                  <button
                    type="button"
                    className="text-link"
                    aria-expanded={showForgot}
                    aria-controls={`${ids}-forgot`}
                    onClick={() => setShowForgot((v) => !v)}
                  >
                    Forgot password?
                  </button>
                )}
              </div>
              <div className="password-box">
                <input
                  id={`${ids}-password`}
                  type={showPassword ? 'text' : 'password'}
                  autoComplete={isRegister ? 'new-password' : 'current-password'}
                  value={password}
                  onChange={(e) => {
                    setPassword(e.target.value)
                    clearError('password')
                  }}
                  placeholder={isRegister ? 'At least 8 characters' : 'Your password'}
                  aria-invalid={!!fieldErrors.password}
                  aria-describedby={
                    [fieldErrors.password ? errId('password') : '', isRegister ? `${ids}-rules` : '']
                      .filter(Boolean)
                      .join(' ') || undefined
                  }
                />
                <button
                  type="button"
                  className="show-btn"
                  onClick={() => setShowPassword((v) => !v)}
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                  aria-pressed={showPassword}
                >
                  {showPassword ? 'Hide' : 'Show'}
                </button>
              </div>
              {fieldErrors.password && (
                <p className="field-error" id={errId('password')}>
                  {fieldErrors.password}
                </p>
              )}
              {isRegister && (
                <ul className="pw-rules" id={`${ids}-rules`}>
                  <li className={pwLongEnough ? 'ok' : ''}>
                    <span aria-hidden="true">{pwLongEnough ? '✓' : '•'}</span> At least {MIN_PASSWORD} characters
                  </li>
                  <li>
                    <span aria-hidden="true">•</span> Don’t reuse your college or email password
                  </li>
                </ul>
              )}
            </div>

            {!isRegister && showForgot && (
              <div className="info-box" id={`${ids}-forgot`} role="note">
                <strong>Password reset isn’t available yet.</strong> CivicSignal can’t send reset emails in this pilot
                version. If you can’t log in, ask the CivicSignal administrator for help, or create a new account with
                another email.
              </div>
            )}

            {isRegister && (
              <div className="field">
                <label htmlFor={`${ids}-confirm`}>Confirm password</label>
                <input
                  id={`${ids}-confirm`}
                  type={showPassword ? 'text' : 'password'}
                  autoComplete="new-password"
                  value={confirm}
                  onChange={(e) => {
                    setConfirm(e.target.value)
                    clearError('confirm')
                  }}
                  placeholder="Type it again"
                  aria-invalid={!!fieldErrors.confirm}
                  aria-describedby={fieldErrors.confirm ? errId('confirm') : undefined}
                />
                {fieldErrors.confirm && (
                  <p className="field-error" id={errId('confirm')}>
                    {fieldErrors.confirm}
                  </p>
                )}
              </div>
            )}

            {formError && (
              <p className="error" role="alert">
                {formError}{' '}
                {alreadyRegistered && (
                  <button type="button" className="link-btn" onClick={() => switchMode('login')}>
                    Log in instead →
                  </button>
                )}
              </p>
            )}

            <button type="submit" className="primary submit-btn" disabled={busy}>
              {busy && <span className="spinner" aria-hidden="true" />}
              {busy
                ? isRegister
                  ? 'Creating your account…'
                  : 'Logging in…'
                : isRegister
                  ? 'Create student account'
                  : 'Log in'}
            </button>
          </form>

          {isRegister && (
            <p className="hint">
              Sign-up creates a student account. Supervisor accounts are created by the administrator.
            </p>
          )}
        </div>

        <footer className="auth-footer">
          <button type="button" className="footer-link" onClick={() => setPolicy('privacy')}>
            Privacy Policy
          </button>
          <span aria-hidden="true">·</span>
          <button type="button" className="footer-link" onClick={() => setPolicy('terms')}>
            Terms of Service
          </button>
        </footer>
      </div>

      <PolicyDialog policy={policy} onClose={() => setPolicy(null)} />
    </main>
  )
}
