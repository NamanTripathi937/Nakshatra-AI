import type { NextApiRequest, NextApiResponse } from 'next';

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== 'POST') {
    res.status(405).json({ error: 'Method not allowed' });
    return;
  }
  const { query } = req.body;  
console.log("Message to send:", query);
if (!query || typeof query !== 'string') {
  return res.status(400).json({ error: 'Query is required and must be a string' });
}

  try {
    const sessionId = req.headers["x-session-id"] as string;
    const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 85000);

    try {
      const response = await fetch(`${backendUrl}/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Session-Id": sessionId
        },
        body: JSON.stringify({ query }),
        signal: controller.signal,
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.error("Backend returned error:", errorText);
        return res.status(response.status).json({ error: errorText || "Backend error" });
      }

      const reply = await response.json();
      console.log("Chat reply received:", reply);
      res.status(200).json(reply);
    } finally {
      clearTimeout(timeout);
    }
  } catch (error) {
    console.error("Error forwarding to backend:", error);
    res.status(502).json({ error: "Failed to fetch from backend" });
  }
}
