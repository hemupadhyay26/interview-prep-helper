import { useCallback, useEffect, useState } from 'react'
import Sidebar from './components/Sidebar'
import ChatPanel from './components/ChatPanel'
import { useSessions } from './hooks/useSessions'
import { useSessionMessages } from './hooks/useSessionMessages'
import { useSessionMutations } from './hooks/useSessionMutations'
import { useChatStream } from './hooks/useChatStream'
import { useAddJob, useJob } from './hooks/useJob'

export default function App() {
  // `null` means "no explicit choice yet" — fall back to the newest session.
  const [selectedId, setSelectedId] = useState<string | null>(null)

  const sessionsQuery = useSessions()
  const sessions = sessionsQuery.data ?? []

  const activeId = selectedId ?? sessions[0]?.session_id ?? null

  const messagesQuery = useSessionMessages(activeId)
  const { create, rename, remove } = useSessionMutations()
  const addJob = useAddJob()
  const jobQuery = useJob(activeId)
  const {
    overlay,
    isStreaming,
    error: chatError,
    send: sendChat,
    reset: resetChat,
  } = useChatStream()

  const messages = [...(messagesQuery.data ?? []), ...overlay]
  const activeTitle = sessions.find((s) => s.session_id === activeId)?.title

  // Drop any in-flight stream state when switching conversations.
  useEffect(() => {
    resetChat()
  }, [activeId, resetChat])

  const handleNew = useCallback(async () => {
    const created = await create.mutateAsync()
    setSelectedId(created.session_id)
  }, [create])

  const handleRename = useCallback(
    (id: string, title: string) => rename.mutate({ id, title }),
    [rename],
  )

  const handleDelete = useCallback(
    (id: string) => {
      remove.mutate(id, {
        onSuccess: () => {
          // Fall back to the newest remaining session.
          if (id === activeId) setSelectedId(null)
        },
      })
    },
    [remove, activeId],
  )

  const handleSend = useCallback(
    async (text: string) => {
      let sessionId = activeId
      if (!sessionId) {
        const created = await create.mutateAsync()
        sessionId = created.session_id
        setSelectedId(created.session_id)
      }
      await sendChat(sessionId, text)
    },
    [activeId, create, sendChat],
  )

  const handleAddJobLink = useCallback(
    async (url: string) => {
      // Attach the job to the conversation the user is already in. Only
      // spin up a session when there genuinely isn't one yet.
      let sessionId = activeId
      if (!sessionId) {
        const created = await create.mutateAsync()
        sessionId = created.session_id
        setSelectedId(created.session_id)
      }
      await addJob.mutateAsync({ sessionId, url })
    },
    [activeId, create, addJob],
  )

  return (
    <div className="flex h-full">
      <Sidebar
        sessions={sessions}
        activeId={activeId}
        isLoading={sessionsQuery.isLoading}
        onSelect={setSelectedId}
        onNew={handleNew}
        onRename={handleRename}
        onDelete={handleDelete}
      />
      <ChatPanel
        messages={messages}
        isStreaming={isStreaming}
        error={chatError}
        isLoading={Boolean(activeId) && messagesQuery.isLoading}
        onSend={handleSend}
        onAddJobLink={handleAddJobLink}
        job={jobQuery.data ?? null}
        sessionId={activeId}
        sessionTitle={activeTitle}
      />
    </div>
  )
}
