import { createClient } from '@supabase/supabase-js'

// Only the publishable (anon) key belongs in the browser. Every table has row level security
// with no public policies, so this key alone can't read or write data. The API holds the secret key.
const url = import.meta.env.VITE_SUPABASE_URL ?? ''
const key = import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY ?? ''

/** False until web/.env.local has both VITE_ settings; the app then shows a setup message. */
export const isConfigured = Boolean(url && key)

// createClient throws on a blank URL, so a placeholder keeps the import safe when not configured.
export const supabase = createClient(url || 'http://localhost', key || 'not-configured')
