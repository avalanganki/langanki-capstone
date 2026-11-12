import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { TOKEN, fakeSession, resetSupabase } from './test/supabaseMock'

vi.mock('./supabase', () => import('./test/supabaseMock'))

const { ApiError, apiGet } = await import('./api')

async function failure(path: string) {
  try {
    await apiGet(path)
  } catch (e) {
    return e as InstanceType<typeof ApiError>
  }
  throw new Error('expected apiGet to throw')
}

function jsonResponse(status: number, body: unknown) {
  return new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } })
}

describe('apiGet', () => {
  let fetchMock: ReturnType<typeof vi.fn>

  beforeEach(() => {
    resetSupabase(fakeSession)
    fetchMock = vi.fn()
    vi.stubGlobal('fetch', fetchMock)
  })
  afterEach(() => vi.unstubAllGlobals())

  it('sends the Bearer token and returns the JSON', async () => {
    fetchMock.mockResolvedValue(jsonResponse(200, { signed_in: true }))
    await expect(apiGet('/api/me')).resolves.toEqual({ signed_in: true })
    const [path, init] = fetchMock.mock.calls[0]
    expect(path).toBe('/api/me')
    expect(init.headers.Authorization).toBe(`Bearer ${TOKEN}`)
  })

  it.each([
    [401, 'Sign in required.'],
    [403, "This account can't use Patterns."],
  ])('throws ApiError with the detail on %i', async (status, detail) => {
    fetchMock.mockResolvedValue(jsonResponse(status, { detail }))
    const err = await failure('/api/me')
    expect(err).toBeInstanceOf(ApiError)
    expect(err.status).toBe(status)
    expect(err.message).toBe(detail)
  })

  it('uses a plain message when the error body is not JSON', async () => {
    fetchMock.mockResolvedValue(new Response('Bad gateway', { status: 502 }))
    const err = await failure('/api/me')
    expect(err).toBeInstanceOf(ApiError)
    expect(err.message).toBe("Couldn't reach Patterns. Try again.")
  })

  it('uses a plain message when the API is unreachable', async () => {
    fetchMock.mockRejectedValue(new TypeError('Failed to fetch'))
    const err = await failure('/api/me')
    expect(err).toBeInstanceOf(ApiError)
    expect(err.status).toBe(0)
  })

  it('sends no Authorization header when signed out', async () => {
    resetSupabase(null)
    fetchMock.mockResolvedValue(jsonResponse(200, {}))
    await apiGet('/api/health')
    expect(fetchMock.mock.calls[0][1].headers.Authorization).toBeUndefined()
  })

  it('never logs the token', async () => {
    const spies = (['log', 'info', 'warn', 'error', 'debug'] as const).map((m) =>
      vi.spyOn(console, m).mockImplementation(() => {}),
    )
    fetchMock.mockResolvedValue(jsonResponse(403, { detail: 'no' }))
    await apiGet('/api/me').catch(() => {})
    for (const spy of spies) {
      expect(JSON.stringify(spy.mock.calls)).not.toContain(TOKEN)
      spy.mockRestore()
    }
  })
})
