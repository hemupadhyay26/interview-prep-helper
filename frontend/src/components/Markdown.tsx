import { Fragment, type ReactNode } from 'react'

/**
 * Deliberately tiny Markdown renderer — no dependencies. Handles the
 * subset the interview agent actually produces: fenced code blocks,
 * inline code, bold / italic, links, headings, ordered / unordered
 * lists (incl. blank-line-separated "loose" lists), blockquotes, and
 * horizontal rules — the shapes a one-question-at-a-time mock interview
 * (question, then feedback, then the next question) comes back in.
 */

function renderInline(text: string, keyPrefix: string): ReactNode[] {
  // Split on `code`, [link](url), **bold**, *italic* — keep the delimiters.
  const tokens = text.split(
    /(`[^`]+`|\[[^\]]+\]\([^)]+\)|\*\*[^*]+\*\*|\*[^*]+\*)/g,
  )
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
    const link = tok.match(/^\[([^\]]+)\]\(([^)]+)\)$/)
    if (link) {
      return (
        <a
          key={key}
          href={link[2]}
          target="_blank"
          rel="noreferrer"
          className="text-primary underline underline-offset-2"
        >
          {link[1]}
        </a>
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

    // Horizontal rule — the agent separates feedback from the next
    // question with one of these.
    if (/^\s*([-*_])(\s*\1){2,}\s*$/.test(line)) {
      blocks.push(<hr key={blockKey++} className="my-4 border-border" />)
      i++
      continue
    }

    // Blockquote — the agent may pose the interview question as a quote.
    if (/^\s*>\s?/.test(line)) {
      const quoted: string[] = []
      while (i < lines.length && /^\s*>\s?/.test(lines[i])) {
        quoted.push(lines[i].replace(/^\s*>\s?/, ''))
        i++
      }
      blocks.push(
        <blockquote
          key={blockKey++}
          className="my-3 whitespace-pre-line border-l-2 border-border pl-3 text-muted-foreground"
        >
          {renderInline(quoted.join('\n'), `q${blockKey}`)}
        </blockquote>,
      )
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
    const itemRe = /^\s*([-*+]|\d+[.)])\s+/
    const orderedRe = /^\s*\d+[.)]\s+/
    if (itemRe.test(line)) {
      const ordered = orderedRe.test(line)
      const startMatch = line.match(/^\s*(\d+)[.)]\s+/)
      const start = startMatch ? Number(startMatch[1]) : 1
      const items: ReactNode[] = []
      while (i < lines.length) {
        if (itemRe.test(lines[i])) {
          const content = lines[i].replace(itemRe, '')
          items.push(
            <li key={items.length}>
              {renderInline(content, `li${blockKey}-${items.length}`)}
            </li>,
          )
          i++
          continue
        }
        // A single blank line between two items of the same kind is a
        // "loose" list — stay in the same <ol>/<ul> instead of starting
        // a fresh one (which would restart numbering at 1).
        if (
          lines[i].trim() === '' &&
          i + 1 < lines.length &&
          itemRe.test(lines[i + 1]) &&
          orderedRe.test(lines[i + 1]) === ordered
        ) {
          i++
          continue
        }
        break
      }
      const listClass = 'my-3 space-y-1.5 pl-6'
      blocks.push(
        ordered ? (
          <ol
            key={blockKey++}
            start={start}
            className={`${listClass} list-decimal`}
          >
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

    // Paragraph — gather consecutive plain lines, stopping at anything
    // that starts a different block.
    const para: string[] = []
    while (
      i < lines.length &&
      lines[i].trim() !== '' &&
      !lines[i].trimStart().startsWith('```') &&
      !itemRe.test(lines[i]) &&
      !/^#{1,4}\s+/.test(lines[i]) &&
      !/^\s*>\s?/.test(lines[i]) &&
      !/^\s*([-*_])(\s*\1){2,}\s*$/.test(lines[i])
    ) {
      para.push(lines[i])
      i++
    }
    blocks.push(
      <p
        key={blockKey++}
        className="my-3 whitespace-pre-line first:mt-0 last:mb-0"
      >
        {renderInline(para.join('\n'), `p${blockKey}`)}
      </p>,
    )
  }

  return <>{blocks}</>
}
