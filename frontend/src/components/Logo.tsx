/** CivicSignal logo: a coral megaphone (a complaint being raised) with mustard sound lines. */
export function Logo({ size = 34 }: { size?: number }) {
  return (
    <svg width={size} height={(size * 32) / 40} viewBox="0 0 40 32" aria-hidden="true" className="logo">
      <rect x="4" y="12" width="7" height="9" rx="2" className="logo-body" />
      <path d="M11 12 25 5v23l-14-7z" className="logo-body" />
      <ellipse cx="25.5" cy="16.5" rx="2.6" ry="11.5" className="logo-rim" />
      <path d="M8 21l2.5 7h3.5l-2-7" className="logo-body" />
      <path d="M30.5 9.5l3.5-3M31.5 16.5h5M30.5 23.5l3.5 3" className="logo-waves" />
    </svg>
  )
}

/** Logo + "CivicSignal" wordmark ("Signal" in mustard). */
export function Brand({ size = 34 }: { size?: number }) {
  return (
    <span className="brand">
      <Logo size={size} />
      <span className="brand-word">
        Civic<span className="brand-accent">Signal</span>
      </span>
    </span>
  )
}
