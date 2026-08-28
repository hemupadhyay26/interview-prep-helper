import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ApiError } from '@/api/client'
import { resumeApi } from '@/api/resume'
import { queryKeys } from '@/lib/queryKeys'
import type { Resume } from '@/types'

/**
 * The resume attached to a session, or `null` when none is uploaded
 * (the backend 404s in that case — treated as "no resume", not an error).
 */
export function useResume(sessionId: string | null) {
  return useQuery({
    queryKey: queryKeys.resume(sessionId ?? '__none__'),
    enabled: Boolean(sessionId),
    staleTime: 60_000,
    queryFn: async (): Promise<Resume | null> => {
      try {
        return await resumeApi.get(sessionId as string)
      } catch (err) {
        if (err instanceof ApiError && err.status === 404) return null
        throw err
      }
    },
  })
}

/**
 * Upload/replace and delete mutations for a session's resume, writing the
 * result straight into the `useResume` cache.
 */
export function useResumeMutations(sessionId: string | null) {
  const qc = useQueryClient()
  const key = queryKeys.resume(sessionId ?? '__none__')

  const upload = useMutation({
    mutationFn: (file: File) => resumeApi.upload(sessionId as string, file),
    onSuccess: (data) => qc.setQueryData<Resume | null>(key, data),
  })

  const remove = useMutation({
    mutationFn: () => resumeApi.remove(sessionId as string),
    onSuccess: () => qc.setQueryData<Resume | null>(key, null),
  })

  return { upload, remove }
}
