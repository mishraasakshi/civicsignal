import { useEffect, useState } from 'react'
import { ApiError, listComplaints, type Complaint } from '../api'
import { ComplaintCard } from '../components/ComplaintCard'
import { ComplaintForm } from '../components/ComplaintForm'
import { CATEGORY_LABELS } from '../labels'

export function StudentHome() {
  const [complaints, setComplaints] = useState<Complaint[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [justCreated, setJustCreated] = useState<Complaint | null>(null)

  // Load "my complaints" once when the page opens
  useEffect(() => {
    listComplaints()
      .then((res) => setComplaints(res.items))
      .catch((err) => setError(err instanceof ApiError ? err.message : 'Could not load complaints.'))
      .finally(() => setLoading(false))
  }, [])

  function handleCreated(created: Complaint) {
    setComplaints((prev) => [created, ...prev]) // show it at the top straight away
    setJustCreated(created)
  }

  return (
    <div className="student-grid">
      <section>
        <ComplaintForm onCreated={handleCreated} />

        {justCreated && (
          <div className="notice" role="status">
            ✅ Complaint #{justCreated.id} submitted. Sorted as{' '}
            <strong>{CATEGORY_LABELS[justCreated.category]}</strong>
            {justCreated.needs_review
              ? '. The AI was not sure, so a supervisor will double-check it.'
              : ` (${Math.round(justCreated.confidence * 100)}% sure).`}
          </div>
        )}
      </section>

      <section>
        <h2>My complaints {!loading && <span className="muted">({complaints.length})</span>}</h2>
        {loading && <p className="muted">Loading…</p>}
        {error && (
          <p className="error" role="alert">
            {error}
          </p>
        )}
        {!loading && !error && complaints.length === 0 && (
          <p className="muted">No complaints yet. Report your first problem on the left.</p>
        )}
        <div className="list">
          {complaints.map((c) => (
            <ComplaintCard key={c.id} complaint={c} highlight={c.id === justCreated?.id} />
          ))}
        </div>
      </section>
    </div>
  )
}
