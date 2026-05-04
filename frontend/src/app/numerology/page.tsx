import type { Metadata } from "next"

import JsonLd from "@/components/JsonLd"
import NumerologyPage from "@/components/NumerologyPage"
import { buildPageMetadata } from "@/lib/site"
import { buildStaticPageJsonLd } from "@/lib/structured-data"

const title = "Numerology Calculator"
const description =
  "Calculate your numerology profile from your full name and birth date, including Life Path, Destiny, Soul Urge, Personality, Birthday, and Attitude numbers."

export const metadata: Metadata = buildPageMetadata({
  title,
  description,
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
  return (
    <>
      <JsonLd
        id="numerology-page-jsonld"
        data={buildStaticPageJsonLd({
          title,
          description,
          path: "/numerology",
        })}
      />
      <NumerologyPage />
    </>
  )
}
