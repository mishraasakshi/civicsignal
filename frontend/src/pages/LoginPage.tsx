import { useEffect, useState, type MouseEvent } from 'react'
import { AuthCard, type Mode } from '../components/AuthCard'
import { CampusIllustration } from '../components/CampusIllustration'
import { Brand } from '../components/Logo'
import { PolicyDialog, type Policy } from '../components/PolicyDialog'
import { ProgressTracker } from '../components/ProgressTracker'
import { CONTACT_EMAIL } from '../config'

/** Landing page for visitors who are not logged in. */
export function LoginPage() {
  const [mode, setMode] = useState<Mode>(() => (window.location.hash === '#signup' ? 'register' : 'login'))
  const [policy, setPolicy] = useState<Policy | null>(null)
  const [announcement, setAnnouncement] = useState('')
  const [menuOpen, setMenuOpen] = useState(false)

  // After logging in this page closes: remove #signin / #signup from the address bar
  useEffect(() => {
    return () => {
      if (window.location.hash) window.history.replaceState(null, '', window.location.pathname)
    }
  }, [])

  // Close the mobile menu with Escape
  useEffect(() => {
    if (!menuOpen) return
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && setMenuOpen(false)
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [menuOpen])

  /** Open the login card in the right mode and put the cursor in it. */
  function openAuth(next: Mode, message?: string) {
    return (e: MouseEvent) => {
      e.preventDefault()
      setMenuOpen(false)
      setMode(next)
      window.history.replaceState(null, '', next === 'register' ? '#signup' : '#signin')
      document.getElementById('auth')?.scrollIntoView({ behavior: 'smooth', block: 'center' })
      window.setTimeout(() => document.getElementById('auth-email')?.focus({ preventScroll: true }), 350)
      setAnnouncement(message ?? (next === 'register' ? 'Sign-up form shown.' : 'Login form shown.'))
    }
  }

  function openDialog(which: Policy) {
    return (e: MouseEvent) => {
      e.preventDefault()
      setMenuOpen(false)
      setPolicy(which)
    }
  }

  function closeMenu() {
    setMenuOpen(false)
  }

  // Contact: a real mailto only when an address is configured, otherwise an honest note
  const contactProps = CONTACT_EMAIL
    ? { href: `mailto:${CONTACT_EMAIL}`, onClick: closeMenu }
    : { href: '#contact', onClick: openDialog('contact') }

  const navLinks = (
    <>
      <a href="#top" aria-current="page" onClick={closeMenu}>
        Home
      </a>
      <a href="#signin" onClick={openAuth('login', 'Log in to track your complaints.')}>
        Track Complaint
      </a>
      <a href="#how-it-works" onClick={closeMenu}>
        About
      </a>
      <a {...contactProps}>Contact</a>
    </>
  )

  return (
    <div className="landing" id="top">
      <div className="sr-only" aria-live="polite" role="status">
        {announcement}
      </div>

      <header className="site-header">
        <div className="site-header-inner">
          <a href="#top" className="brand-link" aria-label="CivicSignal home">
            <Brand />
          </a>

          <nav className="site-nav" aria-label="Main">
            {navLinks}
          </nav>

          <a href="#signin" className="btn-coral header-cta" onClick={openAuth('login')}>
            Login / Sign Up
          </a>

          <button
            type="button"
            className="menu-btn"
            aria-expanded={menuOpen}
            aria-controls="mobile-menu"
            aria-label={menuOpen ? 'Close menu' : 'Open menu'}
            onClick={() => setMenuOpen((v) => !v)}
          >
            <svg viewBox="0 0 24 24" aria-hidden="true">
              {menuOpen ? <path d="M6 6l12 12M18 6L6 18" /> : <path d="M4 7h16M4 12h16M4 17h16" />}
            </svg>
          </button>
        </div>

        {menuOpen && (
          <nav id="mobile-menu" className="mobile-menu" aria-label="Main (mobile)">
            {navLinks}
            <a href="#signin" className="btn-coral" onClick={openAuth('login')}>
              Login / Sign Up
            </a>
          </nav>
        )}
      </header>

      <main>
        <section className="hero" aria-labelledby="hero-title">
          <CampusIllustration />

          <div className="hero-copy">
            <h1 id="hero-title" className="hero-title">
              <span className="hero-line">The little things</span>
              <span className="hero-line">that go wrong</span>
              <span className="hero-line hero-accent">shouldn’t stay that way.</span>
            </h1>
            <p className="hero-sub">Report. Track. Resolve — for a more responsive campus.</p>
            <div className="hero-actions">
              <a
                href="#signin"
                className="btn-mustard"
                onClick={openAuth('login', 'Log in or sign up to report a complaint.')}
              >
                Report a Complaint <span aria-hidden="true">→</span>
              </a>
              <a href="#how-it-works" className="btn-text">
                Learn More
              </a>
            </div>
          </div>

          <div className="hero-panel">
            <AuthCard mode={mode} onModeChange={setMode} />
          </div>

          <figure className="report-card" aria-label="Example complaint">
            <div className="report-main">
              <div className="report-head">
                <svg viewBox="0 0 20 20" className="report-icon" aria-hidden="true">
                  <path d="M5 2.5h7l3.5 3.5v11.5H5z" />
                  <path d="M12 2.5V6h3.5M7.5 10h6M7.5 13h6" />
                </svg>
                <span className="report-title">Report #CS-2025-1047</span>
                <span className="pill-sage">Assigned</span>
                <span className="example-tag">Example</span>
              </div>
              <p className="report-category">
                <svg viewBox="0 0 20 20" className="drop-icon" aria-hidden="true">
                  <path d="M10 2.5S4.5 9 4.5 12.5a5.5 5.5 0 0 0 11 0C15.5 9 10 2.5 10 2.5z" />
                </svg>
                <strong>Category:</strong> Water &amp; Plumbing
              </p>
              <ProgressTracker current={2} dates={['Aug 30, 2025', 'Aug 30, 2025']} />
            </div>
            <figcaption className="report-aside">
              <span>Your complaint is currently being looked into by our team.</span>
              <svg viewBox="0 0 64 64" className="report-art" aria-hidden="true">
                <path d="M6 44h26v14H6z" className="paper" />
                <path d="M10 49h18M10 53h12" className="ink" />
                <circle cx="34" cy="26" r="13" className="glass" />
                <path d="M28 23h12M28 28h9" className="ink" />
                <path d="M43.5 35.5l11 11" className="handle" />
                <path d="M22 9l-3-4M34 6V1M46 9l3-4" className="spark" />
              </svg>
            </figcaption>
          </figure>
        </section>

        <section id="how-it-works" className="how" aria-labelledby="how-title">
          <h2 id="how-title" className="how-title">
            How It{' '}
            <br />
            Works
          </h2>
          <ol className="how-grid">
            <li className="how-card">
              <span className="how-num" aria-hidden="true">
                1
              </span>
              <div>
                <svg viewBox="0 0 32 32" className="how-icon" aria-hidden="true">
                  <path d="M7 4h13l5 5v19H7z" />
                  <path d="M11 13h10M11 17h7M11 21h5" />
                  <path d="M17 25l9-9 3 3-9 9h-3z" />
                </svg>
                <h3>Report</h3>
                <p>Share the details of the issue in a few simple steps.</p>
              </div>
            </li>
            <li className="how-card">
              <span className="how-num" aria-hidden="true">
                2
              </span>
              <div>
                <svg viewBox="0 0 32 32" className="how-icon" aria-hidden="true">
                  <circle cx="14" cy="14" r="8.5" />
                  <path d="M20.5 20.5L28 28" />
                </svg>
                <h3>Track</h3>
                <p>Get status updates on your complaint.</p>
              </div>
            </li>
            <li className="how-card">
              <span className="how-num" aria-hidden="true">
                3
              </span>
              <div>
                <svg viewBox="0 0 32 32" className="how-icon" aria-hidden="true">
                  <circle cx="16" cy="16" r="12" />
                  <path d="M10.5 16.5l4 4 7-8" />
                </svg>
                <h3>Resolve</h3>
                <p>See the issue resolved — with full transparency.</p>
              </div>
            </li>
          </ol>
        </section>
      </main>

      <footer className="site-footer">
        <div className="footer-top">
          <a href="#top" className="brand-link" aria-label="CivicSignal home">
            <Brand />
          </a>
          <nav className="footer-links" aria-label="Footer">
            <a href="#privacy" onClick={openDialog('privacy')}>
              Privacy Policy
            </a>
            <a href="#terms" onClick={openDialog('terms')}>
              Terms of Service
            </a>
            <a href="#help" onClick={openDialog('help')}>
              Help
            </a>
            <a {...contactProps}>Contact</a>
          </nav>
        </div>
        <div className="footer-bottom">
          <span>© 2026 CivicSignal. All rights reserved.</span>
          <em>A more responsive campus. Together.</em>
        </div>
      </footer>

      <PolicyDialog policy={policy} onClose={() => setPolicy(null)} />
    </div>
  )
}
