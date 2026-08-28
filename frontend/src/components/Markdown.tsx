import { Fragment, type ReactNode } from 'react'

/**
 * Deliberately tiny Markdown renderer — no dependencies. Handles the
 * subset the interview agent actually produces: fenced code blocks,
 * inline code, bold / italic, headings, and ordered / unordered lists.
 */

function renderInline(text: string, keyPrefix: string): ReactNode[] {
  // Split on `code`, **bold**, *italic* while keeping the delimiters.
  const tokens = text.split(/(`[^`]+`|\*\*[^*]+\*\*|\*[^*]+\*)/g)
  return tokens.map((tok, i) => {
    const key = `${keyPrefix}-${i}`
    if (tok.startsWith('`') && tok.endsWith('`')) {
      return (
        <code
          key={key}
          className="rounded bg-muted px-1.5 py-0.5 font-mono text-[0.85em]"
        >
          {tok.slice(1, -1)}
        </code>
      )
    }
    if (tok.startsWith('**') && tok.endsWith('**')) {
      return (
        <strong key={key} className="font-semibold">
          {tok.slice(2, -2)}
        </strong>
      )
    }
    if (tok.startsWith('*') && tok.endsWith('*') && tok.length > 2) {
      return (
        <em key={key} className="italic">
          {tok.slice(1, -1)}
        </em>
      )
    }
    return <Fragment key={key}>{tok}</Fragment>
  })
}

export default function Markdown({ text }: { text: string }) {
  const blocks: ReactNode[] = []
  const lines = text.split('\n')

  let i = 0
  let blockKey = 0

  while (i < lines.length) {
    const line = lines[i]

    // Fenced code block
    if (line.trimStart().startsWith('```')) {
      const code: string[] = []
      i++
      while (i < lines.length && !lines[i].trimStart().startsWith('```')) {
        code.push(lines[i])
        i++
      }
      i++ // closing fence
      blocks.push(
        <pre
          key={blockKey++}
          className="my-3 overflow-x-auto rounded-lg border bg-muted p-3 text-[0.85em]"
        >
          <code className="font-mono">{code.join('\n')}</code>
        </pre>,
      )
      continue
    }

    // Blank line
    if (line.trim() === '') {
      i++
      continue
    }

    // Heading
    const heading = line.match(/^(#{1,4})\s+(.*)$/)
    if (heading) {
      blocks.push(
        <h4
          key={blockKey++}
          className="mt-4 mb-2 text-sm font-semibold first:mt-0"
        >
          {renderInline(heading[2], `h${blockKey}`)}
        </h4>,
      )
      i++
      continue
    }

    // List (ordered or unordered)
    if (/^\s*([-*+]|\d+[.)])\s+/.test(line)) {
      const ordered = /^\s*\d+[.)]\s+/.test(line)
      const items: ReactNode[] = []
      while (i < lines.length && /^\s*([-*+]|\d+[.)])\s+/.test(lines[i])) {
        const content = lines[i].replace(/^\s*([-*+]|\d+[.)])\s+/, '')
        items.push(
          <li key={items.length}>
            {renderInline(content, `li${blockKey}-${items.length}`)}
          </li>,
        )
        i++
      }
      const listClass = 'my-3 space-y-1.5 pl-6'
      blocks.push(
        ordered ? (
          <ol key={blockKey++} className={`${listClass} list-decimal`}>
            {items}
          </ol>
        ) : (
          <ul key={blockKey++} className={`${listClass} list-disc`}>
            {items}
          </ul>
        ),
      )
      continue
    }

    // Paragraph — gather consecutive plain lines
    const para: string[] = []
    while (
      i < lines.length &&
      lines[i].trim() !== '' &&
      !lines[i].trimStart().startsWith('```') &&
      !/^\s*([-*+]|\d+[.)])\s+/.test(lines[i]) &&
      !/^#{1,4}\s+/.test(lines[i])
    ) {
      para.push(lines[i])
      i++
    }
    blocks.push(
      <p key={blockKey++} className="my-3 first:mt-0 last:mb-0">
        {renderInline(para.join('\n'), `p${blockKey}`)}
      </p>,
    )
  }

  return <>{blocks}</>
}
