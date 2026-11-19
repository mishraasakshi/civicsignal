// All calls to the CivicSignal backend go through this file.

// In development this is '' (Vite forwards /api to localhost:8000).
// When deployed, set VITE_API_URL to the backend's address.
const BASE_URL = import.meta.env.VITE_API_URL ?? ''
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

// The login session lives in an httpOnly cookie set by the backend.
// JavaScript never sees or stores the token, so an XSS bug can't steal it.
// (Older versions kept it in localStorage - remove that copy if it is still there.)
try {
  localStorage.removeItem('civicsignal_token')
} catch {
  /* storage blocked: nothing to clean up */
}

let loggedIn = false // so a 401 is only treated as "session expired" for someone who was logged in
export function setLoggedIn(value: boolean) {
  loggedIn = value
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

  let response: Response
  try {
    response = await fetch(`${BASE_URL}${path}`, {
      method: options.method ?? 'GET',
      headers,
      body,
      credentials: 'include', // send the session cookie
    })
  } catch {
    throw new ApiError(0, 'NETWORK_ERROR', 'Cannot reach the server. Is the backend running?')
  }

  const data = response.status === 204 ? null : await response.json().catch(() => null)

  // Session expired or became invalid: tell the app to show the login page
  if (response.status === 401 && loggedIn) {
    loggedIn = false
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

/** Log in. The backend answers with an httpOnly session cookie (30 days if remember is true). */
export async function login(email: string, password: string, remember = false): Promise<void> {
  await request<unknown>('/api/auth/login', {
    method: 'POST',
    form: { username: email, password, remember: String(remember) },
  })
}

export async function logout(): Promise<void> {
  await request<null>('/api/auth/logout', { method: 'POST' })
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

// ---- Insights (supervisors only) ----

export interface GroupInsight {
  group: number
  size: number // how many complaints are in this group
  title: string
  summary: string
  category: Category
  urgency: Urgency
  suggested_action: string
}

export interface GroupInsights {
  source: string
  generated_at: string
  groups: GroupInsight[]
}

export function fetchGroupInsights(): Promise<GroupInsights> {
  return request<GroupInsights>('/api/insights/groups')
}
