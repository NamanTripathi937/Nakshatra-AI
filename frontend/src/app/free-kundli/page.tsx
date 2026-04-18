import SeoLandingPage from "@/components/SeoLandingPage"
import { getLandingPageOrThrow } from "@/lib/seo-content"
import { buildPageMetadata } from "@/lib/site"

const page = getLandingPageOrThrow("free-kundli")

export const metadata = buildPageMetadata({
  title: page.title,
  description: page.description,
  path: page.path,
  keywords: ["free kundli", "free kundli online", "janam kundli", "vedic astrology reading"],
})

export default function FreeKundliPage() {
  return <SeoLandingPage page={page} />
}
