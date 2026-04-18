import SeoLandingPage from "@/components/SeoLandingPage"
import { getLandingPageOrThrow } from "@/lib/seo-content"
import { buildPageMetadata } from "@/lib/site"

const page = getLandingPageOrThrow("mangal-dosh")

export const metadata = buildPageMetadata({
  title: page.title,
  description: page.description,
  path: page.path,
  keywords: ["mangal dosh", "manglik", "mars dosha", "vedic marriage astrology"],
})

export default function MangalDoshPage() {
  return <SeoLandingPage page={page} />
}
