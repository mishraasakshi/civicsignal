import type { Complaint } from '../api'
import { ProgressTracker } from './ProgressTracker'
import { CATEGORY_LABELS, STATUS_HELP, STATUS_TONE, URGENCY_LABELS, formatDate, stageIndex } from '../labels'

interface Props {
  complaint: Complaint
  highlight?: boolean // true for the one just submitted
}

export function ComplaintCard({ complaint: c, highlight = false }: Props) {
  return (
    <article className={highlight ? 'card complaint highlight' : 'card complaint'}>
      <header className="complaint-head">
        <span className={`status status-${STATUS_TONE[c.status]}`}>{c.status}</span>
        <span className="muted small">
          #{c.id} · {formatDate(c.created_at)}
        </span>
      </header>

      <p className="complaint-text">{c.text}</p>

      <div className="tags">
        <span className="tag">{CATEGORY_LABELS[c.category]}</span>
        {c.location && <span className="tag">{c.location}</span>}
        {c.urgency_reported && <span className="tag">Urgency: {URGENCY_LABELS[c.urgency_reported]}</span>}
      </div>

      <ProgressTracker
        current={stageIndex(c.status)}
        allDone={c.status === 'Resolved' || c.status === 'Closed'}
        dates={[formatDate(c.created_at)]}
      />

      <p className="muted small">
        {STATUS_HELP[c.status]}
        {c.needs_review && ' The category will be checked by a supervisor.'}
      </p>
    </article>
  )
}
