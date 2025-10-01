"use client"

import React, { useState, useRef, useEffect } from "react"

import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Textarea } from "@/components/ui/textarea"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Send } from "lucide-react"
import KundliForm from "./KundliForm"
import '@geoapify/geocoder-autocomplete/styles/minimal.css'
import AIMessage from './AImessage'
import {getOrCreateSessionId} from "@/lib/utils"


interface Message {
  id: string
  content: string
  sender: "user" | "ai"
}

export default function ChatComponent() {
  const [formSubmitted, setFormSubmitted] = useState(false)
  const [messages, setMessages] = useState<Message[]>([])
  const [inputMessage, setInputMessage] = useState("")
  const scrollAreaRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/ping`).catch(() => { })
    console.log('Sent ping to backend')
  }, [])

  const handleFormSubmit = async (data: any) => {
    setFormSubmitted(true)

    setMessages(prev => [
      ...prev,
      {
        id: Date.now().toString(),
        sender: "user",
        content: "We have received your Birth Details. For privacy purposes, we are not saving it anywhere ✅",
      },
    ])

    setLoading(true);

    try {
      const res = await fetch("/api/kundli", {
        method: "POST",
        headers: { "Content-Type": "application/json","X-Session-Id":session_id  },
        body: JSON.stringify(data),
      })

      let raw = await res.text()

      try {
        const parsed = JSON.parse(raw)
        if (Array.isArray(parsed)) raw = parsed.join("\n")
      } catch (e) {
        console.log(e)
      }

      setMessages(prev => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          sender: "ai",
          content: raw,
        },
      ])
    } catch (e) {
      setMessages(prev => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          sender: "ai",
          content: "⚠️ Error fetching Kundli details. Please try again later.",
        },
      ])
    } finally {
      setLoading(false)
    }
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

  const newMessage = inputMessage.trim();

  const session_id = getOrCreateSessionId();

  const handleSendMessage = async () => {
    if (newMessage) {
      const userMsg: Message = {
        id: Date.now().toString(),
        content: newMessage,
        sender: "user",
      }

      setMessages(prev => [...prev, userMsg])

      setInputMessage("")
      setLoading(true)

      try {
        const controller = new AbortController()
        const timeout = setTimeout(() => controller.abort(), 30000)

        const res = await Promise.race([
          fetch("/api/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json","X-Session-Id":session_id },
            body: JSON.stringify({ query: newMessage }),
            signal: controller.signal,
          }),
          new Promise<null>((_, reject) =>
            setTimeout(() => reject(new Error("timeout")), 30000)
          ),
        ])

        clearTimeout(timeout)

        if (!res || !(res as Response).ok) {
          throw new Error("Server error or timeout.")
        }

        const result = await (res as Response).json()

        setMessages(prev => [
          ...prev,
          {
            id: (Date.now() + 1).toString(),
            sender: "ai",
            content: result.response,
          },
        ])
      } catch (error) {
        setMessages(prev => [
          ...prev,
          {
            id: (Date.now() + 1).toString(),
            sender: "ai",
            content:
              "🚀 All out of free stars! You have asked all the free questions we can handle. But do not worry — just refresh + re-enter your details to keep the conversation going 🔮 ",
          },
        ])
        console.error("Error sending message:", error)
      } finally {
        setLoading(false)
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
    <div className="flex flex-col h-screen bg-black text-white overflow-hidden">
      {/* Header */}
      <header className="bg-black/90 backdrop-blur-md border-b border-gray-700 shadow-sm mb-4">
        <div className="flex items-center justify-center py-4 px-6">
          <h1 className="text-2xl font-bold bg-gradient-to-r from-white to-blue-300 bg-clip-text text-transparent">
            ✦ N A K S H A T R A ✦
          </h1>
        </div>
      </header>

      {/* Kundli Form */}
      {!formSubmitted && <KundliForm onSubmit={handleFormSubmit} />}

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
                      <AIMessage id={msg.id} content={msg.content} />
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
            {loading && (
              <div className="flex justify-start">
                <div className="max-w-[80%] sm:max-w-[70%]">
                  <Card className="px-4 pt-2 pb-4 shadow-md bg-gray-900 border border-gray-700 text-white">
                    <p className="text-sm leading-relaxed whitespace-pre-wrap italic text-gray-400">
                      AI is typing<span className="animate-pulse">...</span>
                    </p>
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

      {/* Message Input */}
      {formSubmitted && <div className="bg-black/95 border-t border-gray-700">
        <div className="max-w-4xl mx-auto">
          <Card className="p-4 m-2 shadow-lg border-gray-600 bg-gray-900">
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
                />
              </div>
              <Button
                type="submit"
                disabled={!inputMessage.trim()}
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
      </div>}
    </div>
  )
}
