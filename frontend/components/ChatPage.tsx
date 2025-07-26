'use client';
import { useState } from "react";
import KundliForm from "./KundliForm";
import type { KundliInput } from "../types";

type ChatBubble = {
  sender: 'user' | 'ai';
  content: string;
};

export default function ChatPage() {
  const [chat, setChat] = useState<ChatBubble[]>([]);
  const [formSubmitted, setFormSubmitted] = useState(false);

  const handleFormSubmit = async (data: KundliInput) => {
    setFormSubmitted(true);
    setChat(prev => [...prev, { sender: "user", content: "User submitted birth details ✅" }]);

    const res = await fetch('/api/kundli', {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });

    const result = await res.text();
    setChat(prev => [...prev, { sender: "ai", content: result }]);
  };

  return (
    <div className="p-4">
      {formSubmitted ? null : <KundliForm onSubmit={handleFormSubmit} />}
      <div className="mt-6 space-y-3">
        {chat.map((c, i) => (
          <div key={i} className={`p-3 rounded-md max-w-xl ${c.sender === 'ai' ? 'bg-gray-200' : 'bg-blue-100'}`}>
            <pre className="whitespace-pre-wrap">{c.content}</pre>
          </div>
        ))}
      </div>
    </div>
  );
}
