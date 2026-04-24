import Link from "next/link"

import JsonLd from "@/components/JsonLd"
import StaticPageLayout from "@/components/StaticPageLayout"
import { Card } from "@/components/ui/card"
import { guidePages } from "@/lib/seo-content"
import { buildPageMetadata } from "@/lib/site"
import { buildGuidesIndexJsonLd } from "@/lib/structured-data"

const title = "Vedic Astrology Guides"
const description =
  "Explore Vedic astrology guides on planets, nakshatras, Navamsa, Vimshottari dasha, compatibility, and chart-reading basics."

export const metadata = buildPageMetadata({
  title,
  description,
  path: "/guides",
  keywords: ["vedic astrology guides", "kundli guides", "nakshatra guide", "navamsa guide"],
})

export default function GuidesPage() {
  return (
    <>
      <JsonLd id="guides-index-jsonld" data={buildGuidesIndexJsonLd(guidePages)} />
      <StaticPageLayout
        eyebrow="Vedic Astrology Guides"
        title="Build topical authority with practical Vedic astrology guides."
        intro="These guides are written to help visitors understand real Jyotish concepts before and after they generate a kundli. Use them to explore planets, nakshatras, divisional charts, timing systems, and relationship themes in a more structured way."
      >
        <div className="grid gap-4 lg:grid-cols-2">
          {guidePages.map((guide) => (
            <Link key={guide.slug} href={guide.path}>
              <Card className="h-full rounded-[1.6rem] border border-white/10 bg-slate-950/72 p-5 text-white transition-colors hover:border-cyan-300/25 hover:bg-slate-950/82">
                <div className="text-sm font-semibold uppercase tracking-[0.16em] text-cyan-100">
                  {guide.eyebrow}
                </div>
                <h2 className="mt-3 text-xl font-semibold">{guide.title}</h2>
                <p className="mt-3 text-sm leading-6 text-slate-300">{guide.description}</p>
              </Card>
            </Link>
          ))}
        </div>
      </StaticPageLayout>
    </>
  )
}
