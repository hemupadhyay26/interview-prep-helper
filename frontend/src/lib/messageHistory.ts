import type { ChatMessage } from '@/types'

/**
 * The backend stores conversation memory as a pydantic-ai
 * `ModelMessagesTypeAdapter` JSON dump: an array of request/response
 * messages, each with a `parts` array. This turns that into a flat list
 * of `ChatMessage` suitable for rendering, dropping system prompts and
 * tool-call / tool-return plumbing.
 */

interface RawPart {
  part_kind?: string
  content?: unknown
}

interface RawMessage {
  kind?: string
  parts?: RawPart[]
}

function partText(content: unknown): string {
  if (typeof content === 'string') return content
  // Multimodal user prompts come through as an array of parts.
  if (Array.isArray(content)) {
    return content
      .map((c) =>
        typeof c === 'string'
          ? c
          : ((c as { text?: string } | null)?.text ?? ''),
      )
      .join('')
  }
  return ''
}

export function parseMessageHistory(
  raw: string | unknown[] | null | undefined,
): ChatMessage[] {
  if (!raw) return []

  let messages: unknown
  try {
    messages = typeof raw === 'string' ? JSON.parse(raw) : raw
  } catch {
    return []
  }
  if (!Array.isArray(messages)) return []

  const out: ChatMessage[] = []

  ;(messages as RawMessage[]).forEach((message, i) => {
    const parts = Array.isArray(message?.parts) ? message.parts : []

    if (message?.kind === 'request') {
      const text = parts
        .filter((p) => p?.part_kind === 'user-prompt')
        .map((p) => partText(p.content))
        .join('\n')
        .trim()
      if (text) out.push({ id: `h-${i}`, role: 'user', content: text })
    } else if (message?.kind === 'response') {
      const text = parts
        .filter((p) => p?.part_kind === 'text')
        .map((p) => partText(p.content))
        .join('')
        .trim()
      if (text) out.push({ id: `h-${i}`, role: 'assistant', content: text })
    }
  })

  return out
}
