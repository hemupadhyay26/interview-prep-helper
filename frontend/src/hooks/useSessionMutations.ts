import { useMutation, useQueryClient } from '@tanstack/react-query'
import { sessionsApi } from '@/api/sessions'
import { queryKeys } from '@/lib/queryKeys'
import type { SessionSummary } from '@/types'

interface RenameVars {
  id: string
  title: string
}

interface RenameContext {
  previous?: SessionSummary[]
}

/**
 * Create / rename / delete mutations for chat sessions, each keeping the
 * cached `queryKeys.sessions` list in sync so the sidebar updates without
 * a refetch. Rename is optimistic with rollback.
 */
export function useSessionMutations() {
  const qc = useQueryClient()

  const create = useMutation({
    mutationFn: sessionsApi.create,
    onSuccess: (created) => {
      qc.setQueryData<SessionSummary[]>(queryKeys.sessions, (prev = []) => [
        { session_id: created.session_id, title: created.title },
        ...prev,
      ])
    },
  })

  const rename = useMutation<SessionSummary, Error, RenameVars, RenameContext>({
    mutationFn: ({ id, title }) => sessionsApi.rename(id, title),
    onMutate: async ({ id, title }) => {
      await qc.cancelQueries({ queryKey: queryKeys.sessions })
      const previous = qc.getQueryData<SessionSummary[]>(queryKeys.sessions)
      qc.setQueryData<SessionSummary[]>(queryKeys.sessions, (prev = []) =>
        prev.map((s) => (s.session_id === id ? { ...s, title } : s)),
      )
      return { previous }
    },
    onError: (_err, _vars, context) => {
      if (context?.previous) {
        qc.setQueryData(queryKeys.sessions, context.previous)
      }
    },
  })

  const remove = useMutation({
    mutationFn: (id: string) => sessionsApi.remove(id),
    onSuccess: (_data, id) => {
      qc.setQueryData<SessionSummary[]>(queryKeys.sessions, (prev = []) =>
        prev.filter((s) => s.session_id !== id),
      )
      qc.removeQueries({ queryKey: queryKeys.session(id) })
    },
  })

  return { create, rename, remove }
}
