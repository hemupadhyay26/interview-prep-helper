import type { Resume } from '@/types'
import { apiFetch } from './client'

/**
 * REST bindings for the backend `/sessions/{id}/resume` routes.
 * A session may have at most one resume; upload replaces it.
 */
export const resumeApi = {
  get: (sessionId: string) =>
    apiFetch<Resume>(`/sessions/${sessionId}/resume`),

  upload: (sessionId: string, file: File) => {
    const form = new FormData()
    form.append('file', file)
    return apiFetch<Resume>(`/sessions/${sessionId}/resume`, {
      method: 'POST',
      body: form,
    })
  },

  remove: (sessionId: string) =>
    apiFetch<{ success: boolean; session_id: string }>(
      `/sessions/${sessionId}/resume`,
      { method: 'DELETE' },
    ),
}
