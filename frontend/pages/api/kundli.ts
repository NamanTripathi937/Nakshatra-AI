import type { NextApiRequest, NextApiResponse } from 'next';

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== 'POST') {
    res.status(405).json({ error: 'Method not allowed' });
    return;
  }

  const data = req.body;

  try {
    const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
    // console.log(backendUrl)
    const response = await fetch(`${backendUrl}/kundli`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const errorText = await response.text(); // Get raw error
      console.error(" Backend returned error:", errorText);
      return res.status(500).json({ error: " Hi ! Our servers are under maintainence break , Please Try again shortly  " });
    }

    const kundli = await response.json();
    console.log("Kundli data received:", kundli);
    res.status(200).json(kundli);
  } catch (error) {
    console.error("Error fetching kundli:", error);
    res.status(500).json({ error: "Failed to fetch kundli" });
  }
}