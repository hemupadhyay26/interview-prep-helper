/**
 * Central registry of TanStack Query keys. Import from here instead of
 * writing key arrays inline so invalidation stays consistent.
 */
export const queryKeys = {
  sessions: ['sessions'] as const,
  session: (id: string) => ['sessions', id] as const,
  resume: ['resume'] as const,
}
