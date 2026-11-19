// All calls to the CivicSignal backend go through this file.

// In development this is '' (Vite forwards /api to localhost:8000).
// When deployed, set VITE_API_URL to the backend's address.
const BASE_URL = import.meta.env.VITE_API_URL ?? ''
const TOKEN_KEY = 'civicsignal_token'

export type Role = 'reporter' | 'supervisor'

export interface User {
  id: number
  email: string
  role: Role
  created_at: string
}

/** An error from the backend, in its standard {"error": {"code", "message"}} shape. */
export class ApiError extends Error {
  status: number
  code: string

  constructor(status: number, code: string, message: string) {
    super(message)
    this.status = status
    this.code = code
  }
}

export const tokenStore = {
  get: () => localStorage.getItem(TOKEN_KEY),
  set: (token: string) => localStorage.setItem(TOKEN_KEY, token),
  clear: () => localStorage.removeItem(TOKEN_KEY),
}

interface RequestOptions {
  method?: string
  json?: unknown // sent as JSON
  form?: Record<string, string> // sent as a login form
}

export async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const headers: Record<string, string> = {}
  let body: BodyInit | undefined

  if (options.json !== undefined) {
    headers['Content-Type'] = 'application/json'
    body = JSON.stringify(options.json)
  } else if (options.form) {
    body = new URLSearchParams(options.form)
  }

  const token = tokenStore.get()
  if (token) headers['Authorization'] = `Bearer ${token}`

  let response: Response
  try {
    response = await fetch(`${BASE_URL}${path}`, { method: options.method ?? 'GET', headers, body })
  } catch {
    throw new ApiError(0, 'NETWORK_ERROR', 'Cannot reach the server. Is the backend running?')
  }

  const data = await response.json().catch(() => null)
  if (!response.ok) {
    const err = data?.error
    throw new ApiError(
      response.status,
      err?.code ?? 'HTTP_ERROR',
      err?.message ?? `Request failed (${response.status})`,
    )
  }
  return data as T
}

// ---- Auth endpoints ----

export async function login(email: string, password: string): Promise<void> {
  const res = await request<{ access_token: string }>('/api/auth/login', {
    method: 'POST',
    form: { username: email, password },
  })
  tokenStore.set(res.access_token)
}

export function register(email: string, password: string): Promise<User> {
  return request<User>('/api/auth/register', { method: 'POST', json: { email, password } })
}

export function fetchMe(): Promise<User> {
  return request<User>('/api/auth/me')
}
