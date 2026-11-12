import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { TOKEN, auth, fakeSession, resetSupabase } from './test/supabaseMock'

vi.mock('./supabase', () => import('./test/supabaseMock'))

const { default: App } = await import('./App')

function jsonResponse(status: number, body: unknown) {
  return new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } })
}

describe('App', () => {
  let fetchMock: ReturnType<typeof vi.fn>

  beforeEach(() => {
    fetchMock = vi.fn()
    vi.stubGlobal('fetch', fetchMock)
  })
  afterEach(() => vi.unstubAllGlobals())

  it('shows SignIn when signed out and does not call the API', async () => {
    resetSupabase(null)
    render(<App />)
    expect(await screen.findByRole('button', { name: 'Send sign-in link' })).toBeInTheDocument()
    expect(fetchMock).not.toHaveBeenCalled()
  })

  it('shows the Tonight header and "Signed in." when /api/me is ok', async () => {
    resetSupabase(fakeSession)
    fetchMock.mockResolvedValue(jsonResponse(200, { signed_in: true }))
    render(<App />)
    expect(await screen.findByText('Signed in.')).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Tonight' })).toBeInTheDocument()
    expect(fetchMock.mock.calls[0][0]).toBe('/api/me')
    expect(fetchMock.mock.calls[0][1].headers.Authorization).toBe(`Bearer ${TOKEN}`)
  })

  it('on 403 shows the not-allowed message and signs out', async () => {
    resetSupabase(fakeSession)
    fetchMock.mockResolvedValue(jsonResponse(403, { detail: "This account can't use Patterns." }))
    render(<App />)
    expect(await screen.findByText("This account can't use Patterns.")).toBeInTheDocument()
    expect(auth.signOut).toHaveBeenCalled()
    expect(screen.getByRole('button', { name: 'Send sign-in link' })).toBeInTheDocument()
    expect(screen.queryByText('Signed in.')).not.toBeInTheDocument()
  })

  it("shows the API's message on any other error", async () => {
    resetSupabase(fakeSession)
    fetchMock.mockResolvedValue(jsonResponse(503, { detail: "Couldn't check sign-in. Try again." }))
    render(<App />)
    expect(await screen.findByText("Couldn't check sign-in. Try again.")).toBeInTheDocument()
    expect(auth.signOut).not.toHaveBeenCalled()
    expect(screen.queryByText('Signed in.')).not.toBeInTheDocument()
  })

  it('Sign out returns to the sign-in screen', async () => {
    resetSupabase(fakeSession)
    fetchMock.mockResolvedValue(jsonResponse(200, { signed_in: true }))
    render(<App />)
    await screen.findByText('Signed in.')
    await userEvent.click(screen.getByRole('button', { name: 'Sign out' }))
    expect(auth.signOut).toHaveBeenCalled()
    expect(await screen.findByRole('button', { name: 'Send sign-in link' })).toBeInTheDocument()
  })

  it('a password sign-in for an account that is not allowed is signed out', async () => {
    resetSupabase(null)
    fetchMock.mockResolvedValue(jsonResponse(403, { detail: "This account can't use Patterns." }))
    render(<App />)
    await userEvent.click(await screen.findByRole('button', { name: 'Use a password instead' }))
    await userEvent.type(screen.getByLabelText('Email'), 'other@example.invalid')
    await userEvent.type(screen.getByLabelText('Password'), 'synthetic-pass-123')
    await userEvent.click(screen.getByRole('button', { name: 'Sign in' }))

    expect(await screen.findByText("This account can't use Patterns.")).toBeInTheDocument()
    expect(fetchMock.mock.calls[0][0]).toBe('/api/me')
    expect(auth.signOut).toHaveBeenCalled()
    expect(screen.queryByText('Signed in.')).not.toBeInTheDocument()
  })

  it('a password sign-in for my account shows the Tonight header', async () => {
    resetSupabase(null)
    fetchMock.mockResolvedValue(jsonResponse(200, { signed_in: true }))
    render(<App />)
    await userEvent.click(await screen.findByRole('button', { name: 'Use a password instead' }))
    await userEvent.type(screen.getByLabelText('Email'), 'someone@example.invalid')
    await userEvent.type(screen.getByLabelText('Password'), 'synthetic-pass-123')
    await userEvent.click(screen.getByRole('button', { name: 'Sign in' }))

    expect(await screen.findByText('Signed in.')).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Tonight' })).toBeInTheDocument()
  })
})
