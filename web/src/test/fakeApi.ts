import { vi } from 'vitest'

// A fake Patterns API for component tests: answers by method and path. Synthetic values only.
type Reply = { status: number; body?: unknown }
type Handler = Reply | ((body: unknown) => Reply)

export const QUESTIONS = [
  'How was your energy this afternoon?',
  'When was your last caffeine today?',
  'How did you wind down tonight?',
]

export const NIGHTS = {
  source: 'oura',
  nights: [
    { date: '2000-01-01', sleep_score: 70, readiness: 60, avg_hrv: 40 },
    { date: '2000-01-02', sleep_score: 81, readiness: null, avg_hrv: 52.25 },
  ],
  counted: 2,
}

export function defaultRoutes(): Record<string, Handler> {
  return {
    'GET /api/me': { status: 200, body: { signed_in: true } },
    'GET /api/nights': { status: 200, body: NIGHTS },
    'GET /api/questions': { status: 200, body: { questions: QUESTIONS } },
    'GET /api/tags/status': { status: 200, body: { on: true } },
    'POST /api/tags/suggest': { status: 200, body: { tags: [] } },
    'POST /api/entries': (body) => ({ status: 201, body: { id: 1, ...(body as object) } }),
  }
}

export function fakeApi(overrides: Record<string, Handler> = {}) {
  const routes = { ...defaultRoutes(), ...overrides }
  const fetchMock = vi.fn(async (path: string, init?: RequestInit) => {
    const key = `${init?.method ?? 'GET'} ${path}`
    const handler = routes[key]
    if (!handler) return new Response(JSON.stringify({ detail: `No fake for ${key}` }), { status: 404 })
    const body = init?.body ? JSON.parse(String(init.body)) : undefined
    const reply = typeof handler === 'function' ? handler(body) : handler
    return new Response(reply.body === undefined ? null : JSON.stringify(reply.body), {
      status: reply.status,
      headers: { 'Content-Type': 'application/json' },
    })
  })
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

/** The parsed JSON body of the first call to `method path`. */
export function sentBody(fetchMock: ReturnType<typeof fakeApi>, method: string, path: string): unknown {
  const call = fetchMock.mock.calls.find(([p, init]) => p === path && (init?.method ?? 'GET') === method)
  return call?.[1]?.body ? JSON.parse(String(call[1].body)) : undefined
}
