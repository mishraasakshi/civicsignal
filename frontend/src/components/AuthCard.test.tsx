import { act, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { useState } from 'react'
import { describe, expect, it, vi } from 'vitest'
import { ApiError } from '../api'
import { AuthContext, type AuthState } from '../auth/context'
import { AuthCard, type Mode } from './AuthCard'

/** Render the card with fake login/register functions (no backend needed). */
function setup(overrides: Partial<AuthState> = {}, startMode: Mode = 'login') {
  const auth: AuthState = {
    user: null,
    loading: false,
    login: vi.fn().mockResolvedValue(undefined),
    register: vi.fn().mockResolvedValue(undefined),
    logout: vi.fn().mockResolvedValue(undefined),
    notice: null,
    clearNotice: vi.fn(),
    ...overrides,
  }
  function Harness() {
    const [mode, setMode] = useState<Mode>(startMode)
    return (
      <AuthContext value={auth}>
        <AuthCard mode={mode} onModeChange={setMode} />
      </AuthContext>
    )
  }
  render(<Harness />)
  return { auth, user: userEvent.setup() }
}

const email = () => screen.getByLabelText('Email address')
const password = () => screen.getByLabelText('Password')
const submit = (name: RegExp) => screen.getByRole('button', { name })

describe('AuthCard - login', () => {
  it('empty form: shows both field errors and does not call the server', async () => {
    const { auth, user } = setup()
    await user.click(submit(/^login$/i))
    expect(screen.getByText('Please enter your email.')).toBeTruthy()
    expect(screen.getByText('Please enter your password.')).toBeTruthy()
    expect(auth.login).not.toHaveBeenCalled()
    expect(document.activeElement).toBe(email()) // cursor moved to the first problem
  })

  it('rejects a badly formatted email', async () => {
    const { auth, user } = setup()
    await user.type(email(), 'not-an-email')
    await user.type(password(), 'whatever1')
    await user.click(submit(/^login$/i))
    expect(screen.getByText(/doesn’t look like an email/)).toBeTruthy()
    expect(auth.login).not.toHaveBeenCalled()
  })

  it('sends trimmed email, password and the Remember me choice', async () => {
    const { auth, user } = setup()
    await user.type(email(), '  student@x.co ')
    await user.type(password(), 'secret-pass-1')
    await user.click(screen.getByLabelText('Remember me'))
    await user.click(submit(/^login$/i))
    expect(auth.login).toHaveBeenCalledWith('student@x.co', 'secret-pass-1', true)
  })

  it('Remember me is off unless ticked', async () => {
    const { auth, user } = setup()
    await user.type(email(), 'student@x.co')
    await user.type(password(), 'secret-pass-1')
    await user.click(submit(/^login$/i))
    expect(auth.login).toHaveBeenCalledWith('student@x.co', 'secret-pass-1', false)
  })

  it('wrong password (401) shows a clear message', async () => {
    const { user } = setup({ login: vi.fn().mockRejectedValue(new ApiError(401, 'UNAUTHORIZED', 'wrong')) })
    await user.type(email(), 'student@x.co')
    await user.type(password(), 'wrong-pass-1')
    await user.click(submit(/^login$/i))
    expect((await screen.findByRole('alert')).textContent).toContain('Wrong email or password')
  })

  it('locked account (429) shows the server’s wait time', async () => {
    const message = 'too many failed login attempts for this account. Please try again in about 15 minutes.'
    const { user } = setup({ login: vi.fn().mockRejectedValue(new ApiError(429, 'TOO_MANY_REQUESTS', message)) })
    await user.type(email(), 'student@x.co')
    await user.type(password(), 'guess-pass-1')
    await user.click(submit(/^login$/i))
    expect((await screen.findByRole('alert')).textContent?.trim()).toBe(
      'Too many failed login attempts for this account. Please try again in about 15 minutes.',
    )
  })

  it('while waiting: shows a loading label and ignores a second click', async () => {
    let finish: () => void = () => {}
    const login = vi.fn(() => new Promise<void>((resolve) => (finish = resolve)))
    const { user } = setup({ login })
    await user.type(email(), 'student@x.co')
    await user.type(password(), 'secret-pass-1')
    await user.click(submit(/^login$/i))
    const busy = screen.getByRole('button', { name: /logging in/i }) as HTMLButtonElement
    expect(busy.disabled).toBe(true)
    await user.click(busy)
    expect(login).toHaveBeenCalledTimes(1)
    await act(async () => finish())
  })

  it('Show password reveals what was typed', async () => {
    const { user } = setup()
    expect(password().getAttribute('type')).toBe('password')
    await user.click(screen.getByRole('button', { name: 'Show password' }))
    expect(password().getAttribute('type')).toBe('text')
  })

  it('Forgot Password? shows the honest message (no fake reset)', async () => {
    const { user } = setup()
    await user.click(screen.getByRole('button', { name: 'Forgot Password?' }))
    expect(screen.getByRole('note').textContent).toBe(
      'Password reset is not available yet. Please contact your campus administrator for assistance.',
    )
  })
})

describe('AuthCard - sign up', () => {
  it('switching tabs shows the sign-up form', async () => {
    const { user } = setup()
    await user.click(screen.getByRole('tab', { name: 'Sign Up' }))
    expect(screen.getByLabelText('Confirm password')).toBeTruthy()
    expect(screen.getByRole('button', { name: 'Create Account' })).toBeTruthy()
  })

  it('password must be at least 8 characters, and both passwords must match', async () => {
    const { auth, user } = setup({}, 'register')
    await user.type(email(), 'new@x.co')
    await user.type(password(), 'short')
    await user.type(screen.getByLabelText('Confirm password'), 'other')
    await user.click(submit(/create account/i))
    expect(screen.getByText('Use at least 8 characters.')).toBeTruthy()
    expect(screen.getByText('The passwords don’t match.')).toBeTruthy()
    expect(auth.register).not.toHaveBeenCalled()
  })

  it('valid sign-up calls register', async () => {
    const { auth, user } = setup({}, 'register')
    await user.type(email(), 'new@x.co')
    await user.type(password(), 'long-enough-1')
    await user.type(screen.getByLabelText('Confirm password'), 'long-enough-1')
    await user.click(submit(/create account/i))
    expect(auth.register).toHaveBeenCalledWith('new@x.co', 'long-enough-1')
  })

  it('already registered (409) offers a way to log in instead', async () => {
    const { user } = setup(
      { register: vi.fn().mockRejectedValue(new ApiError(409, 'CONFLICT', 'email already registered')) },
      'register',
    )
    await user.type(email(), 'taken@x.co')
    await user.type(password(), 'long-enough-1')
    await user.type(screen.getByLabelText('Confirm password'), 'long-enough-1')
    await user.click(submit(/create account/i))
    expect((await screen.findByRole('alert')).textContent).toContain('already registered')
    await user.click(screen.getByRole('button', { name: /log in instead/i }))
    expect(screen.getByRole('tab', { name: 'Login' }).getAttribute('aria-selected')).toBe('true')
  })
})
