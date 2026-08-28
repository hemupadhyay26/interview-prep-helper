import { useEffect, useRef } from 'react'
import { CopyButton } from '@/components/animate-ui/components/buttons/copy'
import Composer from './Composer'
import Markdown from './Markdown'
import ResumePanel from './ResumePanel'
import type { ChatMessage } from '@/types'

interface ChatPanelProps {
  messages: ChatMessage[]
  isStreaming: boolean
  error: string | null
  isLoading: boolean
  onSend: (text: string) => void
  sessionId: string | null
  sessionTitle?: string
}

function EmptyState() {
  return (
    <div className="mx-auto mt-[12vh] max-w-md text-center">
      <h1 className="mb-3 text-2xl font-semibold tracking-tight">
        Interview Prep Helper
      </h1>
      <p className="text-sm text-muted-foreground">
        Tell me about the role you&apos;re preparing for and I&apos;ll help you
        get ready — then ask for practice questions whenever you want them.
      </p>
    </div>
  )
}

export default function ChatPanel({
  messages,
  isStreaming,
  error,
  isLoading,
  onSend,
  sessionId,
  sessionTitle,
}: ChatPanelProps) {
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const el = scrollRef.current
    if (el) el.scrollTop = el.scrollHeight
  }, [messages, isStreaming])

  const showEmpty = !isLoading && messages.length === 0

  return (
    <main className="border-fade-x flex min-w-0 flex-1 flex-col">
      {sessionId && (
        <header className="flex items-center justify-between gap-3 px-6 py-2.5">
          <span className="truncate text-sm font-medium text-muted-foreground">
            {sessionTitle || 'Untitled'}
          </span>
          <ResumePanel sessionId={sessionId} />
        </header>
      )}

      <div ref={scrollRef} className="flex-1 overflow-y-auto">
        <div className="mx-auto max-w-3xl space-y-6 px-6 py-8">
          {isLoading && (
            <div className="py-2 text-sm text-muted-foreground">
              Loading conversation…
            </div>
          )}
          {showEmpty && <EmptyState />}

          {messages.map((m) => {
            if (m.role === 'user') {
              return (
                <div key={m.id} className="flex justify-end">
                  <div className="max-w-[80%] whitespace-pre-wrap rounded-2xl rounded-br-sm bg-primary px-4 py-2.5 text-sm text-primary-foreground">
                    {m.content}
                  </div>
                </div>
              )
            }

            return (
              <div key={m.id} className="group">
                <div className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                  Assistant
                </div>

                <div className="text-sm leading-7 text-foreground">
                  {m.content ? (
                    <Markdown text={m.content} />
                  ) : (
                    <span className="inline-block animate-pulse text-primary">
                      ▋
                    </span>
                  )}
                </div>

                {m.content && (
                  <div className="mt-2">
                    <CopyButton
                      content={m.content}
                      variant="ghost"
                      size="xs"
                      className="opacity-0 transition-opacity group-hover:opacity-100"
                      aria-label="Copy response"
                    />
                  </div>
                )}
              </div>
            )
          })}

          {error && (
            <div className="mt-3 rounded-md border border-destructive/40 bg-destructive/10 px-3 py-2 text-sm text-destructive">
              {error}
            </div>
          )}
        </div>
      </div>

      <div className="border-fade-x bg-background">
        <div className="mx-auto max-w-3xl px-6 py-4">
          <Composer disabled={isStreaming || isLoading} onSend={onSend} />
          <p className="mt-2 text-center text-xs text-muted-foreground">
            Enter to send · Shift+Enter for a new line
          </p>
        </div>
      </div>
    </main>
  )
}
