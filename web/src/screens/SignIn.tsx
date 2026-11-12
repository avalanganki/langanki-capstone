import { useState, type FormEvent } from 'react'
import { supabase } from '../supabase'
import { NightSky } from './NightSky'

export const CHECK_EMAIL = 'Check your email for a sign-in link.'
export const SEND_FAILED = "Couldn't send the link. Try again."
export const PASSWORD_FAILED = "Couldn't sign in. Check your email and password."

type Mode = 'link' | 'password'
type Status = 'idle' | 'sending' | 'sent' | 'error'

export function SignIn({ notice }: { notice?: string }) {
  const [mode, setMode] = useState<Mode>('link')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [status, setStatus] = useState<Status>('idle')

  function switchTo(next: Mode) {
    setMode(next)
    setPassword('')
    setStatus('idle')
  }

  async function sendLink(event: FormEvent) {
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

  async function signInWithPassword(event: FormEvent) {
    event.preventDefault()
    if (!email.trim() || !password) return
    setStatus('sending')
    const attempt = password
    setPassword('') // cleared after every attempt
    try {
      // Never creates an account. On success App sees the new session and checks /api/me.
      const { error } = await supabase.auth.signInWithPassword({ email: email.trim(), password: attempt })
      setStatus(error ? 'error' : 'idle')
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

        {mode === 'link' && status === 'sent' && (
          <p className="note fade-in" role="status">
            {CHECK_EMAIL}
          </p>
        )}

        {mode === 'link' && status !== 'sent' && (
          <form onSubmit={sendLink} noValidate>
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

        {mode === 'password' && (
          <form onSubmit={signInWithPassword} noValidate>
            <label htmlFor="email">Email</label>
            <input
              id="email"
              className="field"
              type="email"
              autoComplete="username"
              inputMode="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
            <label htmlFor="password">Password</label>
            <input
              id="password"
              className="field"
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
            <button
              className="button"
              type="submit"
              disabled={status === 'sending' || !email.trim() || !password}
            >
              Sign in
            </button>
            {status === 'error' && (
              <p className="error" role="alert">
                {PASSWORD_FAILED}
              </p>
            )}
          </form>
        )}

        <button
          className="button quiet"
          type="button"
          onClick={() => switchTo(mode === 'link' ? 'password' : 'link')}
        >
          {mode === 'link' ? 'Use a password instead' : 'Use a sign-in link instead'}
        </button>
      </main>
    </>
  )
}
