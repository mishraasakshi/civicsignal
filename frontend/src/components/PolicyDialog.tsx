import { useEffect, useRef } from 'react'

export type Policy = 'privacy' | 'terms'

interface Props {
  policy: Policy | null // which one to show; null = closed
  onClose: () => void
}

/** Privacy Policy and Terms of Service in a pop-up (native <dialog>: Esc closes it, focus stays inside). */
export function PolicyDialog({ policy, onClose }: Props) {
  const ref = useRef<HTMLDialogElement>(null)

  useEffect(() => {
    const dialog = ref.current
    if (!dialog) return
    if (policy && !dialog.open) {
      dialog.showModal()
      dialog.scrollTop = 0
      dialog.querySelector<HTMLElement>('h2')?.focus() // start reading at the title, not at the Close button
    }
    if (!policy && dialog.open) dialog.close()
  }, [policy])

  return (
    <dialog
      ref={ref}
      className="policy-dialog"
      onClose={onClose}
      onClick={(e) => e.target === ref.current && onClose()} // click outside the box closes it
      aria-labelledby="policy-title"
    >
      <div className="policy-body">
        {policy === 'terms' ? <Terms /> : <Privacy />}
        <p className="policy-note">
          Pilot version, written for the CivicSignal student project. It should be reviewed by the university before
          a full launch.
        </p>
        <button type="button" className="primary policy-close" onClick={onClose}>
          Close
        </button>
      </div>
    </dialog>
  )
}

function Privacy() {
  return (
    <>
      <h2 id="policy-title" tabIndex={-1}>Privacy Policy</h2>
      <h3>What we store</h3>
      <ul>
        <li>Your email address and a scrambled (bcrypt-hashed) version of your password. We never store the password itself.</li>
        <li>The complaints you submit: the text, the location and urgency you chose, the category the AI picked and the status.</li>
        <li>Which account submitted each complaint, so that you can see your own complaints.</li>
      </ul>
      <h3>Who can see what</h3>
      <ul>
        <li>Students see only their own complaints.</li>
        <li>Supervisors see complaint text and details, but the app never shows them who wrote a complaint.</li>
      </ul>
      <h3>AI processing</h3>
      <ul>
        <li>The category is chosen by an AI model running on the CivicSignal server.</li>
        <li>
          To summarise repeated problems, complaint texts may be sent to an external AI service (Groq). Your email
          and account are never sent.
        </li>
      </ul>
      <h3>On your device</h3>
      <ul>
        <li>After you log in, a login token is kept in your browser so you stay logged in. It expires after 24 hours, and logging out removes it.</li>
      </ul>
      <h3>Please don't include</h3>
      <ul>
        <li>Names, phone numbers or room numbers of other people in your complaints.</li>
      </ul>
    </>
  )
}

function Terms() {
  return (
    <>
      <h2 id="policy-title" tabIndex={-1}>Terms of Service</h2>
      <ul>
        <li>CivicSignal is a pilot project for reporting campus facility problems. It is not an emergency service: for fire, medical or security emergencies, contact campus security directly.</li>
        <li>Describe real problems honestly. Do not submit false, abusive or offensive complaints.</li>
        <li>Do not include other people's personal details (names, phone numbers, room numbers).</li>
        <li>Keep your password private. You are responsible for complaints sent from your account.</li>
        <li>The AI can make mistakes. Supervisors check and correct categories, and a complaint's status is updated by staff, not by the AI.</li>
        <li>Accounts used to misuse the service may be removed.</li>
      </ul>
    </>
  )
}
