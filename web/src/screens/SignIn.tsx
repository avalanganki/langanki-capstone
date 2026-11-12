import { useState, type FormEvent } from 'react'
import { supabase } from '../supabase'
import { NightSky } from './NightSky'

export const CHECK_EMAIL = 'Check your email for a sign-in link.'
export const SEND_FAILED = "Couldn't send the link. Try again."

type Status = 'idle' | 'sending' | 'sent' | 'error'

export function SignIn({ notice }: { notice?: string }) {
  const [email, setEmail] = useState('')
  const [status, setStatus] = useState<Status>('idle')

  async function send(event: FormEvent) {
    event.preventDefault()
    if (!email.trim()) return
    setStatus('sending')
    try {
      const { error } = await supabase.auth.signInWithOtp({
        email: email.trim(),
        // Sign-ups are off: a link only goes to an account that already exists.
        options: { shouldCreateUser: false, emailRedirectTo: window.location.origin },
      })
      if (error) {
        setStatus('error')
        return
      }
      setEmail('') // never show the address again after sending
      setStatus('sent')
    } catch {
      setStatus('error')
    }
  }

  return (
    <>
      <NightSky date="" title="Patterns" />
      <main className="content">
        {notice && (
          <p className="error" role="alert">
            {notice}
          </p>
        )}
        <p className="prompt">Sign in to start tonight's reflection.</p>
        {status === 'sent' ? (
          <p className="note fade-in" role="status">
            {CHECK_EMAIL}
          </p>
        ) : (
          <form onSubmit={send} noValidate>
            <label htmlFor="email">Email</label>
            <input
              id="email"
              className="field"
              type="email"
              autoComplete="email"
              inputMode="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
            <button className="button" type="submit" disabled={status === 'sending' || !email.trim()}>
              Send sign-in link
            </button>
            {status === 'error' && (
              <p className="error" role="alert">
                {SEND_FAILED}
              </p>
            )}
          </form>
        )}
      </main>
    </>
  )
}
