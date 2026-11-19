import { useId } from 'react'

/** CivicSignal logo: a signal sending out waves (a complaint being "heard"). */
export function Logo({ size = 28 }: { size?: number }) {
  const gradientId = useId() // unique per logo, so two logos on one page don't clash
  return (
    <svg width={size} height={size} viewBox="0 0 32 32" aria-hidden="true" className="logo">
      <defs>
        <linearGradient id={gradientId} x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="#2fb393" />
          <stop offset="1" stopColor="#1a6fb0" />
        </linearGradient>
      </defs>
      <rect width="32" height="32" rx="8" fill={`url(#${gradientId})`} />
      <circle cx="11" cy="21" r="2.6" fill="#fff" />
      <path d="M11 14.5a6.5 6.5 0 0 1 6.5 6.5" stroke="#fff" strokeWidth="2.4" fill="none" strokeLinecap="round" />
      <path
        d="M11 9a12 12 0 0 1 12 12"
        stroke="#fff"
        strokeWidth="2.4"
        fill="none"
        strokeLinecap="round"
        opacity="0.75"
      />
    </svg>
  )
}
