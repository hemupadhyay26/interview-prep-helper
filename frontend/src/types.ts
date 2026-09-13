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

/**
 * The job posting attached to a session (`GET/POST /sessions/{id}/job`,
 * `JobOut`). One per session; the interview agent grounds its questions
 * in it.
 */
export interface Job {
  session_id: string
  source_url: string
  summary: string
  title: string
  company: string
  location: string
  employment_type: string
  seniority: string
  responsibilities: string[]
  required_skills: string[]
  preferred_skills: string[]
  tech_stack: string[]
}

/** One project extracted from an uploaded resume. */
export interface ResumeProject {
  name: string
  description: string
  technologies: string[]
  link: string
}

/** One role in the candidate's work history. */
export interface ResumeExperience {
  company: string
  title: string
  location: string
  start_date: string
  end_date: string
  highlights: string[]
}

/** One degree / school. */
export interface ResumeEducation {
  institution: string
  degree: string
  location: string
  start_date: string
  end_date: string
  details: string[]
}

/** Contact block from the resume header. */
export interface ResumeContact {
  email: string
  phone: string
  location: string
  links: string[]
}

/**
 * The candidate's structured resume. Global (one per app), shared across
 * every session. `GET/POST /resume` response (`ResumeOut`).
 */
export interface Resume {
  filename: string
  name: string
  headline: string
  contact: ResumeContact
  summary: string
  skills: string[]
  experience: ResumeExperience[]
  projects: ResumeProject[]
  education: ResumeEducation[]
  certifications: string[]
  awards: string[]
  languages: string[]
}
