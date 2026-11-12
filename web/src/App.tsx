import { useEffect, useState } from 'react'
import type { Session } from '@supabase/supabase-js'
import { ApiError, GENERIC_ERROR, apiGet } from './api'
import { isConfigured, supabase } from './supabase'
import { formatToday } from './dates'
import { NightSky } from './screens/NightSky'
import { SignIn } from './screens/SignIn'

export const NOT_ALLOWED = "This account can't use Patterns."
export const NOT_SET_UP = "Sign-in isn't set up yet. Add the Supabase settings to web/.env.local."

type Check = { state: 'checking' } | { state: 'ok' } | { state: 'error'; message: string }

export default function App() {
  const [session, setSession] = useState<Session | null | undefined>(undefined)
  // The /api/me result for one access token; a new token reads as 'checking' until it answers.
  const [result, setResult] = useState<{ token: string; check: Check } | null>(null)
  const [refused, setRefused] = useState(false)

  useEffect(() => {
    if (!isConfigured) return
    let active = true
    supabase.auth.getSession().then(({ data }) => {
      if (active) setSession(data.session)
    })
    const { data } = supabase.auth.onAuthStateChange((_event, next) => {
      if (active) setSession(next)
    })
    return () => {
      active = false
      data.subscription.unsubscribe()
    }
  }, [])

  const token = session?.access_token
  useEffect(() => {
    if (!token) return
    let active = true
    const setCheck = (check: Check) => setResult({ token, check })
    apiGet('/api/me')
      .then(() => {
        if (!active) return
        setRefused(false)
        setCheck({ state: 'ok' })
      })
      .catch((err: unknown) => {
        if (!active) return
        if (err instanceof ApiError && err.status === 403) {
          setRefused(true)
          supabase.auth.signOut()
          return
        }
        setCheck({ state: 'error', message: err instanceof ApiError ? err.message : GENERIC_ERROR })
      })
    return () => {
      active = false
    }
  }, [token])

  const check: Check = result && result.token === token ? result.check : { state: 'checking' }

  if (!isConfigured) {
    return (
      <>
        <NightSky date="" title="Patterns" />
        <main className="content">
          <p className="error" role="alert">
            {NOT_SET_UP}
          </p>
        </main>
      </>
    )
  }

  if (session === undefined) return null // reading the stored session; avoids a sign-in flash

  if (!session) {
    return <SignIn notice={refused ? NOT_ALLOWED : undefined} />
  }

  return (
    <>
      <NightSky date={formatToday()} title="Tonight" />
      <main className="content">
        {check.state === 'ok' && (
          <p className="note fade-in" role="status">
            Signed in.
          </p>
        )}
        {check.state === 'error' && (
          <p className="error" role="alert">
            {check.message}
          </p>
        )}
        <button className="button quiet" type="button" onClick={() => supabase.auth.signOut()}>
          Sign out
        </button>
      </main>
    </>
  )
}
