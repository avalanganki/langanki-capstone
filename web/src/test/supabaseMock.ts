import { vi } from 'vitest'

// In-memory stand-in for src/supabase.ts. No real Supabase is ever contacted in tests.
type Listener = (event: string, session: unknown) => void

export const TOKEN = 'test-access-token'
export const fakeSession = { access_token: TOKEN }

let listeners: Listener[] = []
let current: unknown = null

export const auth = {
  getSession: vi.fn(async () => ({ data: { session: current }, error: null })),
  onAuthStateChange: vi.fn((cb: Listener) => {
    listeners.push(cb)
    return { data: { subscription: { unsubscribe: () => (listeners = listeners.filter((l) => l !== cb)) } } }
  }),
  signInWithOtp: vi.fn(async (_args: unknown) => ({ data: {}, error: null as unknown })),
  // Succeeds by default and starts a session, like the real client.
  signInWithPassword: vi.fn(async (_args: unknown) => {
    setSession(fakeSession)
    return { data: { session: fakeSession as unknown }, error: null as unknown }
  }),
  signOut: vi.fn(async () => {
    setSession(null)
    return { error: null }
  }),
}

export function setSession(session: unknown) {
  current = session
  listeners.forEach((l) => l(session ? 'SIGNED_IN' : 'SIGNED_OUT', session))
}

export function resetSupabase(session: unknown = null) {
  current = session
  listeners = []
  vi.clearAllMocks()
}

export const supabase = { auth }
export const isConfigured = true
