import { useState } from 'react'
import { ApiError, updateComplaint, type Category, type Complaint, type Status } from '../api'
import {
  CATEGORIES,
  CATEGORY_LABELS,
  NEXT_STATUSES,
  STATUS_TONE,
  URGENCY_LABELS,
  formatDate,
} from '../labels'

interface Props {
  complaint: Complaint
  onUpdated: (complaint: Complaint) => void
}

/** One complaint in the supervisor dashboard, with buttons to fix the category and move the status. */
export function SupervisorRow({ complaint: c, onUpdated }: Props) {
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function save(changes: { category?: Category; status?: Status }) {
    setBusy(true)
    setError(null)
    try {
      onUpdated(await updateComplaint(c.id, changes))
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Could not save. Please try again.')
    } finally {
      setBusy(false)
    }
  }

  const corrected = c.category !== c.predicted_category
  const next = NEXT_STATUSES[c.status]

  return (
    <article className={c.needs_review ? 'card complaint review' : 'card complaint'}>
      <header className="complaint-head">
        <span className={`status status-${STATUS_TONE[c.status]}`}>{c.status}</span>
        <span className="muted small">
          #{c.id} · {formatDate(c.created_at)}
        </span>
      </header>

      <p className="complaint-text">{c.text}</p>

      <div className="tags">
        {c.location && <span className="tag">{c.location}</span>}
        {c.urgency_reported && <span className="tag">Urgency: {URGENCY_LABELS[c.urgency_reported]}</span>}
        {c.needs_review && <span className="tag tag-warn">⚠ Needs review</span>}
      </div>

      <div className="sup-controls">
        <div className="ai-guess small">
          AI guess: <strong>{CATEGORY_LABELS[c.predicted_category]}</strong>{' '}
          <span className="muted">({Math.round(c.confidence * 100)}% sure)</span>
          {corrected && <span className="muted"> · corrected by supervisor</span>}
        </div>

        <label className="inline">
          Category
          <select
            value={c.category}
            disabled={busy}
            onChange={(e) => save({ category: e.target.value as Category })}
          >
            {CATEGORIES.map((cat) => (
              <option key={cat} value={cat}>
                {CATEGORY_LABELS[cat]}
              </option>
            ))}
          </select>
        </label>

        {c.needs_review && (
          <button type="button" className="ghost small-btn" disabled={busy} onClick={() => save({ category: c.category })}>
            ✓ AI is right
          </button>
        )}
      </div>

      {next.length > 0 ? (
        <div className="moves">
          <span className="small"><strong>Change status →</strong></span>
          {next.map((s) => (
            <button
              key={s}
              type="button"
              className={s === 'Closed' ? 'ghost small-btn' : 'ghost small-btn move'}
              disabled={busy}
              onClick={() => save({ status: s })}
            >
              {s}
            </button>
          ))}
        </div>
      ) : (
        <p className="muted small">Closed. No further changes.</p>
      )}

      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
    </article>
  )
}
