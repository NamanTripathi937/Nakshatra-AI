"use client"

import React, { useState, useRef, useEffect, useCallback } from "react"

import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Textarea } from "@/components/ui/textarea"
import { ScrollArea } from "@/components/ui/scroll-area"
import BillingPlansModal from "@/components/BillingPlansModal"
import GoogleSignInButton from "@/components/GoogleSignInButton"
import { buildAuthHeaders, useAuth } from "@/lib/auth"
import { Crown, HeartHandshake, LayoutGrid, Send } from "lucide-react"
import AIMessage from './components/AImessage'
import ChartViewer from "./components/ChartViewer"
import CompatibilityViewer from "./components/CompatibilityViewer"
import { getBackendUrl } from "@/lib/utils"
import { useParams } from "next/navigation"

interface Message {
  id: string
  content: string
  sender: "user" | "ai"
  isNew?: boolean // true for newly created messages (should animate), false/undefined for restored messages
}

interface SessionResponse {
  session_id: string
  full_name?: string | null
  has_birth_details: boolean
  messages: Message[]
}

const CHAT_TIMEOUT_MS = 90000
const FREE_LIMIT_MESSAGE = "🔒 You’ve reached today’s free question limit. Upgrade to Premium for unlimited questions."

function shouldShowBillingCta(content: string): boolean {
  const normalized = String(content || "").toLowerCase()
  return (
    normalized.includes("free question limit") ||
    normalized.includes("upgrade to premium for unlimited questions")
  )
}

function getFriendlyChatErrorMessage(error: unknown): string {
  const message = error instanceof Error ? error.message : ""
  if (message.toLowerCase().includes("timeout")) {
    return "🔮 This reading is taking longer than usual. Please try again in a moment, and I’ll continue from where we left off."
  }
  if (message.toLowerCase().includes("5 free questions")) {
    return FREE_LIMIT_MESSAGE
  }
  if (message.toLowerCase().includes("premium")) {
    return `🔒 ${message}`
  }
  return "🔮 I ran into a temporary server issue while preparing your reading. Please try the question again in a moment."
}

function isExpectedHandledChatError(error: unknown): boolean {
  const message = error instanceof Error ? error.message.toLowerCase() : ""
  return (
    message.includes("timeout") ||
    message.includes("5 free questions") ||
    message.includes("premium") ||
    message.includes("daily limit") ||
    message.includes("upgrade to premium") ||
    message.includes("llm conversation failed") ||
    message.includes("server_error")
  )
}

