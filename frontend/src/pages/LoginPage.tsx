import { useEffect, useState, type MouseEvent } from 'react'
import { AuthCard, type Mode } from '../components/AuthCard'
import { Logo } from '../components/Logo'
import { PolicyDialog, type Policy } from '../components/PolicyDialog'

/** Landing page for visitors who are not logged in: header, hero with the login card, how it works, footer. */
export function LoginPage() {
  const [mode, setMode] = useState<Mode>(() => (window.location.hash === '#signup' ? 'register' : 'login'))
  const [policy, setPolicy] = useState<Policy | null>(null)
  const [announcement, setAnnouncement] = useState('')

  // After logging in this page closes: remove #signin / #signup from the address bar
  useEffect(() => {
    return () => {
      if (window.location.hash) window.history.replaceState(null, '', window.location.pathname)
    }
  }, [])

  // "Sign in" / "Get started" / footer links: open the card in the right mode and put the cursor in it
  function openAuth(next: Mode) {
    return (e: MouseEvent) => {
      e.preventDefault()
      setMode(next)
      window.history.replaceState(null, '', next === 'register' ? '#signup' : '#signin')
      document.getElementById('auth')?.scrollIntoView({ behavior: 'smooth', block: 'center' })
      window.setTimeout(() => document.getElementById('auth-email')?.focus({ preventScroll: true }), 300)
      setAnnouncement(next === 'register' ? 'Sign-up form shown.' : 'Sign-in form shown.')
    }
  }

  function openPolicy(which: Policy) {
    return (e: MouseEvent) => {
      e.preventDefault()
      setPolicy(which)
    }
  }

  return (
    <div className="landing">
      <div className="ambient" aria-hidden="true">
        <span className="glow glow-1" />
        <span className="glow glow-2" />
        <span className="glow glow-3" />
      </div>

      {/* screen readers hear short updates here (e.g. "Sign-up form shown.") */}
      <div className="sr-only" aria-live="polite" role="status">
        {announcement}
      </div>

      <header className="site-header">
        <a href="#top" className="brand header-brand" aria-label="CivicSignal home">
          <Logo size={30} />
          <span>
            CivicSignal <span className="brand-sub">Campus</span>
          </span>
        </a>

        <nav className="site-nav" aria-label="Main">
          <a href="#top" aria-current="page">
            Home
          </a>
          <a href="#how-it-works">How it works</a>
        </nav>

        <div className="header-actions">
          <a href="#signin" className="btn-ghost" onClick={openAuth('login')}>
            Sign in
          </a>
          <a href="#signup" className="btn-cta" onClick={openAuth('register')}>
            Get started
          </a>
        </div>
      </header>

      <main id="top">
        <section className="hero" aria-labelledby="hero-title">
          <div className="hero-copy">
            <span className="pill">
              <span className="pill-dot" aria-hidden="true" />
              Powered by multilingual AI
            </span>

            <h1 id="hero-title" className="hero-title">
              <span className="hero-line">Your campus. Your voice.</span>
              <span className="hero-line hero-accent">Real problems. Real action.</span>
            </h1>

            <p className="hero-sub">
              Every campus has problems. Make sure yours don’t go unheard. Share what’s wrong, and let CivicSignal
              connect your concern to the right team.
            </p>

            <ul className="chips" aria-label="Highlights">
              <li>Sorted in seconds</li>
              <li>English · Hindi · Hinglish</li>
              <li>Anonymous to staff</li>
            </ul>

          </div>

          <div className="hero-panel">
            <AuthCard mode={mode} onModeChange={setMode} />
          </div>
          <figure className="demo-card showcase">
            <figcaption className="demo-label">Example complaint</figcaption>
            <blockquote className="demo-text">“B block geyser kharab hai, garam paani nahi aa raha”</blockquote>
            <div className="demo-result">
              <span className="demo-chip">Water &amp; Plumbing</span>
              <span className="demo-arrow">AI sorted · Assigned to maintenance</span>
            </div>
            <ol className="demo-steps" aria-label="Status">
              <li className="done">Submitted</li>
              <li className="done current">Assigned</li>
              <li>In Progress</li>
              <li>Resolved</li>
            </ol>
          </figure>
        </section>

        <section id="how-it-works" className="how" aria-labelledby="how-title">
          <h2 id="how-title">How it works</h2>
          <ol className="how-grid">
            <li className="how-card">
              <span className="feature-icon" aria-hidden="true">
                <svg viewBox="0 0 24 24"><path d="M4 5h16v11H8l-4 4z" /></svg>
              </span>
              <h3>Write it your way</h3>
              <p>Describe the problem in English, Hindi or Hinglish. Add where it is and how urgent it feels.</p>
            </li>
            <li className="how-card">
              <span className="feature-icon" aria-hidden="true">
                <svg viewBox="0 0 24 24"><path d="M12 3l2.2 5.8L20 11l-5.8 2.2L12 19l-2.2-5.8L4 11l5.8-2.2z" /></svg>
              </span>
              <h3>Sorted instantly</h3>
              <p>AI categorises the complaint. If it isn’t sure, a supervisor checks it before anything happens.</p>
            </li>
            <li className="how-card">
              <span className="feature-icon" aria-hidden="true">
                <svg viewBox="0 0 24 24"><path d="M4 12l5 5L20 6" /></svg>
              </span>
              <h3>Tracked until fixed</h3>
              <p>Follow every step: Submitted → Assigned → In Progress → Resolved.</p>
            </li>
          </ol>
        </section>
      </main>

      <footer className="site-footer">
        <div className="footer-grid">
          <div className="footer-brand">
            <a href="#top" className="brand" aria-label="CivicSignal home">
              <Logo size={28} />
              <span>CivicSignal</span>
            </a>
            <p>
              CivicSignal turns student complaints into clear, sorted reports for the people who fix them. Powered by
              a multilingual AI model.
            </p>
          </div>

          <nav aria-label="Product">
            <h3>Product</h3>
            <ul>
              <li>
                <a href="#signup" onClick={openAuth('register')}>
                  Report a problem
                </a>
              </li>
              <li>
                <a href="#how-it-works">How it works</a>
              </li>
            </ul>
          </nav>

          <nav aria-label="Account">
            <h3>Account</h3>
            <ul>
              <li>
                <a href="#signin" onClick={openAuth('login')}>
                  Sign in
                </a>
              </li>
              <li>
                <a href="#signup" onClick={openAuth('register')}>
                  Create an account
                </a>
              </li>
            </ul>
          </nav>

          <nav aria-label="Legal">
            <h3>Legal</h3>
            <ul>
              <li>
                <a href="#privacy" onClick={openPolicy('privacy')}>
                  Privacy Policy
                </a>
              </li>
              <li>
                <a href="#terms" onClick={openPolicy('terms')}>
                  Terms of Service
                </a>
              </li>
            </ul>
          </nav>
        </div>

        <div className="footer-bottom">
          <span>© 2026 CivicSignal. Built as a student project.</span>
          <span>Not an emergency service: contact campus security for emergencies.</span>
        </div>
      </footer>

      <PolicyDialog policy={policy} onClose={() => setPolicy(null)} />
    </div>
  )
}
