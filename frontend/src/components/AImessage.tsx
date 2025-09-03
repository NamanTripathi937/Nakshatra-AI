import React from "react"
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"
import rehypeHighlight from "rehype-highlight"
import rehypeRaw from "rehype-raw"

interface AIMessageProps {
  id: string
  content: string
}

function useTypingEffect(text: string, id: string): string {
  const [displayed, setDisplayed] = React.useState("")

  React.useEffect(() => {
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
      }
    }

    typeNext()

    return () => { i = text.length }
  }, [id, text])

  return displayed
}


export default function AIMessage({ id, content }: AIMessageProps) {
  const typed = useTypingEffect(content, id)

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
