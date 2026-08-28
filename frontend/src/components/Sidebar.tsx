import { useEffect, useRef, useState } from 'react'
import { PanelLeftIcon, PencilIcon, PlusIcon, Trash2Icon } from 'lucide-react'
import { RippleButton } from '@/components/animate-ui/components/buttons/ripple'
import { IconButton } from '@/components/animate-ui/components/buttons/icon'
import { Button } from '@/components/animate-ui/components/buttons/button'
import { ThemeTogglerButton } from '@/components/animate-ui/components/buttons/theme-toggler'
import {
  Dialog,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogPopup,
  DialogTitle,
} from '@/components/animate-ui/components/base/dialog'
import { cn } from '@/lib/utils'
import ResumePanel from './ResumePanel'
import type { SessionSummary } from '@/types'

interface SidebarProps {
  sessions: SessionSummary[]
  activeId: string | null
  isLoading: boolean
  onSelect: (id: string) => void
  onNew: () => void
  onRename: (id: string, title: string) => void
  onDelete: (id: string) => void
}

interface SessionRowProps {
  session: SessionSummary
  active: boolean
  onSelect: (id: string) => void
  onRename: (id: string, title: string) => void
  onRequestDelete: (session: SessionSummary) => void
}

function SessionRow({
  session,
  active,
  onSelect,
  onRename,
  onRequestDelete,
}: SessionRowProps) {
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState(session.title)
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (editing) {
      inputRef.current?.focus()
      inputRef.current?.select()
    }
  }, [editing])

  function commit() {
    const next = draft.trim()
    setEditing(false)
    if (next && next !== session.title) onRename(session.session_id, next)
    else setDraft(session.title)
  }

  return (
    <div
      className={cn(
        'group flex items-center gap-1 rounded-lg px-2 py-1.5 text-sm',
        active
          ? 'bg-sidebar-accent text-sidebar-accent-foreground'
          : 'text-sidebar-foreground/80 hover:bg-sidebar-accent/60',
      )}
    >
      {editing ? (
        <input
          ref={inputRef}
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onBlur={commit}
          onKeyDown={(e) => {
            if (e.key === 'Enter') commit()
            if (e.key === 'Escape') {
              setDraft(session.title)
              setEditing(false)
            }
          }}
          className="flex-1 rounded border border-ring bg-background px-1.5 py-0.5 text-sm outline-none"
        />
      ) : (
        <button
          type="button"
          onClick={() => onSelect(session.session_id)}
          className="flex-1 truncate text-left"
          title={session.title}
        >
          {session.title || 'Untitled'}
        </button>
      )}

      <div className="flex shrink-0 items-center gap-0.5 opacity-0 transition-opacity group-hover:opacity-100 focus-within:opacity-100">
        <IconButton
          size="xs"
          variant="ghost"
          aria-label="Rename conversation"
          onClick={() => {
            setDraft(session.title)
            setEditing(true)
          }}
        >
          <PencilIcon />
        </IconButton>
        <IconButton
          size="xs"
          variant="ghost"
          aria-label="Delete conversation"
          onClick={() => onRequestDelete(session)}
        >
          <Trash2Icon />
        </IconButton>
      </div>
    </div>
  )
}

export default function Sidebar({
  sessions,
  activeId,
  isLoading,
  onSelect,
  onNew,
  onRename,
  onDelete,
}: SidebarProps) {
  const [pendingDelete, setPendingDelete] = useState<SessionSummary | null>(null)
  const [collapsed, setCollapsed] = useState(() => {
    try {
      return localStorage.getItem('sidebar:collapsed') === '1'
    } catch {
      return false
    }
  })

  const toggleCollapsed = () =>
    setCollapsed((prev) => {
      const next = !prev
      try {
        localStorage.setItem('sidebar:collapsed', next ? '1' : '0')
      } catch {
        // ignore — collapse still works for this session
      }
      return next
    })

  if (collapsed) {
    return (
      <aside className="border-fade-y flex w-14 shrink-0 flex-col items-center gap-1 bg-sidebar py-3 text-sidebar-foreground">
        <IconButton
          size="sm"
          variant="ghost"
          aria-label="Expand sidebar"
          onClick={toggleCollapsed}
        >
          <PanelLeftIcon />
        </IconButton>
        <IconButton
          size="sm"
          variant="ghost"
          aria-label="New chat"
          onClick={onNew}
        >
          <PlusIcon />
        </IconButton>
        <div className="flex-1" />
        <ThemeTogglerButton variant="ghost" size="sm" />
      </aside>
    )
  }

  return (
    <aside className="border-fade-y flex w-64 shrink-0 flex-col bg-sidebar text-sidebar-foreground">
      <div className="flex items-center justify-between px-4 py-3">
        <span className="font-semibold tracking-tight">Prep Helper</span>
        <div className="flex items-center gap-0.5">
          <ThemeTogglerButton variant="ghost" size="sm" />
          <IconButton
            size="sm"
            variant="ghost"
            aria-label="Collapse sidebar"
            onClick={toggleCollapsed}
          >
            <PanelLeftIcon />
          </IconButton>
        </div>
      </div>

      <div className="px-3 pb-2">
        <RippleButton
          variant="default"
          size="sm"
          className="w-full"
          onClick={onNew}
        >
          <PlusIcon />
          New chat
        </RippleButton>
      </div>

      <nav className="flex-1 space-y-0.5 overflow-y-auto px-3 py-2">
        {isLoading && sessions.length === 0 && (
          <p className="px-2 py-3 text-sm text-muted-foreground">Loading…</p>
        )}
        {!isLoading && sessions.length === 0 && (
          <p className="px-2 py-3 text-sm text-muted-foreground">
            No conversations yet
          </p>
        )}
        {sessions.map((s) => (
          <SessionRow
            key={s.session_id}
            session={s}
            active={s.session_id === activeId}
            onSelect={onSelect}
            onRename={onRename}
            onRequestDelete={setPendingDelete}
          />
        ))}
      </nav>

      <div className="border-t border-sidebar-border px-3 py-3">
        <p className="mb-1.5 px-0.5 text-xs font-semibold uppercase tracking-wide text-sidebar-foreground/60">
          Resume
        </p>
        <ResumePanel />
      </div>

      <Dialog
        open={pendingDelete !== null}
        onOpenChange={(open) => {
          if (!open) setPendingDelete(null)
        }}
      >
        <DialogPopup className="sm:max-w-sm">
          <DialogHeader>
            <DialogTitle>Delete conversation</DialogTitle>
            <DialogDescription>
              &ldquo;{pendingDelete?.title}&rdquo; will be permanently removed.
              This can&apos;t be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPendingDelete(null)}
            >
              Cancel
            </Button>
            <Button
              variant="destructive"
              size="sm"
              onClick={() => {
                if (pendingDelete) onDelete(pendingDelete.session_id)
                setPendingDelete(null)
              }}
            >
              Delete
            </Button>
          </DialogFooter>
        </DialogPopup>
      </Dialog>
    </aside>
  )
}
