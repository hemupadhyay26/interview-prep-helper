import { useRef, useState, type ChangeEvent, type ReactNode } from 'react'
import { FileTextIcon, Loader2Icon, UploadIcon } from 'lucide-react'
import { Button } from '@/components/animate-ui/components/buttons/button'
import { RippleButton } from '@/components/animate-ui/components/buttons/ripple'
import {
  Dialog,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogPopup,
  DialogTitle,
} from '@/components/animate-ui/components/base/dialog'
import { useResume, useResumeMutations } from '@/hooks/useResume'
import type { Resume } from '@/types'

const ACCEPT = '.pdf,.doc,.docx,.txt,.md'

function Chips({ items }: { items: string[] }) {
  if (items.length === 0) return null
  return (
    <div className="flex flex-wrap gap-1.5">
      {items.map((item, i) => (
        <span
          key={i}
          className="rounded-full border bg-muted px-2 py-0.5 text-xs text-muted-foreground"
        >
          {item}
        </span>
      ))}
    </div>
  )
}

function Section({
  title,
  children,
}: {
  title: string
  children: ReactNode
}) {
  return (
    <div className="space-y-1.5">
      <h4 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
        {title}
      </h4>
      {children}
    </div>
  )
}

function ResumeDetails({ resume }: { resume: Resume }) {
  return (
    <div className="max-h-[55vh] space-y-4 overflow-y-auto pr-1 text-sm">
      {resume.summary && (
        <Section title="Summary">
          <p className="leading-6 text-foreground">{resume.summary}</p>
        </Section>
      )}

      {resume.skills.length > 0 && (
        <Section title="Skills">
          <Chips items={resume.skills} />
        </Section>
      )}

      {resume.projects.length > 0 && (
        <Section title="Projects">
          <ul className="space-y-3">
            {resume.projects.map((p, i) => (
              <li key={i} className="space-y-1">
                <p className="font-medium text-foreground">{p.name}</p>
                <p className="leading-6 text-muted-foreground">
                  {p.description}
                </p>
                <Chips items={p.technologies} />
              </li>
            ))}
          </ul>
        </Section>
      )}

      {resume.experience.length > 0 && (
        <Section title="Experience">
          <ul className="list-disc space-y-1.5 pl-5 text-foreground marker:text-muted-foreground">
            {resume.experience.map((e, i) => (
              <li key={i} className="leading-6">
                {e}
              </li>
            ))}
          </ul>
        </Section>
      )}

      {resume.education.length > 0 && (
        <Section title="Education">
          <ul className="list-disc space-y-1.5 pl-5 text-foreground marker:text-muted-foreground">
            {resume.education.map((e, i) => (
              <li key={i} className="leading-6">
                {e}
              </li>
            ))}
          </ul>
        </Section>
      )}
    </div>
  )
}

export default function ResumePanel({
  sessionId,
}: {
  sessionId: string | null
}) {
  const { data: resume } = useResume(sessionId)
  const { upload, remove } = useResumeMutations(sessionId)
  const [open, setOpen] = useState(false)
  const fileRef = useRef<HTMLInputElement>(null)

  if (!sessionId) return null

  const pickFile = () => fileRef.current?.click()

  const handleFile = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    e.target.value = '' // allow re-picking the same file
    if (file) upload.mutate(file)
  }

  return (
    <div className="flex flex-col items-end gap-1">
      <input
        ref={fileRef}
        type="file"
        accept={ACCEPT}
        className="hidden"
        onChange={handleFile}
      />

      {upload.isPending ? (
        <span className="flex items-center gap-1.5 px-2 py-1 text-xs text-muted-foreground">
          <Loader2Icon className="size-3.5 animate-spin" />
          Parsing resume…
        </span>
      ) : resume ? (
        <button
          type="button"
          onClick={() => setOpen(true)}
          className="flex max-w-[220px] items-center gap-1.5 rounded-md border bg-card px-2.5 py-1 text-xs text-foreground transition-colors hover:bg-accent"
          title={`${resume.filename} — view parsed resume`}
        >
          <FileTextIcon className="size-3.5 shrink-0 text-muted-foreground" />
          <span className="truncate">{resume.filename}</span>
        </button>
      ) : (
        <RippleButton
          variant="outline"
          size="sm"
          onClick={pickFile}
          aria-label="Upload resume"
        >
          <UploadIcon />
          Upload resume
        </RippleButton>
      )}

      {upload.isError && (
        <span className="text-xs text-destructive">
          {(upload.error as Error).message}
        </span>
      )}

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogPopup className="sm:max-w-lg">
          <DialogHeader>
            <DialogTitle>Resume</DialogTitle>
            <DialogDescription>{resume?.filename}</DialogDescription>
          </DialogHeader>

          {resume && <ResumeDetails resume={resume} />}

          <DialogFooter>
            <Button variant="outline" size="sm" onClick={pickFile}>
              Replace
            </Button>
            <Button
              variant="destructive"
              size="sm"
              disabled={remove.isPending}
              onClick={() => {
                remove.mutate(undefined, { onSuccess: () => setOpen(false) })
              }}
            >
              Remove
            </Button>
          </DialogFooter>
        </DialogPopup>
      </Dialog>
    </div>
  )
}
