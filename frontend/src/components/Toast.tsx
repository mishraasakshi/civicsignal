import { useEffect } from 'react'

interface Props {
  message: string
  onClose: () => void
}

/** A small success message in the corner that disappears by itself after a few seconds. */
export function Toast({ message, onClose }: Props) {
  useEffect(() => {
    const timer = window.setTimeout(onClose, 5000)
    return () => window.clearTimeout(timer)
  }, [message, onClose])

  return (
    <div className="toast" role="status" aria-live="polite">
      <span aria-hidden="true">✅</span>
      <span>{message}</span>
      <button type="button" className="toast-close" onClick={onClose} aria-label="Dismiss message">
        ×
      </button>
    </div>
  )
}
