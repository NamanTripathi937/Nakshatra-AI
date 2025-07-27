"use client"

import type React from "react"

import { useState, useRef, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Textarea } from "@/components/ui/textarea"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Send, Sparkles, Moon, Star } from "lucide-react"

interface Message {
  id: string
  content: string
  sender: "user" | "ai"
}

export default function Component() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "1",
      content:
        "🙏 Namaste! I'm your Kundali AI assistant. I can help you understand your birth chart, planetary positions, and astrological insights. How can I guide you today?",
      sender: "ai",
    },
  ])

  const [inputMessage, setInputMessage] = useState("")
  const scrollAreaRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const scrollToBottom = () => {
    if (scrollAreaRef.current) {
      const scrollContainer = scrollAreaRef.current.querySelector("[data-radix-scroll-area-viewport]")
      if (scrollContainer) {
        scrollContainer.scrollTop = scrollContainer.scrollHeight
      }
    }
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSendMessage = () => {
    if (inputMessage.trim()) {
      const newMessage: Message = {
        id: Date.now().toString(),
        content: inputMessage.trim(),
        sender: "user",
      }

      setMessages((prev) => [...prev, newMessage])
      setInputMessage("")

      // Simulate AI response
      setTimeout(() => {
        const aiResponse: Message = {
          id: (Date.now() + 1).toString(),
          content:
            "Thank you for your question. I'm analyzing your query and will provide you with detailed astrological insights based on Vedic astrology principles. 🌟",
          sender: "ai",
        }
        setMessages((prev) => [...prev, aiResponse])
      }, 1000)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  // const formatTime = (date: Date) => {
  //   return date.toLocaleTimeString("en-US", {
  //     hour: "2-digit",
  //     minute: "2-digit",
  //     hour12: true,
  //   })
  // }

  return (
    <div className="flex flex-col h-screen bg-black overflow-hidden">
      {/* Fixed Header */}
      <header className="bg-black/95 backdrop-blur-md border-b border-gray-700 shadow-sm">
        <div className="flex items-center justify-center py-4 px-6">
          <div className="flex items-center space-x-3">
            <div className="relative">
              
              {/* <span className="text-3xl drop-shadow-[0_0_15px_rgba(255,255,255,0.4)]">🌕</span> */}
            </div>
            <h1 className="text-2xl font-bold bg-gradient-to-r from-white to-blue-300 bg-clip-text text-transparent">
              ✦ N A K S H A T R A  AI✦ 
            </h1>
            {/* <Sparkles className="h-8 w-8 text-purple-600" />
              <Star className="h-3 w-3 text-yellow-500 absolute -top-1 -right-1" /> */}
          </div>
        </div>
      </header>

      {/* Chat Messages Area */}
      <div className="flex-1 overflow-hidden">
        <ScrollArea ref={scrollAreaRef} className="h-full px-4 py-6">
          <div className="max-w-4xl mx-auto space-y-6">
            {messages.map((message) => (
              <div key={message.id} className={`flex ${message.sender === "user" ? "justify-end" : "justify-start"}`}>
                <div className={`max-w-[80%] sm:max-w-[70%] ${message.sender === "user" ? "order-2" : "order-1"}`}>
                  <Card
                    className={`p-4 shadow-md ${
                      message.sender === "user"
                        ? "bg-gray-800 text-white border-0"
                        : "bg-gray-900/95 backdrop-blur-sm border-gray-700 text-gray-100"
                    }`}
                  >
                    <p className="text-sm leading-relaxed whitespace-pre-wrap">{message.content}</p>
                    <div className={`text-xs mt-2 ${message.sender === "user" ? "text-purple-200" : "text-gray-400"}`}>
                      {/* {formatTime(message.timestamp)} */}
                    </div>
                  </Card>

                  {/* Avatar */}
                  <div className={`flex mt-2 ${message.sender === "user" ? "justify-end" : "justify-start"}`}>
                    <div
                      className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-medium ${
                        message.sender === "user"
                          ? "bg-gradient-to-r from-black to-blue-400 text-white"
                          : "bg-gradient-to-r from-gray-500 to-gray-1000 text-white"
                      }`}
                    >
                      {message.sender === "user" ? "You" : "AI"}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </ScrollArea>
      </div>

      {/* Message Input Area */}
      <div className="bg-black/95 backdrop-blur-md border-t border-gray-700 p-4">
        <div className="max-w-4xl mx-auto">
          <Card className="p-4 shadow-lg border-gray-600 bg-gray-900/95">
            <div className="flex space-x-3">
              <div className="flex-1">
                <Textarea
                  ref={textareaRef}
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Ask about your Kundali, planetary positions, or astrological guidance..."
                  className="min-h-[60px] max-h-32 resize-none bg-black border-gray-600 text-gray-100 placeholder:text-gray-400 focus:border-purple-400 focus:ring-purple-400"
                  rows={2}
                />
              </div>
              <Button
                onClick={handleSendMessage}
                disabled={!inputMessage.trim()}
                className="self-end bg-gradient-to-r from-gray-900 to-blue-800 hover:from-purple-700 hover:to-indigo-700 text-white shadow-lg hover:shadow-xl transition-all duration-200 px-6 py-3 mb-3"
              >
                <Send className="h-4 w-4" />
                <span className="ml-2 hidden sm:inline">Send</span>
              </Button>
            </div>

            <div className="flex items-center justify-between mt-3 text-xs text-gray-400">
              <span>Press Enter to send, Shift+Enter for new line</span>
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