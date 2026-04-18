import SeoLandingPage from "@/components/SeoLandingPage"
import { getLandingPageOrThrow } from "@/lib/seo-content"
import { buildPageMetadata } from "@/lib/site"

const page = getLandingPageOrThrow("daily-horoscope")

export const metadata = buildPageMetadata({
  title: page.title,
  description: page.description,
  path: page.path,
  keywords: ["daily horoscope", "vedic daily horoscope", "daily astrology", "chart-based horoscope"],
})

export default function DailyHoroscopePage() {
  return <SeoLandingPage page={page} />
}
