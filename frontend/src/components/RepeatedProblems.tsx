import { useEffect, useState } from 'react'
import { ApiError, fetchGroupInsights, type GroupInsights } from '../api'
import { CATEGORY_LABELS, URGENCY_LABELS, formatDate } from '../labels'

/** Groups of similar complaints found by the AI, each with a short summary and a suggested next step. */
export function RepeatedProblems() {
  const [data, setData] = useState<GroupInsights | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchGroupInsights()
      .then(setData)
      .catch((err) => setError(err instanceof ApiError ? err.message : 'Could not load repeated problems.'))
  }, [])

  if (error) {
    return (
      <p className="error" role="alert">
        {error}
      </p>
    )
  }
  if (!data) return <p className="muted">Loading…</p>

  const totalComplaints = data.groups.reduce((sum, g) => sum + g.size, 0)

  return (
    <div>
      <p className="muted small">
        {data.groups.length} problems reported by several students ({totalComplaints} complaints in total).
        Source: {data.source}, updated {formatDate(data.generated_at)}. The AI grouped similar complaints and
        wrote these summaries, so please check them before acting.
      </p>

      <div className="group-grid">
        {data.groups.map((g) => (
          <article key={g.group} className={`card group-card urgency-${g.urgency}`}>
            <header className="group-head">
              <span className="group-size" title="complaints in this group">
                {g.size}
                <small>students</small>
              </span>
              <h3>{g.title}</h3>
            </header>

            <div className="tags">
              <span className="tag">{CATEGORY_LABELS[g.category]}</span>
              <span className={`tag urgency-tag-${g.urgency}`}>Urgency: {URGENCY_LABELS[g.urgency]}</span>
            </div>

            <p className="group-summary">{g.summary}</p>

            <div className="group-action">
              <strong>Suggested next step</strong>
              <p>{g.suggested_action}</p>
            </div>
          </article>
        ))}
      </div>
    </div>
  )
}
