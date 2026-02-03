import React from "react"
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"
import rehypeHighlight from "rehype-highlight"
import rehypeRaw from "rehype-raw"

interface AIMessageProps {
  id: string
  content: string
  isNew?: boolean // true for new messages (animate), false for restored messages (skip animation)
  onTypingComplete?: () => void // callback when typing animation completes
}

function useTypingEffect(text: string, id: string, isNew: boolean, onComplete?: () => void): string {
  const [displayed, setDisplayed] = React.useState("")

  React.useEffect(() => {
    // If message is not new (restored from localStorage), skip animation
    if (!isNew) {
      setDisplayed(text)
      // Call onComplete immediately since there's no animation
      if (onComplete) {
        onComplete()
      }
      return
    }

    // Otherwise, animate from the beginning
    setDisplayed("")
    let i = 0

    function typeNext() {
      // bigger chunks = faster
      const chunkSize = Math.floor(Math.random() * 4) + 20 // 20–35 chars
      const nextChunk = text.slice(i, i + chunkSize)
      setDisplayed(prev => prev + nextChunk)
      i += chunkSize

      if (i < text.length) {
        // shorter delays = faster speed
        const delay = Math.floor(Math.random() * 40) + 0 // 15–55ms
        setTimeout(typeNext, delay)
      } else {
        // Typing complete - call the callback
        if (onComplete) {
          onComplete()
        }
      }
    }

    typeNext()

    return () => { i = text.length }
  }, [id, text, isNew, onComplete])

  return displayed
}


export default function AIMessage({ id, content, isNew = false, onTypingComplete }: AIMessageProps) {
  const typed = useTypingEffect(content, id, isNew)

  return (
    <div className="prose prose-invert text-sm leading-relaxed max-w-none">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeHighlight, rehypeRaw]}
        components={{
          table: ({ node, ...props }) => (
            <table
              className="w-full border-collapse rounded-xl overflow-hidden shadow-md my-4"
              {...props}
            />
          ),
          thead: ({ node, ...props }) => (
            <thead
              className="bg-gradient-to-r from-purple-700 to-indigo-600 text-white"
              {...props}
            />
          ),
          th: ({ node, ...props }) => (
            <th
              className="px-4 py-2 text-left font-semibold border border-gray-700"
              {...props}
            />
          ),
          td: ({ node, ...props }) => (
            <td
              className="px-4 py-2 border border-gray-700 text-gray-200"
              {...props}
            />
          ),
          tr: ({ node, ...props }) => (
            <tr
              className="odd:bg-gray-800 even:bg-gray-900 hover:bg-gray-700 transition-colors"
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
