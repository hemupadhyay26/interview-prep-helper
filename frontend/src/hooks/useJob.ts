import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ApiError } from '@/api/client'
import { jobApi } from '@/api/job'
import { queryKeys } from '@/lib/queryKeys'
import type { Job } from '@/types'

/**
 * The job posting attached to `sessionId`, or `null` when none is set
 * (the backend 404s in that case). Keeps the pasted URL / parsed role
 * around so the UI can show what this conversation is grounded in.
 */
export function useJob(sessionId: string | null) {
  return useQuery({
    queryKey: sessionId ? queryKeys.job(sessionId) : ['job', 'none'],
    enabled: Boolean(sessionId),
    staleTime: 60_000,
    queryFn: async (): Promise<Job | null> => {
      try {
        return await jobApi.get(sessionId as string)
      } catch (err) {
        if (err instanceof ApiError && err.status === 404) return null
        throw err
      }
    },
  })
}

/**
 * Attach / replace a job posting on a session by URL. The backend
 * scrapes, structures, and stores it (including the source URL), and
 * titles the session after the role - so on success we write the result
 * into the `useJob` cache and refresh the session list.
 */
export function useAddJob() {
  const qc = useQueryClient()

  return useMutation({
    mutationFn: ({ sessionId, url }: { sessionId: string; url: string }) =>
      jobApi.add(sessionId, url),
    onSuccess: (data, { sessionId }) => {
      qc.setQueryData<Job | null>(queryKeys.job(sessionId), data)
      qc.invalidateQueries({ queryKey: queryKeys.sessions })
    },
  })
}
