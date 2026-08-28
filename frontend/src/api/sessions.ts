import type {
  SessionDetail,
  SessionMutationResult,
  SessionSummary,
} from '@/types'
import { apiFetch } from './client'

/**
 * REST bindings for the backend `/sessions` router. These are plain
 * async functions — TanStack Query wraps them in `src/hooks/`.
 */
export const sessionsApi = {
  list: () => apiFetch<SessionSummary[]>('/sessions'),

  get: (id: string) => apiFetch<SessionDetail>(`/sessions/${id}`),

  create: () =>
    apiFetch<SessionMutationResult>('/sessions', { method: 'POST' }),

  rename: (id: string, title: string) =>
    apiFetch<SessionMutationResult>(`/sessions/${id}`, {
      method: 'PATCH',
      body: JSON.stringify({ title }),
    }),

  remove: (id: string) =>
    apiFetch<{ success: boolean; session_id: string }>(`/sessions/${id}`, {
      method: 'DELETE',
    }),
}
