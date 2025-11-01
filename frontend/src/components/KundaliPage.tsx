"use client"

import React, { useState, useRef, useEffect } from "react"
import KundaliForm from "./KundaliForm"
import { getOrCreateSessionId, loadMessagesForSession, saveMessagesForSession, formatBirthDetails } from "@/lib/utils"
import { useRouter } from "next/navigation"


interface Message {
  id: string
  content: string
  sender: "user" | "ai"
}

export default function KundaliPage() {
  const [formSubmitted, setFormSubmitted] = useState(false)
  const [messages, setMessages] = useState<Message[]>([])
  const [inputMessage, setInputMessage] = useState("")
  const [loading, setLoading] = useState(false)

  const router = useRouter();
  // const newMessage = inputMessage.trim();
  

  // const storagePrefix = `nakshatra:session:${session_id}`
  

  useEffect(() => {
    fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/ping`).catch(() => { })
    console.log('Sent ping to backend')
  }, [])

  const handleFormSubmit = async (data: any) => {
    if (loading) return;   //double click prevention
    setLoading(true);
    const sessionId = getOrCreateSessionId();
    const formatted = formatBirthDetails(data);
    const userMsg: Message = {
      id: Date.now().toString(),
      sender: "user",
      content: `We have received your following Birth Details:\n\n${formatted}\n\nFor privacy purposes, we are not saving it anywhere ✅`,
    };
    setFormSubmitted(true)

    // Read any persisted messages to avoid accidental overwrite
    // const persistMessages = loadMessagesForSession(sessionId) || [];
    const afterPersistMessages = [userMsg];
    console.log("Existing persisted messages for session", afterPersistMessages);

    // Optimistically persist user message immediately (canonical key) so chat page shows it right away
    
    // setMessages(prev => [
    //   ...prev,
    //   {
    //     id: Date.now().toString(),
    //     sender: "user",
    //     content: `We have received your following Birth Details : ${data} . For privacy purposes, we are not saving it anywhere ✅`,
    //   },
    // ])

    // // setLoading(true);
    // console.log("Loaded persisted messages for session", persisted);
    // const afterPersistMessages = [...persisted, userMsg];
    // console.log("Persisting messages for session", afterPersistMessages);

    try {
      saveMessagesForSession(sessionId, afterPersistMessages);
      setMessages(afterPersistMessages);
      // Navigate to chat window right away so user sees the first message immediately
      router.push(`/chatWindow/${sessionId}`);
      // const res = await fetch("/api/kundli", {
      //   method: "POST",
      //   headers: { "Content-Type": "application/json", "X-Session-Id": session_id },
      //   body: JSON.stringify(data),
      // })

      // let raw = await res.text()

      // try {
      //   const parsed = JSON.parse(raw)
      //   if (Array.isArray(parsed)) raw = parsed.join("\n")
      // } catch (e) {
      //   console.log(e)
      // }

      // setMessages(prev => [
      //   ...prev,
      //   {
      //     id: (Date.now() + 1).toString(),
      //     sender: "ai",
      //     content: raw,
      //   },
      // ])
      // router.push(`/chatWindow/${session_id}`);
    } catch (e) {
      // setMessages(prev => [
      //   ...prev,
      //   {
      //     id: (Date.now() + 1).toString(),
      //     sender: "ai",
      //     content: "⚠️ Error fetching Kundli details. Please try again later.",
      //   },
      // ])
      console.warn("failed to persist user message before navigation", e);
      // still navigate
      router.push(`/chatWindow/${sessionId}`);

    } 
    // finally {
    //   localStorage.setItem(storagePrefix, JSON.stringify({
    //     createdAt: Date.now(),
    //     messages: messages
    //   }));
    //   setLoading(false)
    // }
    // setLoading(true);
    try {
      const res = await fetch("/api/kundli", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Session-Id": sessionId,
        },
        body: JSON.stringify(data),
      });

      const aiText = await res.text();

      const aiMsg: Message = {
        id: (Date.now() + 1).toString(),
        sender: "ai",
        content: aiText || "No response from AI.",
      };

      // Append AI message to the persisted array and save again
      const finalMessages = [...afterPersistMessages, aiMsg];
      saveMessagesForSession(sessionId, finalMessages);
      // update local state (in this component it won't be visible because we navigated, but other tabs/pages will read from storage)
      setMessages(finalMessages);
    } catch (err) {
      console.error("kundli API error", err);
      const errMsg: Message = {
        id: (Date.now() + 2).toString(),
        sender: "ai",
        content: "⚠️ Error fetching Kundli details. Please try again later.",
        
      };
      const finalMessages = [...afterPersistMessages, errMsg];
      saveMessagesForSession(sessionId, finalMessages);
      setMessages(finalMessages);
    } finally {
      setLoading(false);
    }

  };
  return (
        <div className="flex flex-1 items-center justify-center px-4 mt-40">
          <KundaliForm onSubmit={handleFormSubmit} loading={loading} />
          <div className="mt-4 text-center">
      </div>
        </div>
  )
}
