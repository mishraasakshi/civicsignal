import { useState, type FormEvent } from 'react'
import { ApiError } from '../api'
import { useAuth } from '../auth/context'

export type Mode = 'login' | 'register'
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

const MailIcon = () => (
  <svg viewBox="0 0 20 20" aria-hidden="true" className="field-icon">
    <rect x="2.5" y="4.5" width="15" height="11" rx="1.5" />
    <path d="M3 5.5l7 5.5 7-5.5" />
  </svg>
)

const LockIcon = () => (
  <svg viewBox="0 0 20 20" aria-hidden="true" className="field-icon">
    <rect x="4" y="9" width="12" height="8.5" rx="1.5" />
    <path d="M6.5 9V6.5a3.5 3.5 0 0 1 7 0V9" />
  </svg>
)

const EyeIcon = ({ off }: { off: boolean }) => (
  <svg viewBox="0 0 20 20" aria-hidden="true">
    <path d="M2 10s3-5.5 8-5.5S18 10 18 10s-3 5.5-8 5.5S2 10 2 10z" />
    <circle cx="10" cy="10" r="2.5" />
    {off && <path d="M3.5 3.5l13 13" />}
  </svg>
)

interface Props {
  mode: Mode
  onModeChange: (mode: Mode) => void
}

/** The login / sign-up card (talks to the real backend through useAuth). */
export function AuthCard({ mode, onModeChange }: Props) {
  const { login, register } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [remember, setRemember] = useState(false)
  const [showPassword, setShowPassword] = useState(false)
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({})
  const [formError, setFormError] = useState<string | null>(null)
  const [alreadyRegistered, setAlreadyRegistered] = useState(false)
  const [showForgot, setShowForgot] = useState(false)
  const [busy, setBusy] = useState(false)

  function switchMode(next: Mode) {
    onModeChange(next)
  }

  // When the mode changes (tabs or header buttons), start with a clean form
  const [shownMode, setShownMode] = useState(mode)
  if (shownMode !== mode) {
    setShownMode(mode)
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
      const first = (['email', 'password', 'confirm'] as Field[]).find((f) => errors[f])
      document.getElementById(`auth-${first}`)?.focus()
      return
    }

    setBusy(true)
    try {
      if (mode === 'login') await login(email.trim(), password, remember)
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
  const errId = (f: Field) => `auth-${f}-error`
  const describedBy = (...ids: (string | false)[]) => ids.filter(Boolean).join(' ') || undefined

  return (
    <div className="auth-card" id="auth">
      <h2 className="sr-only">{isRegister ? 'Create a CivicSignal account' : 'Log in to CivicSignal'}</h2>

      <div className="auth-tabs" role="tablist" aria-label="Log in or sign up">
        <button
          type="button"
          role="tab"
          aria-selected={!isRegister}
          className={!isRegister ? 'auth-tab active' : 'auth-tab'}
          onClick={() => switchMode('login')}
        >
          Login
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={isRegister}
          className={isRegister ? 'auth-tab active' : 'auth-tab'}
          onClick={() => switchMode('register')}
        >
          Sign Up
        </button>
      </div>

      <form onSubmit={handleSubmit} className="auth-form" noValidate aria-busy={busy}>
        <div className="field">
          <label htmlFor="auth-email" className="sr-only">
            Email address
          </label>
          <div className="input-wrap">
            <MailIcon />
            <input
              id="auth-email"
              type="email"
              inputMode="email"
              autoComplete="email"
              value={email}
              onChange={(e) => {
                setEmail(e.target.value)
                clearError('email')
              }}
              placeholder="Email Address"
              aria-invalid={!!fieldErrors.email}
              aria-describedby={describedBy(!!fieldErrors.email && errId('email'))}
            />
          </div>
          {fieldErrors.email && (
            <p className="field-error" id={errId('email')}>
              {fieldErrors.email}
            </p>
          )}
        </div>

        <div className="field">
          <label htmlFor="auth-password" className="sr-only">
            Password
          </label>
          <div className="input-wrap">
            <LockIcon />
            <input
              id="auth-password"
              type={showPassword ? 'text' : 'password'}
              autoComplete={isRegister ? 'new-password' : 'current-password'}
              value={password}
              onChange={(e) => {
                setPassword(e.target.value)
                clearError('password')
              }}
              placeholder={isRegister ? 'Password (at least 8 characters)' : 'Password'}
              aria-invalid={!!fieldErrors.password}
              aria-describedby={describedBy(!!fieldErrors.password && errId('password'), isRegister && 'auth-rules')}
            />
            <button
              type="button"
              className="eye-btn"
              onClick={() => setShowPassword((v) => !v)}
              aria-label={showPassword ? 'Hide password' : 'Show password'}
              aria-pressed={showPassword}
            >
              <EyeIcon off={!showPassword} />
            </button>
          </div>
          {fieldErrors.password && (
            <p className="field-error" id={errId('password')}>
              {fieldErrors.password}
            </p>
          )}
          {isRegister && (
            <ul className="pw-rules" id="auth-rules">
              <li className={pwLongEnough ? 'ok' : ''}>
                <span aria-hidden="true">{pwLongEnough ? '✓' : '•'}</span> At least {MIN_PASSWORD} characters
              </li>
              <li>
                <span aria-hidden="true">•</span> Don’t reuse your college or email password
              </li>
            </ul>
          )}
        </div>

        {isRegister && (
          <div className="field">
            <label htmlFor="auth-confirm" className="sr-only">
              Confirm password
            </label>
            <div className="input-wrap">
              <LockIcon />
              <input
                id="auth-confirm"
                type={showPassword ? 'text' : 'password'}
                autoComplete="new-password"
                value={confirm}
                onChange={(e) => {
                  setConfirm(e.target.value)
                  clearError('confirm')
                }}
                placeholder="Confirm Password"
                aria-invalid={!!fieldErrors.confirm}
                aria-describedby={describedBy(!!fieldErrors.confirm && errId('confirm'))}
              />
            </div>
            {fieldErrors.confirm && (
              <p className="field-error" id={errId('confirm')}>
                {fieldErrors.confirm}
              </p>
            )}
          </div>
        )}

        {!isRegister && (
          <div className="auth-row">
            <label className="check">
              <input type="checkbox" checked={remember} onChange={(e) => setRemember(e.target.checked)} />
              Remember me
            </label>
            <button
              type="button"
              className="text-link coral"
              aria-expanded={showForgot}
              aria-controls="auth-forgot"
              onClick={() => setShowForgot((v) => !v)}
            >
              Forgot Password?
            </button>
          </div>
        )}

        {!isRegister && showForgot && (
          <p className="info-box" id="auth-forgot" role="note">
            Password reset is not available yet. Please contact your campus administrator for assistance.
          </p>
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

        <button type="submit" className="btn-outline submit-btn" disabled={busy}>
          {busy && <span className="spinner" aria-hidden="true" />}
          {busy ? (isRegister ? 'Creating your account…' : 'Logging in…') : isRegister ? 'Create Account' : 'Login'}
        </button>

        {isRegister && (
          <p className="hint">Sign-up creates a student account. Supervisor accounts are created by the administrator.</p>
        )}
      </form>
    </div>
  )
}
