import Link from "next/link"

import StaticPageLayout from "@/components/StaticPageLayout"
import { Card } from "@/components/ui/card"
import type { LandingPageContent } from "@/lib/seo-content"

export default function SeoLandingPage({ page }: { page: LandingPageContent }) {
  return (
    <StaticPageLayout eyebrow={page.eyebrow} title={page.heroTitle} intro={page.intro}>
      <div className="grid gap-4 lg:grid-cols-[1.15fr_0.85fr]">
        <Card className="rounded-[1.8rem] border border-white/10 bg-slate-950/72 p-6 text-white sm:p-7">
          <h2 className="text-xl font-semibold">{page.toolTitle}</h2>
          <p className="mt-3 text-sm leading-7 text-slate-300">{page.toolBody}</p>
          <Link
            href={page.toolHref}
            className="mt-5 inline-flex rounded-full border border-cyan-300/16 bg-cyan-400/10 px-4 py-2 text-sm text-cyan-100 transition-colors hover:bg-cyan-400/18"
          >
            {page.toolLabel}
          </Link>
        </Card>

        <Card className="rounded-[1.8rem] border border-cyan-400/14 bg-slate-950/72 p-6 text-white sm:p-7">
          <h2 className="text-xl font-semibold">Why this page matters</h2>
          <ul className="mt-4 space-y-3 text-sm leading-7 text-slate-300">
            {page.highlights.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </Card>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        {page.examples.map((example) => (
          <Card
            key={example.title}
            className="rounded-[1.6rem] border border-white/10 bg-white/4 p-5 text-white"
          >
            <h2 className="text-lg font-semibold">{example.title}</h2>
            <p className="mt-3 text-sm leading-6 text-slate-300">{example.body}</p>
          </Card>
        ))}
      </div>

      <Card className="rounded-[1.8rem] border border-white/10 bg-slate-950/72 p-6 text-white sm:p-7">
        <h2 className="text-xl font-semibold">Frequently asked questions</h2>
        <div className="mt-5 grid gap-4 lg:grid-cols-2">
          {page.faqs.map((item) => (
            <div
              key={item.question}
              className="rounded-[1.4rem] border border-white/10 bg-white/4 p-4"
            >
              <h3 className="text-base font-semibold">{item.question}</h3>
              <p className="mt-3 text-sm leading-6 text-slate-300">{item.answer}</p>
            </div>
          ))}
        </div>
      </Card>

      <Card className="rounded-[1.8rem] border border-cyan-400/14 bg-slate-950/72 p-6 text-white sm:p-7">
        <h2 className="text-xl font-semibold">Keep exploring</h2>
        <div className="mt-5 grid gap-4 lg:grid-cols-3">
          {page.related.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="rounded-[1.4rem] border border-white/10 bg-white/4 p-4 transition-colors hover:border-cyan-300/25 hover:bg-white/8"
            >
              <div className="text-base font-semibold text-white">{item.label}</div>
              <p className="mt-2 text-sm leading-6 text-slate-300">{item.description}</p>
            </Link>
          ))}
        </div>
      </Card>
    </StaticPageLayout>
  )
}
