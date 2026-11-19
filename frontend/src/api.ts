// All calls to the CivicSignal backend go through this file.

// In development this is '' (Vite forwards /api to localhost:8000).
// When deployed, set VITE_API_URL to the backend's address.
const BASE_URL = import.meta.env.VITE_API_URL ?? ''
const TOKEN_KEY = 'civicsignal_token'
export const SESSION_EXPIRED_EVENT = 'civicsignal:session-expired'

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

  // Saved login expired or became invalid: forget it and tell the app to show the login page
  if (response.status === 401 && token) {
    tokenStore.clear()
    window.dispatchEvent(new Event(SESSION_EXPIRED_EVENT))
  }

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

// ---- Complaints ----

export type Category =
  | 'water_plumbing'
  | 'electrical'
  | 'cleanliness'
  | 'internet_wifi'
  | 'furniture'
  | 'mess_food'
  | 'security'
  | 'other'

export type Status =
  | 'Submitted'
  | 'Under Review'
  | 'Assigned'
  | 'In Progress'
  | 'Resolved'
  | 'Closed'
  | 'Needs More Information'

export type Urgency = 'low' | 'medium' | 'high'

export interface Complaint {
  id: number
  text: string
  location: string | null
  urgency_reported: Urgency | null
  predicted_category: Category // the AI's guess (never changes)
  confidence: number // 0..1, how sure the AI was
  needs_review: boolean // true = a supervisor should check the category
  category: Category // current category (AI guess, or a supervisor's correction)
  status: Status
  created_at: string
  updated_at: string
}

export interface ComplaintList {
  total: number
  items: Complaint[]
}

export interface NewComplaint {
  text: string
  location?: string
  urgency?: Urgency
}

export function createComplaint(body: NewComplaint): Promise<Complaint> {
  return request<Complaint>('/api/complaints', { method: 'POST', json: body })
}

export interface ComplaintFilters {
  category?: Category
  status?: Status
  needs_review?: boolean
  limit?: number
}

export function listComplaints(filters: ComplaintFilters = {}): Promise<ComplaintList> {
  const params = new URLSearchParams({ limit: String(filters.limit ?? 50) })
  if (filters.category) params.set('category', filters.category)
  if (filters.status) params.set('status', filters.status)
  if (filters.needs_review !== undefined) params.set('needs_review', String(filters.needs_review))
  return request<ComplaintList>(`/api/complaints?${params}`)
}

/** Supervisors only: correct the category and/or move the status. */
export function updateComplaint(
  id: number,
  changes: { category?: Category; status?: Status },
): Promise<Complaint> {
  return request<Complaint>(`/api/complaints/${id}`, { method: 'PATCH', json: changes })
}
