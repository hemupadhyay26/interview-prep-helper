import { useQuery } from '@tanstack/react-query'
import { sessionsApi } from '@/api/sessions'
import { parseMessageHistory } from '@/lib/messageHistory'
import { queryKeys } from '@/lib/queryKeys'

/**
 * Loads one session and returns its persisted conversation as a flat
 * `ChatMessage[]`. Disabled until an `id` is provided.
 */
export function useSessionMessages(id: string | null) {
  return useQuery({
    queryKey: queryKeys.session(id ?? '__none__'),
    queryFn: () => sessionsApi.get(id as string),
    enabled: Boolean(id),
    select: (data) => parseMessageHistory(data?.message_history),
  })
}
