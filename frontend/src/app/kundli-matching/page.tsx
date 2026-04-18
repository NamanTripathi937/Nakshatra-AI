import SeoLandingPage from "@/components/SeoLandingPage"
import { getLandingPageOrThrow } from "@/lib/seo-content"
import { buildPageMetadata } from "@/lib/site"

const page = getLandingPageOrThrow("kundli-matching")

export const metadata = buildPageMetadata({
  title: page.title,
  description: page.description,
  path: page.path,
  keywords: ["kundli matching", "guna milan", "vedic compatibility", "matchmaking kundli"],
})

export default function KundliMatchingPage() {
  return <SeoLandingPage page={page} />
}
