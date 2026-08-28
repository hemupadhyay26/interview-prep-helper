import { useCallback, useRef, useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { streamChat } from '@/api/streamChat'
import { queryKeys } from '@/lib/queryKeys'
import type { ChatMessage, SessionSummary } from '@/types'

let seq = 0
const nextId = (prefix: string) => `${prefix}-${Date.now()}-${seq++}`

/**
 * Owns the transient state of an in-flight chat turn: the optimistic
 * user + assistant messages ("overlay") shown on top of the persisted
 * history while tokens stream in.
 *
 * On completion the session query is invalidated so the overlay can be
 * dropped in favour of the freshly persisted messages (no flicker,
 * because `invalidateQueries` resolves after the refetch).
 */
export function useChatStream() {
  const qc = useQueryClient()

  const [overlay, setOverlay] = useState<ChatMessage[]>([])
  const [isStreaming, setIsStreaming] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const abortRef = useRef<AbortController | null>(null)

  const reset = useCallback(() => {
    abortRef.current?.abort()
    abortRef.current = null
    setOverlay([])
    setError(null)
    setIsStreaming(false)
  }, [])

  const send = useCallback(
    async (sessionId: string, text: string) => {
      setError(null)

      const assistantId = nextId('a')
      setOverlay([
        { id: nextId('u'), role: 'user', content: text },
        { id: assistantId, role: 'assistant', content: '' },
      ])
      setIsStreaming(true)

      const controller = new AbortController()
      abortRef.current = controller

      try {
        await streamChat({
          sessionId,
          message: text,
          signal: controller.signal,
          onChunk: (chunk) => {
            setOverlay((prev) =>
              prev.map((m) =>
                m.id === assistantId
                  ? { ...m, content: m.content + chunk }
                  : m,
              ),
            )
          },
          onDone: async ({ title }) => {
            if (title) {
              qc.setQueryData<SessionSummary[]>(
                queryKeys.sessions,
                (prev = []) =>
                  prev.map((s) =>
                    s.session_id === sessionId ? { ...s, title } : s,
                  ),
              )
            }
            await qc.invalidateQueries({
              queryKey: queryKeys.session(sessionId),
            })
            setOverlay([])
            setIsStreaming(false)
          },
          onError: (detail) => {
            setError(detail)
            setIsStreaming(false)
            setOverlay((prev) =>
              prev.filter(
                (m) => !(m.id === assistantId && m.content === ''),
              ),
            )
          },
        })
      } catch (err) {
        if ((err as Error).name === 'AbortError') return
        setError((err as Error).message)
        setIsStreaming(false)
      }
    },
    [qc],
  )

  return { overlay, isStreaming, error, send, reset }
}
