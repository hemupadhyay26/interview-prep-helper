import type { Job } from '@/types'
import { apiFetch } from './client'

/**
 * REST bindings for the per-session job posting
 * (`/sessions/{id}/job`). One posting per session; adding another
 * replaces it.
 */
export const jobApi = {
  get: (sessionId: string) => apiFetch<Job>(`/sessions/${sessionId}/job`),

  add: (sessionId: string, url: string) =>
    apiFetch<Job>(`/sessions/${sessionId}/job`, {
      method: 'POST',
      body: JSON.stringify({ url }),
    }),

  remove: (sessionId: string) =>
    apiFetch<{ success: boolean; session_id: string }>(
      `/sessions/${sessionId}/job`,
      { method: 'DELETE' },
    ),
}
