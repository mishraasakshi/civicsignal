import { createContext, useContext } from 'react'
import type { User } from '../api'

export interface AuthState {
  user: User | null
  loading: boolean // true while we check a saved login on page load
  login: (email: string, password: string, remember?: boolean) => Promise<void>
  register: (email: string, password: string) => Promise<void>
  logout: () => Promise<void>
  notice: string | null // short success message shown after login / sign-up
  clearNotice: () => void
}

export const AuthContext = createContext<AuthState | null>(null)

/** Use in any component: const { user, logout } = useAuth() */
export function useAuth(): AuthState {
  const auth = useContext(AuthContext)
  if (!auth) throw new Error('useAuth must be used inside <AuthProvider>')
  return auth
}
