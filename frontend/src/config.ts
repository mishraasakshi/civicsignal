// Settings that come from environment variables (see frontend/.env.example).

/** Public contact email. Not set = Contact explains that details aren't published yet. */
export const CONTACT_EMAIL: string | null = (import.meta.env.VITE_CONTACT_EMAIL ?? '').trim() || null
