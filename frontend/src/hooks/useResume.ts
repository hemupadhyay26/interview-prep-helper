import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ApiError } from '@/api/client'
import { resumeApi } from '@/api/resume'
import { queryKeys } from '@/lib/queryKeys'
import type { Resume } from '@/types'

/**
 * The global resume, or `null` when none is uploaded (the backend 404s in
 * that case — treated as "no resume", not an error).
 */
export function useResume() {
  return useQuery({
    queryKey: queryKeys.resume,
    staleTime: 60_000,
    queryFn: async (): Promise<Resume | null> => {
      try {
        return await resumeApi.get()
      } catch (err) {
        if (err instanceof ApiError && err.status === 404) return null
        throw err
      }
    },
  })
}

/**
 * Upload/replace and delete mutations for the global resume, writing the
 * result straight into the `useResume` cache.
 */
export function useResumeMutations() {
  const qc = useQueryClient()
  const key = queryKeys.resume

  const upload = useMutation({
    mutationFn: (file: File) => resumeApi.upload(file),
    onSuccess: (data) => qc.setQueryData<Resume | null>(key, data),
  })

  const remove = useMutation({
    mutationFn: () => resumeApi.remove(),
    onSuccess: () => qc.setQueryData<Resume | null>(key, null),
  })

  return { upload, remove }
}
