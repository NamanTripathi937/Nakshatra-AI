import type { Metadata } from "next"

import JsonLd from "@/components/JsonLd"
import KundaliPage from "../components/KundaliPage"
import { SITE_DESCRIPTION, buildPageMetadata } from "@/lib/site"
import { buildStaticPageJsonLd } from "@/lib/structured-data"

const title = "Free Kundli Online & AI Vedic Astrology | Nakshatra AI"
const description = SITE_DESCRIPTION

export const metadata: Metadata = buildPageMetadata({
  title,
  description,
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
  return (
    <>
      <JsonLd
        id="home-page-jsonld"
        data={buildStaticPageJsonLd({
          title,
          description,
          path: "/",
          breadcrumbs: [{ name: "Home", path: "/" }],
        })}
      />
      <KundaliPage />
    </>
  )
}
