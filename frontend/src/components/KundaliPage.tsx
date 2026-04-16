"use client"

import React, { useState, useEffect } from "react"
import KundaliForm from "./KundaliForm"
import { formatBirthDetails, generateNewSessionId, getBackendUrl, saveMessagesForSession } from "@/lib/utils"
import { useRouter } from "next/navigation"


interface Message {
  id: string
  content: string
  sender: "user" | "ai"
}

export default function KundaliPage() {
  const [messages, setMessages] = useState<Message[]>([])
  const [loading, setLoading] = useState(false)

  const router = useRouter();
  const backendUrl = getBackendUrl();

  useEffect(() => {
    fetch(`${backendUrl}/ping`).catch(() => { })
    console.log('Sent ping to backend')
  }, [backendUrl])

  const handleFormSubmit = async (data: any) => {
    if (loading) return;
    setLoading(true);

    const sessionId = generateNewSessionId();
    if (typeof localStorage !== "undefined") {
      localStorage.setItem("nakshatra_session_id", sessionId);
    }

    const formatted = formatBirthDetails(data);
    const userMsg: Message = {
      id: Date.now().toString(),
      sender: "user",
      content: `We have received your following Birth Details:\n\n${formatted}\n\nFor privacy purposes, we are not saving it anywhere ✅`,
    };

    const afterPersistMessages = [userMsg];
    console.log("Existing persisted messages for session", afterPersistMessages);

    try {
      saveMessagesForSession(sessionId, afterPersistMessages);
      setMessages(afterPersistMessages);
      router.push(`/chatWindow/${sessionId}`);
    } catch (e) {
      console.warn("failed to persist user message before navigation", e);
      router.push(`/chatWindow/${sessionId}`);
    }

    try {
      const res = await fetch(`${backendUrl}/kundli`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Session-Id": sessionId,
        },
        body: JSON.stringify(data),
      });

      const result = await res.json();
      console.log("Kundli API result:", result);
      console.log("result.response:", result.response);

      const aiMsg: Message = {
        id: (Date.now() + 1).toString(),
        sender: "ai",
        content: result.response || "No response from AI.",
      };

      const finalMessages = [...afterPersistMessages, aiMsg];
      saveMessagesForSession(sessionId, finalMessages);
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
