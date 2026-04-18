import type { Metadata } from "next"

import { Card } from "@/components/ui/card"
import StaticPageLayout from "@/components/StaticPageLayout"
import { buildPageMetadata } from "@/lib/site"

export const metadata: Metadata = buildPageMetadata({
  title: "About Nakshatra AI",
  description:
    "Learn how Nakshatra AI approaches Vedic astrology, chart-aware readings, saved sessions, and practical kundli interpretation.",
  path: "/about",
})

export default function AboutPage() {
  return (
    <StaticPageLayout
      eyebrow="About Nakshatra AI"
      title="A guided Vedic astrology experience built for clarity, continuity, and practical use."
      intro="Nakshatra AI combines structured birth-chart processing with conversational AI so users can generate a kundli, continue asking follow-up questions, and revisit saved readings inside one account-linked flow."
    >
      <Card className="rounded-[1.8rem] border border-white/10 bg-slate-950/72 p-6 text-white sm:p-7">
        <h2 className="text-xl font-semibold">What the product does</h2>
        <p className="mt-3 text-sm leading-7 text-slate-300">
          The site helps users generate a kundli from birth details, ask chart-based questions,
          review divisional charts and compatibility features where available, and return later
          to the same session history without losing context.
        </p>
      </Card>

      <div className="grid gap-4 lg:grid-cols-3">
        <Card className="rounded-[1.6rem] border border-cyan-400/14 bg-slate-950/68 p-5 text-white">
          <h3 className="text-lg font-semibold">Chart-first answers</h3>
          <p className="mt-2 text-sm leading-6 text-slate-300">
            Responses are designed to stay anchored to stored kundli context instead of drifting
            into generic motivational advice.
          </p>
        </Card>
        <Card className="rounded-[1.6rem] border border-cyan-400/14 bg-slate-950/68 p-5 text-white">
          <h3 className="text-lg font-semibold">Account-linked sessions</h3>
          <p className="mt-2 text-sm leading-6 text-slate-300">
            Sign-in keeps readings attached to the user account, making it easier to continue
            earlier conversations and manage plan access.
          </p>
        </Card>
        <Card className="rounded-[1.6rem] border border-cyan-400/14 bg-slate-950/68 p-5 text-white">
          <h3 className="text-lg font-semibold">Free and premium flow</h3>
          <p className="mt-2 text-sm leading-6 text-slate-300">
            Free access offers a lighter experience, while premium unlocks more detailed chart
            tools such as extended readings, remedies, and compatibility features.
          </p>
        </Card>
      </div>

      <Card className="rounded-[1.8rem] border border-white/10 bg-slate-950/72 p-6 text-white sm:p-7">
        <h2 className="text-xl font-semibold">What Nakshatra AI is not</h2>
        <p className="mt-3 text-sm leading-7 text-slate-300">
          It is not a substitute for legal, financial, or medical advice. Astrology content on
          the site is intended for guidance, reflection, and exploratory insight, not as a
          guaranteed prediction engine or professional diagnosis tool.
        </p>
      </Card>
    </StaticPageLayout>
  )
}
