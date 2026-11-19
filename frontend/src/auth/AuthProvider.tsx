import { useCallback, useEffect, useState, type ReactNode } from 'react'
import * as api from '../api'
import { AuthContext } from './context'

/** Keeps track of who is logged in and shares it with the whole app. */
export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<api.User | null>(null)
  const [loading, setLoading] = useState(true) // checking the session cookie on page load
  const [notice, setNotice] = useState<string | null>(null)

  // On page load: ask the backend whether the session cookie belongs to someone
  useEffect(() => {
    api
      .fetchMe()
      .then((me) => {
        api.setLoggedIn(true)
        setUser(me)
      })
      .catch(() => setUser(null)) // no cookie, or it expired: show the landing page
      .finally(() => setLoading(false))
  }, [])

  // If any request finds the session has expired, go back to the landing page
  useEffect(() => {
    const onExpired = () => setUser(null)
    window.addEventListener(api.SESSION_EXPIRED_EVENT, onExpired)
    return () => window.removeEventListener(api.SESSION_EXPIRED_EVENT, onExpired)
  }, [])

  async function signIn(email: string, password: string, remember: boolean) {
    await api.login(email, password, remember)
    const me = await api.fetchMe()
    api.setLoggedIn(true)
    setUser(me)
  }

  async function login(email: string, password: string, remember = false) {
    await signIn(email, password, remember)
    setNotice('Logged in successfully. Welcome back!')
  }

  async function register(email: string, password: string) {
    await api.register(email, password)
    await signIn(email, password, false) // sign up, then log straight in
    setNotice("Your account is ready and you're logged in.")
  }

  async function logout() {
    try {
      await api.logout() // backend clears the httpOnly cookie
    } finally {
      api.setLoggedIn(false)
      setUser(null)
      setNotice(null)
    }
  }

  const clearNotice = useCallback(() => setNotice(null), []) // stable, so the toast timer isn't restarted

  return (
    <AuthContext value={{ user, loading, login, register, logout, notice, clearNotice }}>{children}</AuthContext>
  )
}
