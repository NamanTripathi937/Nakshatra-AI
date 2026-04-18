import SeoLandingPage from "@/components/SeoLandingPage"
import { getLandingPageOrThrow } from "@/lib/seo-content"
import { buildPageMetadata } from "@/lib/site"

const page = getLandingPageOrThrow("navamsa-chart")

export const metadata = buildPageMetadata({
  title: page.title,
  description: page.description,
  path: page.path,
  keywords: ["navamsa chart", "d9 chart", "navamsa meaning", "vedic divisional chart"],
})

export default function NavamsaChartPage() {
  return <SeoLandingPage page={page} />
}
