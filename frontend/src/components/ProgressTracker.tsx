import { STAGES } from '../labels'

interface Props {
  current: number // index of the current stage (0-3)
  dates?: (string | null)[] // optional date under each stage
  allDone?: boolean // the last stage is finished (Resolved/Closed), not just "current"
}

/** Four-stage tracker: done = sage check, current = coral ring, pending = empty ring. */
export function ProgressTracker({ current, dates = [], allDone = false }: Props) {
  return (
    <ol className="tracker" aria-label="Complaint progress">
      {STAGES.map((stage, i) => {
        const state = i < current || (allDone && i === current) ? 'done' : i === current ? 'current' : 'pending'
        return (
          <li key={stage} className={`tracker-step ${state}`} aria-current={state === 'current' ? 'step' : undefined}>
            <span className="tracker-dot" aria-hidden="true">
              {state === 'done' && (
                <svg viewBox="0 0 16 16">
                  <path d="M4 8.5l2.6 2.6L12 5.5" />
                </svg>
              )}
            </span>
            <span className="tracker-label">
              {stage}
              <span className="sr-only">{state === 'done' ? ' (done)' : state === 'current' ? ' (current)' : ' (pending)'}</span>
            </span>
            {dates[i] && <span className="tracker-date">{dates[i]}</span>}
          </li>
        )
      })}
    </ol>
  )
}
