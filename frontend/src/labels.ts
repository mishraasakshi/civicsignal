// Human-friendly names for the values the backend uses.
import type { Category, Status, Urgency } from './api'

export const CATEGORY_LABELS: Record<Category, string> = {
  water_plumbing: 'Water & plumbing',
  electrical: 'Electrical',
  cleanliness: 'Cleanliness',
  internet_wifi: 'Internet / Wi-Fi',
  furniture: 'Furniture',
  mess_food: 'Mess & food',
  security: 'Security',
  other: 'Other',
}

export const URGENCY_LABELS: Record<Urgency, string> = {
  low: 'Low',
  medium: 'Medium',
  high: 'High',
}

/** Colour group for each status badge (see .status-* in index.css). */
export const STATUS_TONE: Record<Status, 'new' | 'active' | 'done' | 'attention'> = {
  Submitted: 'new',
  'Under Review': 'new',
  'Needs More Information': 'attention',
  Assigned: 'active',
  'In Progress': 'active',
  Resolved: 'done',
  Closed: 'done',
}

/** Short explanation a student sees under each status. */
export const STATUS_HELP: Record<Status, string> = {
  Submitted: 'Received. Waiting for a supervisor.',
  'Under Review': 'A supervisor is looking at it.',
  'Needs More Information': 'The supervisor needs more details.',
  Assigned: 'Sent to the team that fixes it.',
  'In Progress': 'The team is working on it.',
  Resolved: 'Marked as fixed.',
  Closed: 'Finished.',
}

export function formatDate(iso: string): string {
  return new Date(iso).toLocaleString(undefined, {
    day: 'numeric',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export const CATEGORIES = Object.keys(CATEGORY_LABELS) as Category[]

export const STATUSES: Status[] = [
  'Submitted',
  'Under Review',
  'Needs More Information',
  'Assigned',
  'In Progress',
  'Resolved',
  'Closed',
]

/**
 * Which status a complaint can move to next.
 * Copy of backend/app/services/workflow.py - the backend still checks every move (409 if not allowed),
 * this copy only decides which buttons to show.
 */
export const NEXT_STATUSES: Record<Status, Status[]> = {
  Submitted: ['Under Review', 'Assigned', 'Needs More Information', 'Closed'],
  'Under Review': ['Assigned', 'Needs More Information', 'Closed'],
  'Needs More Information': ['Under Review', 'Closed'],
  Assigned: ['In Progress', 'Closed'],
  'In Progress': ['Resolved', 'Assigned'],
  Resolved: ['Closed', 'In Progress'],
  Closed: [],
}
