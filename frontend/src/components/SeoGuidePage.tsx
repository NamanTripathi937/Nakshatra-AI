import Link from "next/link"

import StaticPageLayout from "@/components/StaticPageLayout"
import { Card } from "@/components/ui/card"
import type { GuideContent } from "@/lib/seo-content"

export default function SeoGuidePage({ page }: { page: GuideContent }) {
  return (
    <StaticPageLayout eyebrow={page.eyebrow} title={page.heroTitle} intro={page.intro}>
      <Card className="rounded-[1.8rem] border border-cyan-400/14 bg-slate-950/72 p-6 text-white sm:p-7">
        <h2 className="text-xl font-semibold">Key takeaways</h2>
        <ul className="mt-4 space-y-3 text-sm leading-7 text-slate-300">
          {page.keyTakeaways.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </Card>

      {page.sections.map((section) => (
        <Card
          key={section.title}
          className="rounded-[1.8rem] border border-white/10 bg-slate-950/72 p-6 text-white sm:p-7"
        >
          <h2 className="text-xl font-semibold">{section.title}</h2>
          <div className="mt-4 space-y-4 text-sm leading-7 text-slate-300">
            {section.paragraphs.map((paragraph) => (
              <p key={paragraph}>{paragraph}</p>
            ))}
          </div>
        </Card>
      ))}

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
        <h2 className="text-xl font-semibold">Related reading</h2>
        <div className="mt-5 grid gap-4 lg:grid-cols-2">
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
