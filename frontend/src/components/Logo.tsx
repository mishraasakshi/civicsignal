/** CivicSignal logo: a signal sending out waves (a complaint being "heard"). */
export function Logo({ size = 28 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 32 32" aria-hidden="true" className="logo">
      <rect width="32" height="32" rx="8" className="logo-tile" />
      <circle cx="11" cy="21" r="3" className="logo-dot" />
      <path d="M11 14.5a6.5 6.5 0 0 1 6.5 6.5" className="logo-wave" />
      <path d="M11 9a12 12 0 0 1 12 12" className="logo-wave" />
    </svg>
  )
}
