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
})
