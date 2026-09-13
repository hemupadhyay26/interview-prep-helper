import { useEffect, useRef, useState } from 'react'
import { Loader2Icon, LinkIcon, RotateCcwIcon } from 'lucide-react'
import { CopyButton } from '@/components/animate-ui/components/buttons/copy'
import { Button } from '@/components/animate-ui/components/buttons/button'
import {
  Dialog,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogPopup,
  DialogTitle,
} from '@/components/animate-ui/components/base/dialog'
import Composer from './Composer'
import Markdown from './Markdown'
import type { ChatMessage, Job } from '@/types'

function hostOf(url: string) {
  try {
    return new URL(url).host.replace(/^www\./, '')
  } catch {
    return url
  }
}

function JobBar({
  job,
  onSubmit,
}: {
  job: Job | null
  onSubmit: (url: string) => Promise<void>
}) {
  const [open, setOpen] = useState(false)
  const [url, setUrl] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const openDialog = () => {
    setUrl(job?.source_url ?? '')
    setError(null)
    setOpen(true)
  }

  const submit = async () => {
    const value = url.trim()
    if (!value || busy) return
    setBusy(true)
    setError(null)
    try {
      await onSubmit(value)
      setOpen(false)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not add that link')
    } finally {
      setBusy(false)
    }
  }

  const label = job
    ? job.title
      ? `${job.title}${job.company ? ` · ${job.company}` : ''}`
      : hostOf(job.source_url)
    : null

  return (
    <div className="mb-2 flex items-center gap-2 text-xs">
      <button
        type="button"
        onClick={openDialog}
        className="inline-flex shrink-0 items-center gap-1.5 rounded-md px-2 py-1 text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
      >
        <LinkIcon className="size-3.5" />
        {job ? 'Change job link' : 'Add job link'}
      </button>

      {job && (
        <a
          href={job.source_url}
          target="_blank"
          rel="noreferrer"
          title={job.source_url}
          className="inline-flex min-w-0 items-center gap-1 rounded-md bg-accent px-2 py-1 text-muted-foreground transition-colors hover:text-foreground"
        >
          <span className="truncate">{label}</span>
        </a>
      )}

      <Dialog
        open={open}
        onOpenChange={(o) => {
          setOpen(o)
          if (!o) setError(null)
        }}
      >
        <DialogPopup className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>
              {job ? 'Change the job posting' : 'Add a job posting'}
            </DialogTitle>
            <DialogDescription>
              Paste the job posting URL. It gets scraped and structured, and
              the assistant grounds its questions in that role from the next
              message on. It stays attached to this conversation.
            </DialogDescription>
          </DialogHeader>

          <input
            type="url"
            autoFocus
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') submit()
            }}
            placeholder="https://…"
            className="w-full rounded-md border bg-background px-3 py-2 text-sm outline-none focus:border-ring focus:ring-[3px] focus:ring-ring/50"
          />

          {error && <p className="text-xs text-destructive">{error}</p>}

          <DialogFooter>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setOpen(false)}
              disabled={busy}
            >
              Cancel
            </Button>
            <Button
              size="sm"
              onClick={submit}
              disabled={busy || url.trim() === ''}
            >
              {busy ? (
                <>
                  <Loader2Icon className="size-3.5 animate-spin" />
                  Fetching…
                </>
              ) : job ? (
                'Update'
              ) : (
                'Add'
              )}
            </Button>
          </DialogFooter>
        </DialogPopup>
      </Dialog>
    </div>
  )
}

function RegenerateButton({
  onClick,
  className,
}: {
  onClick: () => void
  className?: string
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-label="Regenerate response"
      title="Regenerate response"
      className={
        'inline-flex size-7 items-center justify-center rounded-md text-muted-foreground transition-colors hover:bg-accent hover:text-accent-foreground ' +
        (className ?? '')
      }
    >
      <RotateCcwIcon className="size-3.5" />
    </button>
  )
}

interface ChatPanelProps {
  messages: ChatMessage[]
  isStreaming: boolean
  error: string | null
  isLoading: boolean
  onSend: (text: string) => void
  onAddJobLink: (url: string) => Promise<void>
  job: Job | null
  sessionId: string | null
  sessionTitle?: string
}

function MessagesSkeleton() {
  return (
    <div className="space-y-6" role="status" aria-label="Loading conversation">
      {[
        { align: 'end', widths: ['60%', '40%'] },
        { align: 'start', widths: ['85%', '92%', '70%'] },
        { align: 'end', widths: ['50%'] },
        { align: 'start', widths: ['80%', '65%'] },
      ].map((row, i) => (
        <div
          key={i}
          className={row.align === 'end' ? 'flex justify-end' : ''}
        >
          <div
            className={
              row.align === 'end'
                ? 'w-[70%] space-y-2 rounded-2xl rounded-br-sm bg-primary/10 p-3'
                : 'w-full space-y-2'
            }
          >
            {row.widths.map((w, j) => (
              <div
                key={j}
                className="h-3.5 animate-pulse rounded bg-muted-foreground/15"
                style={{ width: w, animationDelay: `${(i * 3 + j) * 90}ms` }}
              />
            ))}
          </div>
        </div>
      ))}
    </div>
  )
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
  onAddJobLink,
  job,
  sessionId,
  sessionTitle,
}: ChatPanelProps) {
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const el = scrollRef.current
    if (el) el.scrollTop = el.scrollHeight
  }, [messages, isStreaming])

  const showEmpty = !isLoading && messages.length === 0

  // The most recent user turn — re-sent when "Regenerate" is clicked.
  const lastUserText = [...messages].reverse().find((m) => m.role === 'user')
    ?.content
  const lastMessageId = messages[messages.length - 1]?.id
  const canRegenerate =
    !isLoading && !isStreaming && Boolean(lastUserText)

  const regenerate = () => {
    if (canRegenerate && lastUserText) onSend(lastUserText)
  }

  return (
    <main className="border-fade-x flex min-w-0 flex-1 flex-col">
      {sessionId && (
        <header className="flex items-center justify-between gap-3 px-6 py-2.5">
          <span className="truncate text-sm font-medium text-muted-foreground">
            {sessionTitle || 'Untitled'}
          </span>
        </header>
      )}

      <div ref={scrollRef} className="flex-1 overflow-y-auto">
        <div className="mx-auto max-w-3xl space-y-6 px-6 py-8">
          {isLoading && <MessagesSkeleton />}
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
                  <div className="mt-2 flex items-center gap-1 opacity-0 transition-opacity group-hover:opacity-100">
                    <CopyButton
                      content={m.content}
                      variant="ghost"
                      size="xs"
                      aria-label="Copy response"
                    />
                    {m.id === lastMessageId && canRegenerate && (
                      <RegenerateButton onClick={regenerate} />
                    )}
                  </div>
                )}
              </div>
            )
          })}

          {error && (
            <div className="mt-3 rounded-md border border-destructive/40 bg-destructive/10 px-3 py-2 text-sm text-destructive">
              <span>{error}</span>
              {canRegenerate && (
                <div className="mt-2">
                  <RegenerateButton
                    onClick={regenerate}
                    className="text-destructive hover:bg-destructive/10 hover:text-destructive"
                  />
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      <div className="border-fade-x bg-background">
        <div className="mx-auto max-w-3xl px-6 py-4">
          <JobBar job={job} onSubmit={onAddJobLink} />
          <Composer disabled={isLoading} sending={isStreaming} onSend={onSend} />
          <p className="mt-2 text-center text-xs text-muted-foreground">
            Enter to send · Shift+Enter for a new line
          </p>
        </div>
      </div>
    </main>
  )
}
