import type { Metadata } from "next"

import KundaliPage from "../components/KundaliPage"
import { buildPageMetadata } from "@/lib/site"

export const metadata: Metadata = buildPageMetadata({
  title: "Free Kundli & AI Vedic Astrology Reading",
  description:
    "Generate a free kundli online, calculate numerology, ask chart-aware AI Vedic astrology questions, and explore Navamsa, Vimshottari dasha, kundli matching, panchang, and relationship timing.",
  path: "/",
  keywords: [
    "free kundli",
    "numerology",
    "ai vedic astrology",
    "free kundli online",
    "vedic astrology reading",
    "navamsa chart",
    "vimshottari dasha",
  ],
})

export default function HomePage() {
  return <KundaliPage />
}
