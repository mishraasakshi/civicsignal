import { useState, type FormEvent } from 'react'
import { ApiError, createComplaint, type Complaint, type Urgency } from '../api'

const MAX_LENGTH = 2000

interface Props {
  onCreated: (complaint: Complaint) => void
}

export function ComplaintForm({ onCreated }: Props) {
  const [text, setText] = useState('')
  const [location, setLocation] = useState('')
  const [urgency, setUrgency] = useState<Urgency | ''>('')
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError(null)
    if (text.trim().length < 3) {
      setError('Please describe the problem (at least a few words).')
      return
    }

    setBusy(true)
    try {
      const created = await createComplaint({
        text: text.trim(),
        location: location.trim() || undefined,
        urgency: urgency || undefined,
      })
      setText('')
      setLocation('')
      setUrgency('')
      onCreated(created)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Could not submit. Please try again.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <form className="card form" onSubmit={handleSubmit}>
      <h2>Report a problem</h2>

      <label>
        What's wrong?
        <textarea
          rows={4}
          maxLength={MAX_LENGTH}
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="e.g. Hostel B ke washroom me 3 din se paani nahi aa raha"
          required
        />
        <span className="counter">
          {text.length}/{MAX_LENGTH} · English, Hindi or Hinglish is fine
        </span>
      </label>

      <div className="row">
        <label>
          Where? <span className="optional">(optional)</span>
          <input
            value={location}
            maxLength={200}
            onChange={(e) => setLocation(e.target.value)}
            placeholder="e.g. Hostel B, 2nd floor"
          />
        </label>

        <label>
          How urgent? <span className="optional">(optional)</span>
          <select value={urgency} onChange={(e) => setUrgency(e.target.value as Urgency | '')}>
            <option value="">Not sure</option>
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High: safety risk or many affected</option>
          </select>
        </label>
      </div>

      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}

      <button type="submit" className="primary" disabled={busy}>
        {busy ? 'Submitting… (the AI is sorting it)' : 'Submit complaint'}
      </button>
      <p className="hint">Your name is never shown with your complaint.</p>
    </form>
  )
}
