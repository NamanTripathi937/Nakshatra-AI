"use client"

import React, { useState, useRef, useEffect, useCallback } from "react"

import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Textarea } from "@/components/ui/textarea"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Send } from "lucide-react"
import AIMessage from './components/AImessage'
import { getBackendUrl, loadMessagesForSession, messagesKeyForSession, saveMessagesForSession } from "@/lib/utils"
import { useParams } from "next/navigation"

interface Message {
  id: string
  content: string
  sender: "user" | "ai"
  isNew?: boolean // true for newly created messages (should animate), false/undefined for restored messages
}

const CHAT_TIMEOUT_MS = 90000

function getFriendlyChatErrorMessage(error: unknown): string {
  const message = error instanceof Error ? error.message : ""
  if (message.toLowerCase().includes("timeout")) {
    return "🔮 This reading is taking longer than usual. Please try again in a moment, and I’ll continue from where we left off."
  }
  return "🔮 I ran into a temporary server issue while preparing your reading. Please try the question again in a moment."
}

export default function ChatComponent() {
  const params = useParams();
  const sid = (params && (params as any).sid) ?? ""; 
  const backendUrl = getBackendUrl();
  const [messages, setMessages] = useState<Message[]>([])
  const [inputMessage, setInputMessage] = useState("")
  const scrollAreaRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const [isWaitingForAI, setIsWaitingForAI] = useState(false)
  const isFetchingChat = useRef(false) // guard to prevent kundli-detection effect from clearing flag during chat API calls

   const load = useCallback(() => {
    if (!sid) {
      setMessages([]);
      return;
    }
    const loaded = loadMessagesForSession(sid) || [];
    // Mark all loaded messages as not new (skip animation)
    const loadedWithFlag = loaded.map((msg: Message) => ({
      ...msg,
      isNew: false
    }));
    setMessages(loadedWithFlag);
  }, [sid]);


  const newMessage = inputMessage.trim();
  // const session_id = getOrCreateSessionId();

  // const storagePrefix = `nakshatra:session:${session_id}`

  // Load persisted UI state on mount
  // useEffect(() => {
  //   try {
  //     const rawMsgs = localStorage.getItem(`${storagePrefix}:messages`)
  //   //   const rawFormSubmitted = localStorage.getItem(`${storagePrefix}:formSubmitted`)
  //     const rawInput = localStorage.getItem(`${storagePrefix}:inputMessage`)
  //     if (rawMsgs) {
  //       setMessages(JSON.parse(rawMsgs))
  //     }
  //     if (rawInput) setInputMessage(rawInput)
  //   } catch (e) {
  //     console.warn("Failed to load persisted session state", e)
  //   }
  // }, []) // run once per session id

  // // Persist messages & formSubmitted whenever they change
  // useEffect(() => {
  //   try {
  //     localStorage.setItem(`${storagePrefix}:messages`, JSON.stringify(messages))
  //   //   localStorage.setItem(`${storagePrefix}:formSubmitted`, String(formSubmitted))
  //   } catch (e) {
  //     console.warn("Failed to persist session state", e)
  //   }
  // }, [messages])

  // // persist inputMessage while typing (small throttling would be nicer)
  // useEffect(() => {
  //   try {
  //     localStorage.setItem(`${storagePrefix}:inputMessage`, inputMessage)
  //   } catch { /* ignore */ }
  // }, [inputMessage])

   useEffect(() => {
    load();
    
    // Listen for storage changes from other tabs/windows
    const onStorage = (ev: StorageEvent) => {
      if (!ev.key) return;
      if (ev.key === messagesKeyForSession(sid)) {
        try {
          const newVal = ev.newValue ? JSON.parse(ev.newValue) : [];
          // Mark all loaded messages as not new (skip animation)
          const loadedWithFlag = newVal.map((msg: Message) => ({
            ...msg,
            isNew: false
          }));
          setMessages(loadedWithFlag);
        } catch (e) {
          console.warn("failed to parse storage event data", e);
        }
      }
    };
    window.addEventListener("storage", onStorage);
    
    // Poll for localStorage changes in same tab (since storage event doesn't fire for same tab)
    const checkInterval = setInterval(() => {
      if (!sid) return;
      try {
        const current = loadMessagesForSession(sid) || [];
        setMessages(prev => {
          // Only update if messages have actually changed
          if (JSON.stringify(current) !== JSON.stringify(prev.map(({ isNew, ...msg }) => msg))) {
            const loadedWithFlag = current.map((msg: Message) => ({
              ...msg,
              isNew: false
            }));
            return loadedWithFlag;
          }
          return prev;
        });
      } catch (e) {
        console.warn("failed to poll messages", e);
      }
    }, 500); // Check every 500ms
    
    return () => {
      window.removeEventListener("storage", onStorage);
      clearInterval(checkInterval);
    };
  }, [sid, load]);

  // Save messages to localStorage whenever they change
  useEffect(() => {
    if (!sid || messages.length === 0) return;
    // Save messages without the isNew flag (we'll restore them without it)
    const messagesToSave = messages.map(({ isNew, ...msg }) => msg);
    saveMessagesForSession(sid, messagesToSave);
  }, [messages, sid]);

  // Detect if we're waiting for the initial kundli response
  useEffect(() => {
    // Don't interfere when a /chat API call is already in progress
    if (isFetchingChat.current) return;
    const hasAIMessage = messages.some(msg => msg.sender === "ai");
    const hasOnlyUserMessages = messages.length >= 1 && !hasAIMessage;
    
    if (hasOnlyUserMessages) {
      setIsWaitingForAI(true);
    } else if (hasAIMessage) {
      setIsWaitingForAI(false);
    }
  }, [messages]);

  if (!sid) {
    return <div className="p-4 text-sm text-gray-400">No session id found.</div>;
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
    if (newMessage) {
      const userMsg: Message = {
        id: Date.now().toString(),
        content: newMessage,
        sender: "user",
        isNew: true, // Mark as new (though user messages don't animate anyway)
      }

      setMessages(prev => [...prev, userMsg])

      setInputMessage("")
      isFetchingChat.current = true
      setIsWaitingForAI(true)

      try {
        const controller = new AbortController()
        const timeout = setTimeout(() => controller.abort(), CHAT_TIMEOUT_MS)

        const res = await Promise.race([
          fetch(`${backendUrl}/chat`, {
            method: "POST",
            headers: { "Content-Type": "application/json", "X-Session-Id": sid },
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
            backendMessage = result?.error || result?.detail || ""
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
        console.error("Error sending message:", error)
      } finally {
        isFetchingChat.current = false
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

      {/* Chat Messages */}
      <div className="flex-1 overflow-hidden mt-2 mb-1 pb-1">
        <ScrollArea ref={scrollAreaRef} className="h-full px-4 py-0">
          <div className="max-w-4xl mx-auto space-y-2">
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
      <div className="flex-shrink-0 bg-transparent border-t border-gray-800">
        <div className="max-w-4xl mx-auto">
          <Card className="p-4 m-2 shadow-lg border-gray-600 bg-transparent">
            <form
              className="flex space-x-3 items-center"
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
                  className="max-h-40 min-h-[40px] w-full resize-none bg-black border-gray-600 text-white placeholder:text-gray-400 focus:border-purple-400 focus:ring-purple-400 overflow-y-auto"
                  disabled={isWaitingForAI}
                />
              </div>
              <Button
                type="submit"
                disabled={!inputMessage.trim() || isWaitingForAI}
                className="bg-gradient-to-r from-gray-900 to-blue-800 hover:from-purple-700 hover:to-indigo-700 text-white shadow-lg px-6 py-3"
              >
                <Send className="h-4 w-4" />
                <span className="ml-2 hidden sm:inline">Send</span>
              </Button>
            </form>
            <div className="flex items-center justify-between text-xs text-gray-400 mt-2">
              <span>Enter to send • Shift+Enter for new line</span>
              <div className="flex items-center space-x-1">
                <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                <span>AI Online</span>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  )
}
