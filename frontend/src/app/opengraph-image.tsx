import { ImageResponse } from "next/og"

import { SITE_NAME } from "@/lib/site"

export const size = {
  width: 1200,
  height: 630,
}

export const contentType = "image/png"

export default function OpenGraphImage() {
  return new ImageResponse(
    (
      <div
        style={{
          display: "flex",
          height: "100%",
          width: "100%",
          background:
            "radial-gradient(circle at top left, rgba(34,211,238,0.34), rgba(8,15,30,0.95) 42%, rgba(4,8,18,1) 100%)",
          color: "white",
          padding: "56px",
          flexDirection: "column",
          justifyContent: "space-between",
          fontFamily: "sans-serif",
        }}
      >
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 14,
            fontSize: 30,
            letterSpacing: 3,
            textTransform: "uppercase",
            color: "#d1f5ff",
          }}
        >
          <div
            style={{
              display: "flex",
              width: 26,
              height: 26,
              borderRadius: 999,
              background: "linear-gradient(135deg, #fbbf24, #22d3ee)",
            }}
          />
          {SITE_NAME}
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: 20, maxWidth: 920 }}>
          <div style={{ fontSize: 78, fontWeight: 700, lineHeight: 1.02 }}>
            Free Kundli & AI Vedic Astrology Reading
          </div>
          <div style={{ fontSize: 32, lineHeight: 1.35, color: "#d7e5f5" }}>
            Chart-based Vedic astrology insights built around kundli context, follow-up
            questions, Navamsa, dasha timing, and private saved readings.
          </div>
        </div>

        <div
          style={{
            display: "flex",
            gap: 16,
            flexWrap: "wrap",
            fontSize: 24,
            color: "#d7e5f5",
          }}
        >
          <div
            style={{
              display: "flex",
              padding: "12px 20px",
              borderRadius: 999,
              border: "1px solid rgba(255,255,255,0.14)",
              background: "rgba(255,255,255,0.07)",
            }}
          >
            Free Kundli
          </div>
          <div
            style={{
              display: "flex",
              padding: "12px 20px",
              borderRadius: 999,
              border: "1px solid rgba(255,255,255,0.14)",
              background: "rgba(255,255,255,0.07)",
            }}
          >
            AI Vedic Astrologer
          </div>
          <div
            style={{
              display: "flex",
              padding: "12px 20px",
              borderRadius: 999,
              border: "1px solid rgba(255,255,255,0.14)",
              background: "rgba(255,255,255,0.07)",
            }}
          >
            Navamsa • Dasha • Matching
          </div>
        </div>
      </div>
    ),
    size
  )
}
