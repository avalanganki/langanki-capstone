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

/** GET an API path with the signed-in user's access token. Never logs the token. */
export async function apiGet<T = unknown>(path: string): Promise<T> {
  const { data } = await supabase.auth.getSession()
  const token = data.session?.access_token
  const headers: Record<string, string> = { Accept: 'application/json' }
  if (token) headers.Authorization = `Bearer ${token}`

  let response: Response
  try {
    response = await fetch(path, { headers })
  } catch {
    throw new ApiError(0, GENERIC_ERROR)
  }

  if (!response.ok) {
    let detail = GENERIC_ERROR
    try {
      const body = await response.json()
      if (body && typeof body.detail === 'string') detail = body.detail
    } catch {
      // Not JSON (for example the dev proxy when the API is down): keep the generic message.
    }
    throw new ApiError(response.status, detail)
  }
  return (await response.json()) as T
}
