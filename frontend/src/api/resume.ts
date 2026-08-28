import type { Resume } from '@/types'
import { apiFetch } from './client'

/**
 * REST bindings for the backend `/resume` routes.
 * The resume is global (one per app); upload replaces it.
 */
export const resumeApi = {
  get: () => apiFetch<Resume>('/resume'),

  upload: (file: File) => {
    const form = new FormData()
    form.append('file', file)
    return apiFetch<Resume>('/resume', {
      method: 'POST',
      body: form,
    })
  },

  remove: () =>
    apiFetch<{ success: boolean }>('/resume', { method: 'DELETE' }),
}
