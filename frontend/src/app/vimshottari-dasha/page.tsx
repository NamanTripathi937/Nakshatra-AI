import SeoLandingPage from "@/components/SeoLandingPage"
import { getLandingPageOrThrow } from "@/lib/seo-content"
import { buildPageMetadata } from "@/lib/site"

const page = getLandingPageOrThrow("vimshottari-dasha")

export const metadata = buildPageMetadata({
  title: page.title,
  description: page.description,
  path: page.path,
  keywords: ["vimshottari dasha", "mahadasha", "antardasha", "vedic timing"],
})

export default function VimshottariDashaPage() {
  return <SeoLandingPage page={page} />
}
