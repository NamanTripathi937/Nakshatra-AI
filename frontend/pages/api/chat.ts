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
  const response = await fetch("http://localhost:8000/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body:  JSON.stringify({ query }),  
  });

    if (!response.ok) {
      const errorText = await response.text();
      console.error("Backend returned error:", errorText);
      return res.status(500).json({ error: "Backend error: " + errorText });
    }

    const reply = await response.json();
    console.log("Chat reply received:", reply);
    res.status(200).json(reply);
  } catch (error) {
    console.error("Error forwarding to backend:", error);
    res.status(500).json({ error: "Failed to fetch from backend" });
  }
}
