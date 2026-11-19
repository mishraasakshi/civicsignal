import { useEffect, useState, type ReactNode } from 'react'
import * as api from '../api'
import { AuthContext } from './context'

/** Keeps track of who is logged in and shares it with the whole app. */
export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<api.User | null>(null)
  // Only "loading" if there is a saved token to check
  const [loading, setLoading] = useState(() => api.tokenStore.get() !== null)

  // On page load: if a token was saved earlier, ask the backend who it belongs to
  useEffect(() => {
    if (!api.tokenStore.get()) return
    api
      .fetchMe()
      .then(setUser)
      .catch(() => api.tokenStore.clear()) // expired or invalid -> log out quietly
      .finally(() => setLoading(false))
  }, [])

  async function login(email: string, password: string) {
    await api.login(email, password)
    setUser(await api.fetchMe())
  }

  async function register(email: string, password: string) {
    await api.register(email, password)
    await login(email, password) // sign up, then log straight in
  }

  function logout() {
    api.tokenStore.clear()
    setUser(null)
  }

  return <AuthContext value={{ user, loading, login, register, logout }}>{children}</AuthContext>
}
