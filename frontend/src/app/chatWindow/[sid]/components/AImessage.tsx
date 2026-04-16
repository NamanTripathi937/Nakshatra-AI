import React from "react"
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"
import rehypeHighlight from "rehype-highlight"
import rehypeRaw from "rehype-raw"

interface AIMessageProps {
  id: string
  content: string
  isNew?: boolean // true for new messages (animate), false for restored messages (skip animation)
}

function useTypingEffect(text: string, id: string, isNew: boolean): string {
  const [displayed, setDisplayed] = React.useState("")
  const timeoutIds = React.useRef<NodeJS.Timeout[]>([])

  React.useEffect(() => {
    // If message is restored from the server, skip the first-render typing animation
    if (!isNew) {
      setDisplayed(text)
      return
    }

    // Otherwise, animate from the beginning
    setDisplayed("")
    timeoutIds.current = []
    let i = 0

    function typeNext() {
      // bigger chunks = faster
      const chunkSize = Math.floor(Math.random() * 4) + 20 // 20–35 chars
      const nextChunk = text.slice(i, i + chunkSize)
      setDisplayed(prev => prev + nextChunk)
      i += chunkSize

      if (i < text.length) {
        // shorter delays = faster speed
        const delay = Math.floor(Math.random() * 40) + 0 // 0–40ms
        const timeoutId = setTimeout(typeNext, delay)
        timeoutIds.current.push(timeoutId)
      }
    }

    typeNext()

    // Cleanup: clear all pending timeouts
    return () => {
      timeoutIds.current.forEach(clearTimeout)
      timeoutIds.current = []
    }
  }, [id, text, isNew])

  return displayed
}


export default function AIMessage({ id, content, isNew = false }: AIMessageProps) {
  const typed = useTypingEffect(content, id, isNew)

  return (
    <div className="max-w-none text-[15px] leading-7 text-slate-100">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeHighlight, rehypeRaw]}
        components={{
          h1: ({ node, ...props }) => (
            <h1
              className="mb-4 bg-gradient-to-r from-amber-200 via-white to-sky-200 bg-clip-text text-3xl font-semibold leading-tight text-transparent"
              {...props}
            />
          ),
          h2: ({ node, ...props }) => (
            <h2
              className="mb-4 border-b border-white/10 pb-3 text-2xl font-semibold leading-tight tracking-tight text-white"
              {...props}
            />
          ),
          h3: ({ node, ...props }) => (
            <h3
              className="mt-6 mb-3 flex items-center gap-2 text-base font-semibold tracking-wide text-amber-100"
              {...props}
            />
          ),
          p: ({ node, ...props }) => (
            <p
              className="mb-4 text-[15px] leading-7 text-slate-200"
              {...props}
            />
          ),
          strong: ({ node, ...props }) => (
            <strong
              className="font-semibold text-white"
              {...props}
            />
          ),
          ul: ({ node, ...props }) => (
            <ul
              className="mb-4 list-disc space-y-2 pl-5 marker:text-amber-300"
              {...props}
            />
          ),
          ol: ({ node, ...props }) => (
            <ol
              className="mb-4 list-decimal space-y-2 pl-5 marker:text-amber-300"
              {...props}
            />
          ),
          li: ({ node, ...props }) => (
            <li
              className="pl-1 text-slate-200"
              {...props}
            />
          ),
          blockquote: ({ node, ...props }) => (
            <blockquote
              className="my-5 rounded-2xl border border-amber-200/15 bg-white/5 px-4 py-3 text-slate-100 shadow-[inset_0_1px_0_rgba(255,255,255,0.06)]"
              {...props}
            />
          ),
          hr: ({ node, ...props }) => (
            <hr
              className="my-5 border-white/10"
              {...props}
            />
          ),
          a: ({ node, ...props }) => (
            <a
              className="font-medium text-sky-300 underline decoration-sky-400/60 underline-offset-4 transition-colors hover:text-sky-200"
              {...props}
            />
          ),
          code: ({ node, className, children, ...props }) => {
            const isBlock = Boolean(className)

            if (isBlock) {
              return (
                <code
                  className={`${className} block overflow-x-auto rounded-2xl border border-white/10 bg-black/40 p-4 text-[13px] leading-6 text-slate-100`}
                  {...props}
                >
                  {children}
                </code>
              )
            }

            return (
              <code
                className="rounded-md border border-white/10 bg-white/8 px-1.5 py-0.5 text-[13px] text-amber-100"
                {...props}
              >
                {children}
              </code>
            )
          },
          table: ({ node, ...props }) => (
            <table
              className="my-4 w-full overflow-hidden rounded-2xl border border-white/10 border-collapse shadow-md"
              {...props}
            />
          ),
          thead: ({ node, ...props }) => (
            <thead
              className="bg-gradient-to-r from-slate-800/95 via-blue-900/85 to-cyan-800/80 text-slate-100"
              {...props}
            />
          ),
          th: ({ node, ...props }) => (
            <th
              className="border border-white/10 px-4 py-2 text-left font-semibold"
              {...props}
            />
          ),
          td: ({ node, ...props }) => (
            <td
              className="border border-white/10 px-4 py-2 text-slate-200"
              {...props}
            />
          ),
          tr: ({ node, ...props }) => (
            <tr
              className="odd:bg-white/4 even:bg-white/[0.02] transition-colors hover:bg-white/8"
              {...props}
            />
          ),
        }}
      >
        {typed}
      </ReactMarkdown>

      {typed.length < content.length && <span className="animate-pulse">▌</span>}
    </div>
  )
}
