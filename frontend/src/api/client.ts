export const BASE_URL: string =
  import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

export class ApiError extends Error {
  status: number

  constructor(message: string, status: number) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

/**
 * Thin fetch wrapper. Every REST call in `src/api/` goes through here so
 * error handling and the base URL live in one place.
 *
 * JSON is assumed unless the body is `FormData` (file uploads), in which
 * case the browser sets the multipart `Content-Type` itself.
 */
export async function apiFetch<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const isFormData = options.body instanceof FormData

  const res = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers: {
      ...(isFormData ? {} : { 'Content-Type': 'application/json' }),
      ...options.headers,
    },
  })

  if (!res.ok) {
    let detail = `Request failed (${res.status})`
    try {
      const body = await res.json()
      if (body?.detail) detail = body.detail as string
    } catch {
      // no JSON body — keep the default message
    }
    throw new ApiError(detail, res.status)
  }

  if (res.status === 204) return null as T
  return res.json() as Promise<T>
}
