import type { Metadata } from "next"

import JsonLd from "@/components/JsonLd"
import { Card } from "@/components/ui/card"
import StaticPageLayout from "@/components/StaticPageLayout"
import { buildPageMetadata } from "@/lib/site"
import { buildStaticPageJsonLd } from "@/lib/structured-data"

const title = "Privacy Policy"
const description =
  "Read how Nakshatra AI handles account data, birth details, saved kundli sessions, analytics, billing records, and third-party services."

export const metadata: Metadata = buildPageMetadata({
  title,
  description,
  path: "/privacy",
})

export default function PrivacyPage() {
  return (
    <>
      <JsonLd
        id="privacy-page-jsonld"
        data={buildStaticPageJsonLd({ title, description, path: "/privacy" })}
      />
      <StaticPageLayout
        eyebrow="Privacy"
        title="How Nakshatra AI handles account data, chart inputs, and supporting services."
        intro="This page gives a plain-language overview of the data used by the site. It is meant to explain the main product flows clearly, especially around sign-in, stored readings, payments, analytics, and ads."
      >
      <Card className="rounded-[1.8rem] border border-white/10 bg-slate-950/72 p-6 text-white sm:p-7">
        <h2 className="text-xl font-semibold">Information the site may collect</h2>
        <ul className="mt-4 space-y-3 text-sm leading-6 text-slate-300">
          <li>Google sign-in details such as name, email address, and profile image</li>
          <li>Birth details entered to generate kundli and astrology readings</li>
          <li>Chat history, saved sessions, and feature usage tied to the signed-in account</li>
          <li>Billing and payment-related records needed to unlock plans or question add-ons</li>
          <li>Basic analytics, ad-related signals, and device/browser information used by third-party services</li>
        </ul>
      </Card>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card className="rounded-[1.8rem] border border-white/10 bg-slate-950/72 p-6 text-white">
          <h2 className="text-xl font-semibold">Why that information is used</h2>
          <p className="mt-3 text-sm leading-7 text-slate-300">
            The data is used to authenticate users, restore accounts, generate chart-based
            responses, save reading history, enforce plan limits, process purchases, improve
            reliability, and support ad or analytics integrations where enabled.
          </p>
        </Card>

        <Card className="rounded-[1.8rem] border border-white/10 bg-slate-950/72 p-6 text-white">
          <h2 className="text-xl font-semibold">Third-party services involved</h2>
          <p className="mt-3 text-sm leading-7 text-slate-300">
            Depending on the feature used, the site may rely on services such as Google Sign-In,
            Google Analytics, Google AdSense, Razorpay, Vercel hosting, MongoDB storage, and AI
            inference providers used to generate responses.
          </p>
        </Card>
      </div>

      <Card className="rounded-[1.8rem] border border-white/10 bg-slate-950/72 p-6 text-white sm:p-7">
        <h2 className="text-xl font-semibold">Consent, ads, and regional requirements</h2>
        <p className="mt-3 text-sm leading-7 text-slate-300">
          If advertising is enabled, consent tools may be shown where required by law or platform
          policy, including for users in the EEA, UK, and Switzerland. Ad and analytics partners
          may use cookies or similar technologies subject to those consent choices.
        </p>
      </Card>

      <Card className="rounded-[1.8rem] border border-white/10 bg-slate-950/72 p-6 text-white sm:p-7">
        <h2 className="text-xl font-semibold">Data requests and updates</h2>
        <p className="mt-3 text-sm leading-7 text-slate-300">
          If you need help with account-related data concerns, use the support channel listed on
          the contact page and provide enough detail to identify the relevant account or session.
          Operational and compliance handling may vary depending on what data is involved.
        </p>
      </Card>
      </StaticPageLayout>
    </>
  )
}
