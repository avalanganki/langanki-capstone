import { supabase } from './supabase'

export const GENERIC_ERROR = "Couldn't reach Patterns. Try again."

/** A non-2xx answer from the API. `message` is the API's plain-language `detail`. */
export class ApiError extends Error {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

async function request<T>(method: string, path: string, body?: unknown): Promise<T> {
  const { data } = await supabase.auth.getSession()
  const token = data.session?.access_token
  const headers: Record<string, string> = { Accept: 'application/json' }
  if (token) headers.Authorization = `Bearer ${token}`
  if (body !== undefined) headers['Content-Type'] = 'application/json'

  let response: Response
  try {
    response = await fetch(path, {
      method,
      headers,
      ...(body !== undefined ? { body: JSON.stringify(body) } : {}),
    })
  } catch {
    throw new ApiError(0, GENERIC_ERROR)
  }

  if (!response.ok) {
    let detail = GENERIC_ERROR
    try {
      const errorBody = await response.json()
      if (errorBody && typeof errorBody.detail === 'string') detail = errorBody.detail
    } catch {
      // Not JSON (for example the dev proxy when the API is down): keep the generic message.
    }
    throw new ApiError(response.status, detail)
  }
  if (response.status === 204) return undefined as T
  return (await response.json()) as T
}

/** GET an API path with the signed-in user's access token. Never logs the token. */
export function apiGet<T = unknown>(path: string): Promise<T> {
  return request<T>('GET', path)
}

/** POST JSON to an API path with the signed-in user's access token. Never logs the body or token. */
export function apiPost<T = unknown>(path: string, body: unknown): Promise<T> {
  return request<T>('POST', path, body)
}