export default function ChatComponent() {
  const params = useParams();
  const sid = (params && (params as any).sid) ?? ""; 
  const backendUrl = getBackendUrl();
  const { user, token, loading: authLoading, refreshUser } = useAuth()
  const [messages, setMessages] = useState<Message[]>([])
  const [inputMessage, setInputMessage] = useState("")
  const scrollAreaRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const [isWaitingForAI, setIsWaitingForAI] = useState(false)
  const [isChartViewerOpen, setIsChartViewerOpen] = useState(false)
  const [isCompatibilityOpen, setIsCompatibilityOpen] = useState(false)
  const [isBillingOpen, setIsBillingOpen] = useState(false)
  const [sessionError, setSessionError] = useState("")
  const [sessionLoading, setSessionLoading] = useState(true)


  const newMessage = inputMessage.trim();

  const loadSession = useCallback(async () => {
    if (!sid || !token) {
      setMessages([])
      setSessionLoading(false)
      return
    }

    setSessionLoading(true)
    try {
      const res = await fetch(`${backendUrl}/sessions/${sid}`, {
        headers: buildAuthHeaders(token),
      })
      if (!res.ok) {
        let message = "Failed to load this reading."
        try {
          const data = await res.json()
          message = data?.detail?.message || data?.detail || data?.error || message
        } catch {
          // ignore parse errors
        }
        throw new Error(message)
      }
      const data: SessionResponse = await res.json()
      const loadedWithFlag = (data.messages || []).map((msg) => ({
        ...msg,
        isNew: false,
      }))
      setMessages(loadedWithFlag)
      const hasAIMessage = loadedWithFlag.some((msg) => msg.sender === "ai")
      const hasOnlyUserMessages = loadedWithFlag.length >= 1 && !hasAIMessage
      setIsWaitingForAI(hasOnlyUserMessages)
      setSessionError("")
    } catch (err) {
      setSessionError(err instanceof Error ? err.message : "Failed to load this reading.")
    } finally {
      setSessionLoading(false)
    }
  }, [backendUrl, sid, token])

  useEffect(() => {
    if (authLoading) return
    void loadSession()
  }, [authLoading, loadSession])

  useEffect(() => {
    if (!token || !sid || !isWaitingForAI) return
    const interval = window.setInterval(() => {
      void loadSession()
    }, 1200)
    return () => window.clearInterval(interval)
  }, [isWaitingForAI, loadSession, sid, token])

  if (!sid) {
    return <div className="p-4 text-sm text-gray-400">No session id found.</div>;
  }

  if (!authLoading && (!user || !token)) {
    return (
      <div className="flex flex-1 items-center justify-center px-4">
        <Card className="w-full max-w-md rounded-3xl border border-white/10 bg-slate-950/80 p-6 text-white">
          <div className="mb-2 text-xl font-semibold">Sign in to open this reading</div>
          <p className="mb-4 text-sm leading-6 text-slate-300">
            Kundli sessions are now attached to your account, so this page needs an authenticated sign-in.
          </p>
          <GoogleSignInButton />
        </Card>
      </div>
    )
  }


  const scrollToBottom = () => {
    const container = scrollAreaRef.current?.querySelector(
      "[data-radix-scroll-area-viewport]"
    )
    if (container) container.scrollTop = container.scrollHeight
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSendMessage = async () => {
    if (newMessage && token) {
      const userMsg: Message = {
        id: Date.now().toString(),
        content: newMessage,
        sender: "user",
        isNew: true, // Mark as new (though user messages don't animate anyway)
      }

      setMessages(prev => [...prev, userMsg])

      setInputMessage("")
      setIsWaitingForAI(true)

      try {
        const controller = new AbortController()
        const timeout = setTimeout(() => controller.abort(), CHAT_TIMEOUT_MS)

        const res = await Promise.race([
          fetch(`${backendUrl}/chat`, {
            method: "POST",
            headers: buildAuthHeaders(token, { "Content-Type": "application/json", "X-Session-Id": sid }),
            body: JSON.stringify({ query: newMessage }),
            signal: controller.signal,
          }),
          new Promise<null>((_, reject) =>
            setTimeout(() => reject(new Error("timeout")), CHAT_TIMEOUT_MS)
          ),
        ])

        clearTimeout(timeout)

        if (!res) {
          throw new Error("timeout")
        }

        if (!(res as Response).ok) {
          let backendMessage = ""
          try {
            const result = await (res as Response).json()
            backendMessage = result?.detail?.message || result?.detail || result?.error || ""
          } catch {
            backendMessage = ""
          }
          throw new Error(backendMessage || "server_error")
        }

        const result = await (res as Response).json()

        setMessages(prev => [
          ...prev,
          {
            id: (Date.now() + 1).toString(),
            sender: "ai",
            content: result.response,
            isNew: true, // Mark as new to enable typing animation
          },
        ])
        await refreshUser()
      } catch (error) {
        setMessages(prev => [
          ...prev,
          {
            id: (Date.now() + 1).toString(),
            sender: "ai",
            content: getFriendlyChatErrorMessage(error),
            isNew: true, // Mark as new to enable typing animation
          },
        ])
        if (!isExpectedHandledChatError(error)) {
          console.error("Error sending message:", error)
        }
      } finally {
        setIsWaitingForAI(false)
      }
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }


  return (
    <div className="flex flex-col h-screen text-white overflow-hidden">
      <ChartViewer
        backendUrl={backendUrl}
        open={isChartViewerOpen}
        onClose={() => setIsChartViewerOpen(false)}
        sessionId={sid}
      />
      <CompatibilityViewer
        backendUrl={backendUrl}
        open={isCompatibilityOpen}
        onClose={() => setIsCompatibilityOpen(false)}
        sessionId={sid}
      />
      <BillingPlansModal
        backendUrl={backendUrl}
        open={isBillingOpen}
        onClose={() => setIsBillingOpen(false)}
      />

      {/* Chat Messages */}
      <div className="flex-1 overflow-hidden mt-2 mb-1 pb-1">
        <ScrollArea ref={scrollAreaRef} className="h-full px-4 py-0">
          <div className="max-w-4xl mx-auto space-y-2">
            {sessionLoading && messages.length === 0 ? (
              <Card className="border border-white/10 bg-slate-950/70 px-4 py-4 text-sm text-slate-300">
                Loading your saved reading…
              </Card>
            ) : null}
            {sessionError ? (
              <Card className="border border-rose-400/20 bg-rose-500/10 px-4 py-4 text-sm text-rose-100">
                {sessionError}
              </Card>
            ) : null}
            {user?.plan_access.ads_enabled ? (
              <Card className="border border-blue-400/15 bg-[linear-gradient(135deg,rgba(30,41,59,0.92),rgba(15,23,42,0.98))] px-4 py-3 text-white">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-cyan-200">Sponsored</div>
                    <div className="mt-1 text-sm font-medium">Unlock Premium for unlimited questions and D9/D10 insights.</div>
                  </div>
                  <div className="hidden rounded-full bg-amber-500/15 px-2 py-1 text-[10px] font-semibold uppercase tracking-[0.16em] text-amber-200 sm:inline-flex">
                    <Crown className="mr-1 h-3 w-3" />
                    Premium
                  </div>
                </div>
              </Card>
            ) : null}
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex ${msg.sender === "user" ? "justify-end" : "justify-start"
                  }`}
              >
                <div
                  className={`max-w-[80%] sm:max-w-[70%] ${msg.sender === "user" ? "order-2" : "order-1"
                    }`}
                >
                  <Card
                    className={`px-4 pt-2 pb-4 shadow-md ${msg.sender === "user"
                      ? "bg-gray-800 text-white"
                      : "bg-gray-900 border border-gray-700 text-white"
                      }`}
                  >
                    {msg.sender === "ai" ? (
                      <AIMessage
                        id={msg.id}
                        content={msg.content}
                        isNew={msg.isNew ?? false}
                      />
                    ) : (
                      <p className="text-sm leading-relaxed whitespace-pre-wrap">
                        {msg.content}
                      </p>
                    )}
                    {msg.sender === "ai" && shouldShowBillingCta(msg.content) && !user?.plan_access.is_premium ? (
                      <div className="mt-3 flex justify-start">
                        <Button
                          type="button"
                          onClick={() => setIsBillingOpen(true)}
                          className="h-9 rounded-full bg-amber-500 px-4 text-slate-950 hover:bg-amber-400"
                        >
                          <Crown className="mr-2 h-4 w-4" />
                          Go To Billing
                        </Button>
                      </div>
                    ) : null}
                  </Card>

                  {/* Avatar */}
                  <div
                    className={`flex mt-2 ${msg.sender === "user"
                      ? "justify-end"
                      : "justify-start"
                      }`}
                  >
                    <div
                      className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-medium ${msg.sender === "user"
                        ? "bg-gradient-to-r from-black to-blue-400 text-white"
                        : "bg-gradient-to-r from-gray-500 to-gray-1000 text-white"
                        }`}
                    >
                      {msg.sender === "user" ? "You" : "AI"}
                    </div>
                  </div>
                </div>
              </div>
            ))}
            {isWaitingForAI && (
              <div className="flex justify-start">
                <div className="max-w-[80%] sm:max-w-[70%]">
                  <Card className="px-4 pt-2 pb-4 shadow-md bg-gray-900 border border-gray-700 text-white">
                    <div className="flex items-center gap-1 text-sm leading-relaxed italic text-gray-400">
                      <span>AI is typing</span>
                      <span className="flex gap-0.5">
                        <span className="animate-bounce [animation-delay:0ms]">.</span>
                        <span className="animate-bounce [animation-delay:150ms]">.</span>
                        <span className="animate-bounce [animation-delay:300ms]">.</span>
                      </span>
                    </div>
                  </Card>
                  <div className="flex mt-2 justify-start">
                    <div className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-medium bg-gradient-to-r from-gray-500 to-gray-1000 text-white">
                      AI
                    </div>
                  </div>
                </div>
              </div>
            )}

          </div>
        </ScrollArea>
      </div>

      {/* Message Input - Fixed at bottom */}
      <div className="flex-shrink-0 border-t border-gray-800/80 bg-transparent">
        <div className="max-w-4xl mx-auto">
          <Card className="m-2 rounded-2xl border border-slate-700/80 bg-slate-950/55 p-2.5 shadow-lg shadow-black/30 sm:p-4">
            <form
              className="flex items-end gap-2 sm:gap-3"
              onSubmit={(e) => {
                e.preventDefault()
                handleSendMessage()
              }}
            >
              <div className="flex-1">
                <Textarea
                  ref={textareaRef}
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  onKeyDown={handleKeyPress}
                  placeholder="Ask about your Kundali, planets, career, relationships…"
                  className="min-h-[44px] max-h-28 w-full resize-none overflow-x-hidden rounded-xl border-slate-700 bg-black/80 px-3 py-2.5 text-sm leading-5 text-white placeholder:text-gray-500 [overflow-wrap:anywhere] [word-break:break-word] focus:border-blue-400 focus:ring-blue-400 sm:max-h-40 sm:min-h-[48px] sm:text-base"
                  disabled={isWaitingForAI}
                />
              </div>
              <Button
                type="submit"
                disabled={!inputMessage.trim() || isWaitingForAI}
                className="h-11 w-11 shrink-0 rounded-xl bg-gradient-to-r from-slate-900 to-blue-800 px-0 text-white shadow-lg shadow-blue-950/30 hover:from-slate-800 hover:to-blue-700 sm:h-12 sm:w-auto sm:px-5"
              >
                <Send className="h-4 w-4" />
                <span className="ml-2 hidden sm:inline">Send</span>
              </Button>
            </form>
            <div className="mt-2 sm:flex sm:items-center sm:justify-between sm:text-xs sm:text-gray-400">
              <span className="hidden sm:inline">Enter to send • Shift+Enter for new line</span>
              <div className="grid grid-cols-2 gap-2 sm:flex sm:items-center sm:gap-3">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setIsChartViewerOpen(true)}
                  className="h-9 rounded-xl border-blue-500/30 bg-slate-900/80 px-3 text-xs text-slate-200 hover:bg-slate-800 hover:text-white sm:h-8"
                >
                  <LayoutGrid className="h-3.5 w-3.5" />
                  <span className="ml-1.5">View Charts</span>
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setIsCompatibilityOpen(true)}
                  className="h-9 rounded-xl border-rose-500/30 bg-slate-900/80 px-3 text-xs text-slate-200 hover:bg-slate-800 hover:text-white sm:h-8"
                >
                  <HeartHandshake className="h-3.5 w-3.5" />
                  <span className="ml-1.5">Kundli Milan</span>
                </Button>
                <div className="hidden items-center space-x-1 sm:flex">
                  <div className="h-2 w-2 rounded-full bg-green-400 animate-pulse"></div>
                  <span>AI Online</span>
                </div>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  )
}
