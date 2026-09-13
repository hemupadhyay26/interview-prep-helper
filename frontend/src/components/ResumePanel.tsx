import {
  useRef,
  useState,
  type ChangeEvent,
  type DragEvent,
  type ReactNode,
} from 'react'
import { motion } from 'motion/react'
import { FileTextIcon, UploadIcon } from 'lucide-react'
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
import { cn } from '@/lib/utils'
import { useResume, useResumeMutations } from '@/hooks/useResume'
import type { Resume } from '@/types'

const ACCEPT = '.pdf'
const ACCEPT_EXT = ['pdf']

function hasAcceptedExt(name: string) {
  const ext = name.split('.').pop()?.toLowerCase() ?? ''
  return ACCEPT_EXT.includes(ext)
}

/**
 * Resume links often come through without a scheme (e.g.
 * `hemupadhyay26.github.io`). Without one the browser treats the href as
 * relative and resolves it against the current origin, so force https.
 */
function toHref(link: string) {
  const trimmed = link.trim()
  if (/^[a-z][a-z0-9+.-]*:/i.test(trimmed)) return trimmed // already has a scheme
  return `https://${trimmed.replace(/^\/+/, '')}`
}

function linkLabel(link: string) {
  return link.trim().replace(/^[a-z][a-z0-9+.-]*:\/\//i, '').replace(/\/$/, '')
}

function ParsingIndicator() {
  return (
    <span
      className="flex items-center gap-2 px-2 py-1.5 text-xs text-muted-foreground"
      role="status"
      aria-live="polite"
    >
      <span className="flex items-center gap-1">
        {[0, 1, 2].map((i) => (
          <motion.span
            key={i}
            className="size-1.5 rounded-full bg-current"
            animate={{ opacity: [0.25, 1, 0.25], y: [0, -2, 0] }}
            transition={{
              duration: 0.9,
              repeat: Infinity,
              ease: 'easeInOut',
              delay: i * 0.15,
            }}
          />
        ))}
      </span>
      Parsing resume…
    </span>
  )
}

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

function dateRange(start: string, end: string) {
  const s = start.trim()
  const e = end.trim()
  if (s && e) return `${s} – ${e}`
  return s || e || ''
}

function ResumeDetails({ resume }: { resume: Resume }) {
  const { contact } = resume

  return (
    <div className="max-h-[55vh] space-y-4 overflow-y-auto pr-1 text-sm">
      {(resume.name || resume.headline || contact.location) && (
        <Section title="Candidate">
          {resume.name && (
            <p className="font-medium text-foreground">{resume.name}</p>
          )}
          {resume.headline && (
            <p className="text-foreground">{resume.headline}</p>
          )}
          {contact.location && (
            <p className="text-muted-foreground">{contact.location}</p>
          )}
          {(contact.email || contact.phone) && (
            <p className="text-muted-foreground">
              {[contact.email, contact.phone].filter(Boolean).join(' · ')}
            </p>
          )}
          {contact.links.length > 0 && (
            <div className="flex flex-wrap gap-x-3 gap-y-1 pt-0.5">
              {contact.links.map((link, i) => (
                <a
                  key={i}
                  href={toHref(link)}
                  target="_blank"
                  rel="noreferrer"
                  className="truncate text-primary underline-offset-2 hover:underline"
                >
                  {linkLabel(link)}
                </a>
              ))}
            </div>
          )}
        </Section>
      )}

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

      {resume.experience.length > 0 && (
        <Section title="Experience">
          <ul className="space-y-3">
            {resume.experience.map((e, i) => (
              <li key={i} className="space-y-1">
                <div className="flex flex-wrap items-baseline justify-between gap-x-2">
                  <p className="font-medium text-foreground">
                    {[e.title, e.company].filter(Boolean).join(' · ')}
                  </p>
                  <span className="text-xs text-muted-foreground">
                    {dateRange(e.start_date, e.end_date)}
                  </span>
                </div>
                {e.location && (
                  <p className="text-xs text-muted-foreground">{e.location}</p>
                )}
                {e.highlights.length > 0 && (
                  <ul className="list-disc space-y-1 pl-5 text-foreground marker:text-muted-foreground">
                    {e.highlights.map((h, j) => (
                      <li key={j} className="leading-6">
                        {h}
                      </li>
                    ))}
                  </ul>
                )}
              </li>
            ))}
          </ul>
        </Section>
      )}

      {resume.projects.length > 0 && (
        <Section title="Projects">
          <ul className="space-y-3">
            {resume.projects.map((p, i) => (
              <li key={i} className="space-y-1">
                <p className="font-medium text-foreground">
                  {p.name}
                  {p.link && (
                    <>
                      {' '}
                      <a
                        href={toHref(p.link)}
                        target="_blank"
                        rel="noreferrer"
                        className="text-xs font-normal text-primary underline-offset-2 hover:underline"
                      >
                        {linkLabel(p.link)}
                      </a>
                    </>
                  )}
                </p>
                <p className="leading-6 text-muted-foreground">
                  {p.description}
                </p>
                <Chips items={p.technologies} />
              </li>
            ))}
          </ul>
        </Section>
      )}

      {resume.education.length > 0 && (
        <Section title="Education">
          <ul className="space-y-2">
            {resume.education.map((e, i) => (
              <li key={i} className="space-y-0.5">
                <div className="flex flex-wrap items-baseline justify-between gap-x-2">
                  <p className="font-medium text-foreground">
                    {[e.degree, e.institution].filter(Boolean).join(' · ')}
                  </p>
                  <span className="text-xs text-muted-foreground">
                    {dateRange(e.start_date, e.end_date)}
                  </span>
                </div>
                {e.details.length > 0 && (
                  <p className="text-muted-foreground">
                    {e.details.join(' · ')}
                  </p>
                )}
              </li>
            ))}
          </ul>
        </Section>
      )}

      {resume.certifications.length > 0 && (
        <Section title="Certifications">
          <ul className="list-disc space-y-1 pl-5 text-foreground marker:text-muted-foreground">
            {resume.certifications.map((c, i) => (
              <li key={i} className="leading-6">
                {c}
              </li>
            ))}
          </ul>
        </Section>
      )}

      {resume.awards.length > 0 && (
        <Section title="Awards">
          <ul className="list-disc space-y-1 pl-5 text-foreground marker:text-muted-foreground">
            {resume.awards.map((a, i) => (
              <li key={i} className="leading-6">
                {a}
              </li>
            ))}
          </ul>
        </Section>
      )}

      {resume.languages.length > 0 && (
        <Section title="Languages">
          <Chips items={resume.languages} />
        </Section>
      )}
    </div>
  )
}

export default function ResumePanel() {
  const { data: resume } = useResume()
  const { upload, remove } = useResumeMutations()
  const [open, setOpen] = useState(false)
  const [dragActive, setDragActive] = useState(false)
  const fileRef = useRef<HTMLInputElement>(null)
  // dragenter/dragleave fire for every child element — count depth so the
  // highlight only clears when the pointer actually leaves the drop zone.
  const dragDepth = useRef(0)

  const pickFile = () => fileRef.current?.click()

  const handleFile = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    e.target.value = '' // allow re-picking the same file
    if (file) upload.mutate(file)
  }

  const handleDragEnter = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    dragDepth.current += 1
    if (e.dataTransfer.types.includes('Files')) setDragActive(true)
  }

  const handleDragOver = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    e.dataTransfer.dropEffect = 'copy'
  }

  const handleDragLeave = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    dragDepth.current -= 1
    if (dragDepth.current <= 0) {
      dragDepth.current = 0
      setDragActive(false)
    }
  }

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    dragDepth.current = 0
    setDragActive(false)
    const file = e.dataTransfer.files?.[0]
    if (file && hasAcceptedExt(file.name)) upload.mutate(file)
  }

  return (
    <div
      className={cn(
        'relative flex flex-col gap-1 rounded-md transition-colors',
        dragActive &&
          'outline-2 outline-dashed outline-offset-2 outline-ring bg-accent/40',
      )}
      onDragEnter={handleDragEnter}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      <input
        ref={fileRef}
        type="file"
        accept={ACCEPT}
        className="hidden"
        onChange={handleFile}
      />

      {dragActive && (
        <div className="pointer-events-none absolute inset-0 z-10 flex items-center justify-center rounded-md bg-background/70 text-xs font-medium text-foreground backdrop-blur-sm">
          Drop PDF to upload
        </div>
      )}

      {upload.isPending ? (
        <ParsingIndicator />
      ) : resume ? (
        <button
          type="button"
          onClick={() => setOpen(true)}
          className="flex w-full items-center gap-1.5 rounded-md border bg-card px-2.5 py-1.5 text-xs text-foreground transition-colors hover:bg-accent"
          title={`${resume.filename} — view parsed resume`}
        >
          <FileTextIcon className="size-3.5 shrink-0 text-muted-foreground" />
          <span className="truncate">{resume.filename}</span>
        </button>
      ) : (
        <RippleButton
          variant="outline"
          size="sm"
          className="w-full"
          onClick={pickFile}
          aria-label="Upload resume"
        >
          <UploadIcon />
          Upload resume
        </RippleButton>
      )}

      {!upload.isPending && !resume && (
        <p className="px-2 text-[11px] text-muted-foreground/70">
          or drag &amp; drop a PDF here
        </p>
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
