import { useEffect, useState } from 'react'
import { ApiError, listComplaints, type Category, type Complaint, type ComplaintFilters, type Status } from '../api'
import { RepeatedProblems } from '../components/RepeatedProblems'
import { SupervisorRow } from '../components/SupervisorRow'
import { CATEGORIES, CATEGORY_LABELS, STATUSES } from '../labels'

type View = 'review' | 'all' | 'groups'

export function SupervisorDashboard() {
  const [view, setView] = useState<View>('review')
  const [category, setCategory] = useState<Category | ''>('')
  const [status, setStatus] = useState<Status | ''>('')

  const [items, setItems] = useState<Complaint[]>([])
  const [total, setTotal] = useState(0)
  const [reviewCount, setReviewCount] = useState<number | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Reload the list whenever a filter changes
  useEffect(() => {
    if (view === 'groups') return // that tab loads its own data
    let cancelled = false // ignore old answers if the filters changed again meanwhile
    const filters: ComplaintFilters = { limit: 100 }
    if (view === 'review') filters.needs_review = true
    if (category) filters.category = category
    if (status) filters.status = status

    listComplaints(filters)
      .then((res) => {
        if (cancelled) return
        setItems(res.items)
        setTotal(res.total)
        setError(null)
      })
      .catch((err) => {
        if (!cancelled) setError(err instanceof ApiError ? err.message : 'Could not load complaints.')
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [view, category, status])

  // How many complaints are waiting for review (for the tab badge)
  useEffect(() => {
    listComplaints({ needs_review: true, limit: 1 })
      .then((res) => {
        setReviewCount(res.total)
        if (res.total === 0) setView((v) => (v === 'review' ? 'all' : v)) // nothing to review: open the full list
      })
      .catch(() => setReviewCount(null))
  }, [])

  function changeView(next: View) {
    if (next !== 'groups') setLoading(true)
    setView(next)
  }

  function handleUpdated(updated: Complaint) {
    const before = items.find((c) => c.id === updated.id)
    setItems((prev) => prev.map((c) => (c.id === updated.id ? updated : c)))
    if (before?.needs_review && !updated.needs_review) {
      setReviewCount((n) => (n === null ? n : Math.max(0, n - 1)))
    }
  }

  return (
    <div>
      <div className="dash-head">
        <h1>Supervisor dashboard</h1>
        <div className="tabs view-tabs" role="tablist">
          <button
            type="button"
            role="tab"
            aria-selected={view === 'review'}
            className={view === 'review' ? 'tab active' : 'tab'}
            onClick={() => changeView('review')}
          >
            Needs review {reviewCount !== null && <span className="count">{reviewCount}</span>}
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={view === 'all'}
            className={view === 'all' ? 'tab active' : 'tab'}
            onClick={() => changeView('all')}
          >
            All complaints
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={view === 'groups'}
            className={view === 'groups' ? 'tab active' : 'tab'}
            onClick={() => changeView('groups')}
          >
            🔁 Repeated problems
          </button>
        </div>
      </div>

      {view === 'groups' ? (
        <RepeatedProblems />
      ) : (
        <>

      <div className="filters">
        <span className="filters-title">🔍 Show only:</span>
        <label className="inline">
          Category
          <select
            value={category}
            onChange={(e) => {
              setLoading(true)
              setCategory(e.target.value as Category | '')
            }}
          >
            <option value="">All</option>
            {CATEGORIES.map((c) => (
              <option key={c} value={c}>
                {CATEGORY_LABELS[c]}
              </option>
            ))}
          </select>
        </label>
        <label className="inline">
          Status
          <select
            value={status}
            onChange={(e) => {
              setLoading(true)
              setStatus(e.target.value as Status | '')
            }}
          >
            <option value="">All</option>
            {STATUSES.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </label>
        <span className="muted small">{loading ? 'Loading…' : `${total} complaint${total === 1 ? '' : 's'}`}</span>
      </div>

      <p className="muted small">
        {view === 'review'
          ? 'The AI was less than 50% sure about these. Fix the category, or click “AI is right” to confirm it.'
          : 'To change a complaint, use the buttons on its card.'}
      </p>

      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
      {!loading && !error && items.length === 0 && (
        <p className="muted">
          {view === 'review' && !category && !status
            ? 'Nothing to review. 🎉 Open “All complaints” to manage the rest.'
            : 'No complaints match. Set the filters back to “All”.'}
        </p>
      )}

      <div className="list">
        {items.map((c) => (
          <SupervisorRow key={c.id} complaint={c} onUpdated={handleUpdated} />
        ))}
      </div>
        </>
      )}
    </div>
  )
}
