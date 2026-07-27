import type { Metadata } from "next"

import JsonLd from "@/components/JsonLd"
import { Card } from "@/components/ui/card"
import StaticPageLayout from "@/components/StaticPageLayout"
import { buildPageMetadata } from "@/lib/site"
import { buildStaticPageJsonLd } from "@/lib/structured-data"

const title = "Contact Nakshatra AI"
const description =
  "Contact Nakshatra AI for support, account issues, billing problems, feature feedback, and chart-reading bug reports."

export const metadata: Metadata = buildPageMetadata({
  title,
  description,
  path: "/contact",
})

export default function ContactPage() {
  return (
    <>
      <JsonLd
        id="contact-page-jsonld"
        data={buildStaticPageJsonLd({ title, description, path: "/contact" })}
      />
      <StaticPageLayout
        eyebrow="Contact"
        title="Reach the project through the channels already tied to the product."
        intro="If you need help with account access, billing flow, or a chart-reading issue, the fastest path is to email with the session context that caused the problem and enough detail to reproduce it."
      >
      <div className="grid gap-4 lg:grid-cols-[1.2fr_0.8fr]">
        <Card className="rounded-[1.8rem] border border-white/10 bg-slate-950/72 p-6 text-white sm:p-7">
          <h2 className="text-xl font-semibold">Best ways to get in touch</h2>
          <div className="mt-4 grid gap-4">
            <div className="rounded-2xl border border-cyan-400/14 bg-cyan-400/6 p-4">
              <div className="text-sm font-semibold uppercase tracking-[0.16em] text-cyan-100">
                Email
              </div>
              <a
                href="mailto:namantripathi937@gmail.com"
                className="mt-2 inline-block text-base font-medium text-white underline decoration-cyan-300/45 underline-offset-4"
              >
                namantripathi937@gmail.com
              </a>
              <br></br>
              <a
                href="mailto:kantaman2109@gmail.com"
                className="mt-2 inline-block text-base font-medium text-white underline decoration-cyan-300/45 underline-offset-4"
              >
                kantaman2109@gmail.com
              </a>
              <p className="mt-2 text-sm leading-6 text-slate-300">
                Best for bug reports, billing issues, account-access problems, feature requests,
                and any reproducible product issue.
              </p>
            </div>

            <div className="rounded-2xl border border-white/10 bg-white/4 p-4">
              <div className="text-sm font-semibold uppercase tracking-[0.16em] text-slate-200">
                What to include
              </div>
              <p className="mt-2 text-sm leading-6 text-slate-300">
                Include the page, the action you took, the approximate time, and if possible the
                session ID or screenshot. That makes support much faster.
              </p>
            </div>

            <div className="rounded-2xl border border-white/10 bg-white/4 p-4">
              <div className="text-sm font-semibold uppercase tracking-[0.16em] text-slate-200">
                Helpful subject line
              </div>
              <p className="mt-2 text-sm leading-6 text-slate-300">
                Use a short subject like <span className="font-medium text-white">Nakshatra AI:
                billing issue</span> or <span className="font-medium text-white">Nakshatra AI:
                session loading bug</span> so the request can be triaged quickly.
              </p>
            </div>
          </div>
        </Card>

        <Card className="rounded-[1.8rem] border border-white/10 bg-slate-950/72 p-6 text-white sm:p-7">
          <h2 className="text-xl font-semibold">Support scope</h2>
          <ul className="mt-4 space-y-3 text-sm leading-6 text-slate-300">
            <li>Account sign-in and session-access issues</li>
            <li>Billing or payment flow problems</li>
            <li>Feature bugs, loading failures, or broken pages</li>
            <li>General product feedback and improvement suggestions</li>
          </ul>
        </Card>
      </div>

      <Card className="rounded-[1.8rem] border border-white/10 bg-slate-950/72 p-6 text-white sm:p-7">
        <h2 className="text-xl font-semibold">Response expectations</h2>
        <p className="mt-3 text-sm leading-7 text-slate-300">
          This is an actively developed product, so response times may vary. Clear reproduction
          steps, screenshots, and session details usually lead to the quickest resolution.
        </p>
      </Card>
      </StaticPageLayout>
    </>
  )
}
