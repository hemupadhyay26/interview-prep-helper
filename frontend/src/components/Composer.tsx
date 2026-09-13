import { useEffect, useRef, useState } from 'react'
import { SendHorizontalIcon } from 'lucide-react'
import { RippleButton } from '@/components/animate-ui/components/buttons/ripple'

interface ComposerProps {
  /** Hard-disable the input (e.g. history still loading). */
  disabled?: boolean
  /** A reply is streaming: block sending, but keep the field typeable. */
  sending?: boolean
  onSend: (text: string) => void
}

export default function Composer({ disabled, sending, onSend }: ComposerProps) {
  const [value, setValue] = useState('')
  const taRef = useRef<HTMLTextAreaElement>(null)

  function resize() {
    const ta = taRef.current
    if (!ta) return
    ta.style.height = 'auto'
    ta.style.height = `${Math.min(ta.scrollHeight, 200)}px`
  }

  function submit() {
    const text = value.trim()
    if (!text || disabled || sending) return
    onSend(text)
    setValue('')
    requestAnimationFrame(() => {
      resize()
      // Keep the caret in the box so the conversation can continue.
      taRef.current?.focus()
    })
  }

  // When a reply finishes streaming (or history finishes loading), return
  // focus to the textarea so the user can keep typing without clicking.
  useEffect(() => {
    if (!disabled && !sending) taRef.current?.focus()
  }, [disabled, sending])

  return (
    <form
      className="flex items-end gap-2 rounded-2xl border bg-card p-2 shadow-xs focus-within:border-ring focus-within:ring-[3px] focus-within:ring-ring/50"
      onSubmit={(e) => {
        e.preventDefault()
        submit()
      }}
    >
      <textarea
        ref={taRef}
        rows={1}
        className="max-h-[200px] flex-1 resize-none bg-transparent px-2 py-1.5 text-sm outline-none placeholder:text-muted-foreground"
        placeholder="Ask about your interview, a role, or request practice questions…"
        value={value}
        disabled={disabled}
        onChange={(e) => {
          setValue(e.target.value)
          resize()
        }}
        onKeyDown={(e) => {
          if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault()
            submit()
          }
        }}
      />
      <RippleButton
        type="submit"
        size="icon"
        disabled={disabled || sending || value.trim() === ''}
        aria-label="Send message"
      >
        <SendHorizontalIcon />
      </RippleButton>
    </form>
  )
}
