import SeoLandingPage from "@/components/SeoLandingPage"
import { getLandingPageOrThrow } from "@/lib/seo-content"
import { buildPageMetadata } from "@/lib/site"

const page = getLandingPageOrThrow("ai-vedic-astrologer")

export const metadata = buildPageMetadata({
  title: page.title,
  description: page.description,
  path: page.path,
  keywords: ["ai vedic astrologer", "vedic astrology ai", "ai astrologer", "kundli ai"],
})

export default function AIVedicAstrologerPage() {
  return <SeoLandingPage page={page} />
}
