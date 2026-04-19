import type { Metadata } from "next"

import NumerologyPage from "@/components/NumerologyPage"
import { buildPageMetadata } from "@/lib/site"

export const metadata: Metadata = buildPageMetadata({
  title: "Numerology Calculator",
  description:
    "Calculate your numerology profile from your full name and birth date, including Life Path, Destiny, Soul Urge, Personality, Birthday, and Attitude numbers.",
  path: "/numerology",
  keywords: [
    "numerology calculator",
    "life path number",
    "destiny number",
    "soul urge number",
    "personality number",
    "birthday number",
  ],
})

export default function NumerologyRoute() {
  return <NumerologyPage />
}
