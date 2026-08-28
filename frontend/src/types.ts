/** Shared domain types for the Prep Helper frontend. */

/** A row in the sidebar session list. */
export interface SessionSummary {
  session_id: string
  title: string
}

/** Full session payload from `GET /sessions/{id}`. */
export interface SessionDetail extends SessionSummary {
  /** pydantic-ai `ModelMessagesTypeAdapter` JSON dump. */
  message_history: string
}

/** `POST /sessions` / `PATCH /sessions/{id}` response. */
export type SessionMutationResult = SessionSummary

/** `event: done` payload from the chat SSE stream. */
export interface ChatDonePayload {
  session_id: string
  title: string
}

export type ChatRole = 'user' | 'assistant'

/** A message as rendered in the chat panel. */
export interface ChatMessage {
  id: string
  role: ChatRole
  content: string
}

/** One project extracted from an uploaded resume. */
export interface ResumeProject {
  name: string
  description: string
  technologies: string[]
}

/**
 * Structured resume attached to a session.
 * `GET/POST /sessions/{id}/resume` response (`ResumeOut`).
 */
export interface Resume {
  session_id: string
  filename: string
  summary: string
  skills: string[]
  projects: ResumeProject[]
  experience: string[]
  education: string[]
}
