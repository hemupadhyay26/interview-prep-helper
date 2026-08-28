import { useQuery } from '@tanstack/react-query'
import { sessionsApi } from '@/api/sessions'
import { queryKeys } from '@/lib/queryKeys'

/**
 * The sidebar's list of chat sessions.
 */
export function useSessions() {
  return useQuery({
    queryKey: queryKeys.sessions,
    queryFn: sessionsApi.list,
    staleTime: 30_000,
  })
}
