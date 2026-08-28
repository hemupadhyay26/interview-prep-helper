import type { ChatDonePayload } from '@/types'
import { BASE_URL } from './client'

export interface StreamChatOptions {
  sessionId: string
  message: string
  signal?: AbortSignal
  onChunk?: (text: string) => void
  onDone?: (data: ChatDonePayload) => void
  onError?: (detail: string) => void
}

/**
 * Stream a chat response from `POST /sessions/{id}/chat`.
 *
 * The endpoint replies with Server-Sent Events (not a WebSocket and not
 * plain JSON), so this is kept outside TanStack Query — `useChatStream`
 * owns the React state and calls this to feed it.
 *
 * Event types emitted by the backend:
 *   - "chunk": { text }              one per streamed text delta
 *   - "done":  { session_id, title } once, on success
 *   - "error": { detail }            once, in place of "done"
 */
export async function streamChat({
  sessionId,
  message,
  signal,
  onChunk,
  onDone,
  onError,
}: StreamChatOptions): Promise<void> {
  const res = await fetch(`${BASE_URL}/sessions/${sessionId}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message }),
    signal,
  })

  if (!res.ok || !res.body) {
    onError?.(`Chat request failed (${res.status})`)
    return
  }

  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  for (;;) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })

    // SSE frames are separated by a blank line.
    let sep: number
    while ((sep = buffer.indexOf('\n\n')) !== -1) {
      const frame = buffer.slice(0, sep)
      buffer = buffer.slice(sep + 2)
      dispatchFrame(frame, { onChunk, onDone, onError })
    }
  }
}

type FrameHandlers = Pick<StreamChatOptions, 'onChunk' | 'onDone' | 'onError'>

function dispatchFrame(
  frame: string,
  { onChunk, onDone, onError }: FrameHandlers,
): void {
  let event = 'message'
  const dataLines: string[] = []

  for (const line of frame.split('\n')) {
    if (line.startsWith('event:')) event = line.slice(6).trim()
    else if (line.startsWith('data:')) dataLines.push(line.slice(5).trim())
  }
  if (dataLines.length === 0) return

  let payload: Record<string, unknown>
  try {
    payload = JSON.parse(dataLines.join('\n'))
  } catch {
    return
  }

  if (event === 'chunk') onChunk?.((payload.text as string) ?? '')
  else if (event === 'done') onDone?.(payload as unknown as ChatDonePayload)
  else if (event === 'error')
    onError?.((payload.detail as string) ?? 'Unknown error')
}
