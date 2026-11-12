import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { auth, resetSupabase } from '../test/supabaseMock'

vi.mock('../supabase', () => import('../test/supabaseMock'))

const { SignIn } = await import('./SignIn')

const EMAIL = 'someone@example.invalid'

describe('SignIn', () => {
  beforeEach(() => resetSupabase(null))

  it('sends the OTP without creating a user and shows the check-email message', async () => {
    render(<SignIn />)
    await userEvent.type(screen.getByLabelText('Email'), EMAIL)
    await userEvent.click(screen.getByRole('button', { name: 'Send sign-in link' }))

    expect(auth.signInWithOtp).toHaveBeenCalledWith({
      email: EMAIL,
      options: { shouldCreateUser: false, emailRedirectTo: window.location.origin },
    })
    expect(await screen.findByText('Check your email for a sign-in link.')).toBeInTheDocument()
    expect(document.body.textContent).not.toContain(EMAIL)
  })

  it('shows the retry message on error', async () => {
    auth.signInWithOtp.mockResolvedValueOnce({ data: {}, error: { message: 'Signups not allowed for otp' } })
    render(<SignIn />)
    await userEvent.type(screen.getByLabelText('Email'), EMAIL)
    await userEvent.click(screen.getByRole('button', { name: 'Send sign-in link' }))

    expect(await screen.findByText("Couldn't send the link. Try again.")).toBeInTheDocument()
    expect(screen.queryByText('Check your email for a sign-in link.')).not.toBeInTheDocument()
    expect(document.body.textContent).not.toContain('Signups not allowed')
  })

  it('shows the retry message when the request throws', async () => {
    auth.signInWithOtp.mockRejectedValueOnce(new TypeError('Failed to fetch'))
    render(<SignIn />)
    await userEvent.type(screen.getByLabelText('Email'), EMAIL)
    await userEvent.click(screen.getByRole('button', { name: 'Send sign-in link' }))
    expect(await screen.findByText("Couldn't send the link. Try again.")).toBeInTheDocument()
  })

  it('does not send with a blank email', async () => {
    render(<SignIn />)
    expect(screen.getByRole('button', { name: 'Send sign-in link' })).toBeDisabled()
    expect(auth.signInWithOtp).not.toHaveBeenCalled()
  })

  it('never logs the email', async () => {
    const spies = (['log', 'info', 'warn', 'error', 'debug'] as const).map((m) =>
      vi.spyOn(console, m).mockImplementation(() => {}),
    )
    render(<SignIn />)
    await userEvent.type(screen.getByLabelText('Email'), EMAIL)
    await userEvent.click(screen.getByRole('button', { name: 'Send sign-in link' }))
    await screen.findByText('Check your email for a sign-in link.')
    for (const spy of spies) {
      expect(JSON.stringify(spy.mock.calls)).not.toContain(EMAIL)
      spy.mockRestore()
    }
  })

  describe('password', () => {
    const PASSWORD = 'synthetic-pass-123'

    async function fillPassword(email = EMAIL, password = PASSWORD) {
      await userEvent.click(screen.getByRole('button', { name: 'Use a password instead' }))
      await userEvent.type(screen.getByLabelText('Email'), email)
      await userEvent.type(screen.getByLabelText('Password'), password)
    }

    it('switches to the password form and back', async () => {
      render(<SignIn />)
      await userEvent.click(screen.getByRole('button', { name: 'Use a password instead' }))
      expect(screen.getByLabelText('Password')).toHaveAttribute('type', 'password')
      expect(screen.getByLabelText('Password')).toHaveAttribute('autocomplete', 'current-password')
      expect(screen.queryByRole('button', { name: 'Send sign-in link' })).not.toBeInTheDocument()

      await userEvent.click(screen.getByRole('button', { name: 'Use a sign-in link instead' }))
      expect(screen.getByRole('button', { name: 'Send sign-in link' })).toBeInTheDocument()
      expect(screen.queryByLabelText('Password')).not.toBeInTheDocument()
    })

    it('is disabled until both fields are filled', async () => {
      render(<SignIn />)
      await userEvent.click(screen.getByRole('button', { name: 'Use a password instead' }))
      const button = screen.getByRole('button', { name: 'Sign in' })
      expect(button).toBeDisabled()
      await userEvent.type(screen.getByLabelText('Email'), EMAIL)
      expect(button).toBeDisabled()
      await userEvent.type(screen.getByLabelText('Password'), PASSWORD)
      expect(button).toBeEnabled()
    })

    it('signs in with the email and password and never sends a link', async () => {
      render(<SignIn />)
      await fillPassword()
      await userEvent.click(screen.getByRole('button', { name: 'Sign in' }))
      expect(auth.signInWithPassword).toHaveBeenCalledWith({ email: EMAIL, password: PASSWORD })
      expect(auth.signInWithOtp).not.toHaveBeenCalled()
    })

    it('shows the generic message on error, without Supabase text, and clears the password', async () => {
      auth.signInWithPassword.mockResolvedValueOnce({ data: { session: null }, error: { message: 'Invalid login credentials' } })
      render(<SignIn />)
      await fillPassword()
      await userEvent.click(screen.getByRole('button', { name: 'Sign in' }))
      expect(await screen.findByText("Couldn't sign in. Check your email and password.")).toBeInTheDocument()
      expect(document.body.textContent).not.toContain('Invalid login credentials')
      expect(screen.getByLabelText('Password')).toHaveValue('')
      expect(screen.getByRole('button', { name: 'Sign in' })).toBeDisabled()
    })

    it('shows the generic message when the request throws', async () => {
      auth.signInWithPassword.mockRejectedValueOnce(new TypeError('Failed to fetch'))
      render(<SignIn />)
      await fillPassword()
      await userEvent.click(screen.getByRole('button', { name: 'Sign in' }))
      expect(await screen.findByText("Couldn't sign in. Check your email and password.")).toBeInTheDocument()
      expect(screen.getByLabelText('Password')).toHaveValue('')
    })

    it('never logs the email or password', async () => {
      const spies = (['log', 'info', 'warn', 'error', 'debug'] as const).map((m) =>
        vi.spyOn(console, m).mockImplementation(() => {}),
      )
      auth.signInWithPassword.mockResolvedValueOnce({ data: { session: null }, error: { message: 'nope' } })
      render(<SignIn />)
      await fillPassword()
      await userEvent.click(screen.getByRole('button', { name: 'Sign in' }))
      await screen.findByText("Couldn't sign in. Check your email and password.")
      for (const spy of spies) {
        const logged = JSON.stringify(spy.mock.calls)
        expect(logged).not.toContain(EMAIL)
        expect(logged).not.toContain(PASSWORD)
        spy.mockRestore()
      }
    })
  })
})
