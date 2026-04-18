import SeoLandingPage from "@/components/SeoLandingPage"
import { getLandingPageOrThrow } from "@/lib/seo-content"
import { buildPageMetadata } from "@/lib/site"

const page = getLandingPageOrThrow("panchang")

export const metadata = buildPageMetadata({
  title: page.title,
  description: page.description,
  path: page.path,
  keywords: ["panchang", "vedic panchang", "today panchang", "nakshatra tithi yoga karana"],
})

export default function PanchangPage() {
  return <SeoLandingPage page={page} />
}
