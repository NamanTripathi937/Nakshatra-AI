"use client"

import React, { useEffect, useState } from "react"
import Image from "next/image"
import Link from "next/link"
import { useRouter } from "next/navigation"

import AccountHistory from "./AccountHistory"
import BillingPlansModal from "./BillingPlansModal"
import GoogleSignInButton from "./GoogleSignInButton"
import KundaliForm from "./KundaliForm"
import { Card } from "./ui/card"
import { buildAuthHeaders, useAuth } from "@/lib/auth"
import { getBackendUrl } from "@/lib/utils"

const conceptCards = [
  {
    title: "Free kundli with follow-up chat",
    body:
      "Generate a free kundli, keep the chart tied to the session, and ask follow-up Vedic astrology questions without losing the underlying chart context.",
  },
  {
    title: "Built around Vedic chart logic",
    body:
      "The reading flow is designed around Lagna, house lords, nakshatras, dasha timing, yogas, and divisional charts instead of generic sign-based astrology copy.",
  },
  {
    title: "Private by default",
    body:
      "Birth details, generated charts, and question history are deeply personal. Nakshatra AI is built so that this material stays attached to your account and visible only to you online.",
  },
]

const featureCards = [
  {
    title: "Generate your kundli",
    body:
      "Enter your birth details to create a Vedic chart and preserve the chart context for the rest of the reading session.",
  },
  {
    title: "Ask targeted chart questions",
    body:
      "Ask about marriage, career, timing, family, finances, compatibility, or recurring life patterns without disconnecting the answer from the chart.",
  },
  {
    title: "Return to saved readings",
    body:
      "A useful reading should not restart from zero after every visit. Recent chart sessions stay attached to your account so you can reopen them later.",
  },
]

const sampleReadingCards = [
  {
    title: "Sample career question",
    body:
      "“Which career patterns repeat in my chart, and does the current dasha support a role change or a longer period of consolidation?”",
  },
  {
    title: "Sample marriage question",
    body:
      "“What do the 7th house, Venus, and Navamsa suggest about relationship maturity, timing, and the kind of partner energy I tend to attract?”",
  },
  {
    title: "Sample life-pattern question",
    body:
      "“Why do the same emotional or family patterns keep resurfacing, and which planets or houses deserve the most attention first?”",
  },
]

const queryClusterLinks = [
  {
    href: "/free-kundli",
    title: "Free Kundli Online",
    body:
      "Start with the primary chart-generation query and explain how the kundli plus saved reading flow works.",
  },
  {
    href: "/ai-vedic-astrologer",
    title: "AI Vedic Astrologer",
    body:
      "Show how the chart-aware chat layer differs from generic astrology bots and static reports.",
  },
  {
    href: "/kundli-matching",
    title: "Kundli Matching",
    body:
      "Cover compatibility queries with broader Vedic relationship context instead of only one score.",
  },
  {
    href: "/navamsa-chart",
    title: "Navamsa Chart",
    body:
      "Build authority around D9, marriage refinement, maturity, and divisional chart reading.",
  },
  {
    href: "/vimshottari-dasha",
    title: "Vimshottari Dasha",
    body:
      "Own timing-oriented queries around mahadasha, antardasha, and chart activation periods.",
  },
  {
    href: "/mangal-dosh",
    title: "Mangal Dosh",
    body:
      "Handle a high-intent marriage query carefully without reducing it to fear-based astrology marketing.",
  },
  {
    href: "/daily-horoscope",
    title: "Daily Horoscope",
    body:
      "Build daily guidance pages that connect chart context, transits, and timing instead of generic sign messages.",
  },
  {
    href: "/panchang",
    title: "Panchang",
    body:
      "Open a daily-timing content cluster around tithi, nakshatra, yoga, karana, and practical planning.",
  },
  {
    href: "/numerology",
    title: "Numerology",
    body:
      "Add a lightweight name-and-birth-date numerology tool for Life Path, Destiny, Soul Urge, Personality, and other core numbers.",
  },
]

const faqItems = [
  {
    question: "What makes Nakshatra AI more useful than a generic astrology chatbot?",
    answer:
      "The reading flow is built around an actual generated kundli, so follow-up questions can stay grounded in Lagna, house lords, dasha timing, divisional charts, yogas, and other Vedic chart factors instead of drifting into sign-based filler.",
  },
  {
    question: "What birth details do I need for a free kundli?",
    answer:
      "You need the full name, date of birth, time of birth, and place of birth. The more accurate the birth time is, the more reliable the Lagna, house placements, divisional charts, and timing analysis become.",
  },
  {
    question: "Can I use Nakshatra AI for someone else’s chart?",
    answer:
      "Yes. If you have someone else’s birth details, you can generate their kundli too and ask chart-aware questions from that reading. The free and premium flows are not restricted to your own chart only.",
  },
  {
    question: "Does the site focus on Vedic astrology specifically?",
    answer:
      "Yes. The product is positioned around Vedic astrology and chart-based Jyotish logic, including Lagna, nakshatras, Vimshottari dasha, divisional charts such as Navamsa, and compatibility-oriented chart reading.",
  },
  {
    question: "How private are my kundli and chat sessions?",
    answer:
      "Birth details, generated readings, and follow-up questions are intended to stay private inside your account. The product treats saved chart history as sensitive information rather than casual public content.",
  },
  {
    question: "Is this a replacement for a human astrologer or professional advice?",
    answer:
      "No. It is a chart-aware digital reading tool meant for guidance, reflection, and exploration. It should not be treated as legal, medical, or financial advice, and it does not replace critical judgment in life-changing decisions.",
  },
]

export default function KundaliPage() {
  const [loading, setLoading] = useState(false)
  const [billingOpen, setBillingOpen] = useState(false)

  const router = useRouter()
  const backendUrl = getBackendUrl()
  const { user, token, loading: authLoading, error: authError } = useAuth()
  const hasActiveAccount = Boolean(user && token)

  useEffect(() => {
    fetch(`${backendUrl}/ping`).catch(() => {})
    console.log("Sent ping to backend")
  }, [backendUrl])

  const handleFormSubmit = async (data: any) => {
    if (loading || !token || !user) return
    setLoading(true)

    try {
      const sessionRes = await fetch(`${backendUrl}/sessions`, {
        method: "POST",
        headers: buildAuthHeaders(token),
      })
      if (!sessionRes.ok) {
        throw new Error("Unable to start a new reading session.")
      }
      const sessionData = await sessionRes.json()
      const sessionId = sessionData.session_id as string
      router.push(`/chatWindow/${sessionId}`)
      const res = await fetch(`${backendUrl}/kundli`, {
        method: "POST",
        headers: buildAuthHeaders(token, {
          "Content-Type": "application/json",
          "X-Session-Id": sessionId,
        }),
        body: JSON.stringify(data),
      })

      if (!res.ok) {
        throw new Error("Unable to generate your kundli.")
      }
    } catch (err) {
      console.error("kundli API error", err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex flex-1 px-4 py-6 sm:px-6 sm:py-8 lg:px-8 lg:py-8">
      <BillingPlansModal
        backendUrl={backendUrl}
        open={billingOpen}
        onClose={() => setBillingOpen(false)}
      />

      <div className="mx-auto flex w-full max-w-6xl flex-col gap-6 sm:gap-8">
        <section className="overflow-hidden rounded-[2rem] border border-white/8 bg-slate-950/72 p-6 text-white shadow-[0_24px_90px_rgba(6,11,24,0.45)] sm:p-8">
          <div className="inline-flex rounded-full border border-cyan-300/18 bg-cyan-400/8 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.22em] text-cyan-100">
            Meaningful Vedic Astrology
          </div>
          <div className="mt-5 grid gap-6 lg:grid-cols-[1.1fr_0.9fr] lg:items-start">
            <div className="max-w-3xl">
              <h1 className="bg-gradient-to-r from-white via-cyan-100 to-amber-200 bg-clip-text text-4xl font-semibold leading-none tracking-tight text-transparent sm:text-5xl lg:text-[4rem]">
                Free Kundli & AI Vedic Astrology Reading
              </h1>
              <h2 className="mt-3 max-w-2xl text-lg font-medium leading-relaxed text-cyan-100 sm:text-xl lg:text-[1.45rem]">
                Generate a chart-aware kundli, ask grounded Vedic astrology questions, and keep your reading session saved for later follow-up.
              </h2>
              <p className="mt-4 text-sm leading-7 text-slate-200 sm:text-base">
                Nakshatra AI is built for people searching for a free kundli online but wanting more than a static chart image. The goal is to combine Vedic chart generation with chart-aware AI reading so questions about marriage, career, timing, family, finances, and recurring life patterns stay attached to the same kundli context.
              </p>
              <p className="mt-4 text-sm leading-7 text-slate-300 sm:text-[15px]">
                The reading flow is designed around Vedic astrology concepts such as Lagna, house lords, nakshatras, Vimshottari dasha, yogas, and divisional charts like Navamsa. That is the difference between a chart-based reading and the kind of generic astrology output that sounds spiritual but is not actually tied to your birth chart.
              </p>
              <div className="mt-6 flex flex-wrap gap-3 text-sm">
                <a
                  href="#start-reading"
                  className="rounded-full border border-cyan-300/16 bg-cyan-400/10 px-4 py-2 text-cyan-100 transition-colors hover:bg-cyan-400/18"
                >
                  Start your free reading
                </a>
                <Link
                  href="/free-kundli"
                  className="rounded-full border border-cyan-300/16 bg-cyan-400/10 px-4 py-2 text-cyan-100 transition-colors hover:bg-cyan-400/18"
                >
                  Explore free kundli
                </Link>
                <Link
                  href="/numerology"
                  className="rounded-full border border-cyan-300/16 bg-cyan-400/10 px-4 py-2 text-cyan-100 transition-colors hover:bg-cyan-400/18"
                >
                  Try numerology
                </Link>
                <Link
                  href="/contact"
                  className="rounded-full border border-white/12 bg-white/8 px-4 py-2 text-slate-100 transition-colors hover:bg-white/14"
                >
                  Report an issue
                </Link>
                <Link
                  href="/privacy"
                  className="rounded-full border border-white/12 bg-white/8 px-4 py-2 text-slate-100 transition-colors hover:bg-white/14"
                >
                  Privacy and data
                </Link>
              </div>
            </div>

            <div className="space-y-4">
              <div className="hero-logo-stage relative mx-auto w-full max-w-[410px] lg:mr-0 lg:ml-auto">
                <div className="hero-logo-glow" aria-hidden="true" />
                <div className="hero-logo-shimmer" aria-hidden="true" />
                <div className="hero-logo-orbit relative flex min-h-[264px] items-center justify-center px-2 pt-2 pb-1">
                  <div className="hero-logo-ring" aria-hidden="true" />
                  <Image
                    src="/main-logo.png"
                    alt="Nakshatra AI main logo"
                    width={600}
                    height={586}
                    priority
                    className="hero-logo-image relative z-10 mx-auto h-auto w-full max-w-[348px]"
                  />
                </div>
              </div>

              <Card className="rounded-[1.8rem] border border-white/10 bg-slate-950/58 p-5 text-white shadow-[inset_0_1px_0_rgba(255,255,255,0.03)]">
                <div className="text-sm font-semibold uppercase tracking-[0.16em] text-cyan-100">
                  What this free kundli flow includes
                </div>
                <div className="mt-4 space-y-4 text-sm leading-6 text-slate-300">
                  <p>
                    Every account gets five free questions each day, and those questions stay attached to the generated kundli instead of floating separately from the chart context.
                  </p>
                  <p>
                    You can generate your own chart or someone else&apos;s chart if you have the birth details and want to explore marriage, career, family, timing, and compatibility questions sincerely.
                  </p>
                  <p>
                    Recent readings stay saved to the account so you can reopen sessions and continue the same line of questioning without losing the underlying kundli.
                  </p>
                </div>
              </Card>
            </div>
          </div>
        </section>

        <section
          id="start-reading"
          className="grid gap-5 lg:grid-cols-[minmax(240px,1fr)_minmax(380px,440px)_minmax(260px,1fr)] lg:items-start"
        >
          <aside className="space-y-3">
            <Card className="rounded-3xl border border-cyan-400/15 bg-slate-950/62 p-4 text-white shadow-[inset_0_1px_0_rgba(255,255,255,0.03)]">
              <div className="mb-2 text-sm font-semibold uppercase tracking-[0.18em] text-cyan-200">
                History
              </div>
              <p className="text-sm leading-6 text-slate-300">
                Reopen recent chart sessions, continue the same line of questioning, and keep your chart context attached to your account instead of losing it in a temporary browser tab.
              </p>
            </Card>

            {hasActiveAccount ? (
              <AccountHistory backendUrl={backendUrl} variant="embedded" limit={3} />
            ) : (
              <Card className="rounded-3xl border border-white/10 bg-slate-950/58 p-4 text-white">
                <div className="text-base font-semibold">History unlocks after sign-in</div>
                <p className="mt-2 text-sm leading-6 text-slate-300">
                  Once you sign in, your readings stay private to your account and appear here for quick access across devices.
                </p>
              </Card>
            )}
          </aside>

          <section className="space-y-4">
            <div className="flex justify-center">
              <div className="w-full max-w-[440px]">
                {hasActiveAccount ? (
                  <div className="space-y-3">
                    {authLoading ? (
                      <Card className="rounded-[1.75rem] border border-cyan-400/15 bg-slate-950/62 p-4 text-sm text-slate-300 shadow-[inset_0_1px_0_rgba(255,255,255,0.03)] backdrop-blur-md">
                        Restoring your account in the background. You can start entering kundli details now.
                      </Card>
                    ) : null}
                    <KundaliForm onSubmit={handleFormSubmit} loading={loading} />
                    {authError ? <p className="text-sm text-rose-300">{authError}</p> : null}
                  </div>
                ) : authLoading ? (
                  <Card className="rounded-[1.75rem] border border-cyan-400/15 bg-slate-950/62 p-5 text-sm text-slate-300 shadow-[inset_0_1px_0_rgba(255,255,255,0.03)] backdrop-blur-md sm:p-6">
                    Restoring your account…
                  </Card>
                ) : (
                  <Card
                    id="auth-panel"
                    className="rounded-[1.8rem] border border-cyan-400/15 bg-slate-950/62 p-5 text-center text-white shadow-[inset_0_1px_0_rgba(255,255,255,0.03)] backdrop-blur-md sm:p-5"
                  >
                    <div className="mb-3 inline-flex rounded-full border border-cyan-400/18 bg-cyan-500/8 px-3 py-1 text-[10px] font-semibold uppercase tracking-[0.18em] text-cyan-200">
                      Secure Account Access
                    </div>
                    <div className="mb-2 text-[1.45rem] font-semibold leading-tight sm:text-[1.75rem]">
                      Sign in or sign up to begin your kundli reading
                    </div>
                    <p className="mx-auto mb-4 max-w-sm text-sm leading-6 text-slate-300">
                      Your readings live under your account so the generated chart, private questions, and follow-up answers stay connected to the same session.
                    </p>
                    <div className="mb-4 inline-flex rounded-full border border-white/10 bg-white/6 px-3 py-1 text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-200">
                      Continue With Google
                    </div>
                    <div className="flex justify-center">
                      <GoogleSignInButton text="signup_with" />
                    </div>
                    {authError ? <p className="mt-4 text-sm text-rose-300">{authError}</p> : null}
                  </Card>
                )}
              </div>
            </div>

            <Card className="rounded-3xl border border-white/10 bg-slate-950/60 p-4 text-white">
              <div className="mb-2 text-base font-semibold">Free</div>
              <ul className="space-y-1.5 text-sm text-slate-300">
                <li>5 questions per day</li>
                <li>Ask about your chart or someone else&apos;s</li>
                <li>Basic kundli generation and Lagna access</li>
                <li>Private saved session history</li>
              </ul>
            </Card>
          </section>

          <aside className="space-y-4">
            <div className="space-y-2">
              <div className="inline-flex rounded-full border border-cyan-400/20 bg-cyan-500/10 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.18em] text-cyan-200">
                Reading Access
              </div>
              <h2 className="text-[1.9rem] font-semibold leading-tight text-white sm:text-[2.2rem]">
                Start with a free kundli, then upgrade only if the depth feels worth it.
              </h2>
              <p className="text-sm leading-6 text-slate-300 sm:text-[15px]">
                The free layer is meant to be genuinely useful for seekers who want a kundli, a few chart-aware questions, and saved session history. Premium exists for people who want deeper Vedic astrology interpretation, more continuity, and access to additional chart tools.
              </p>
            </div>

            <Card className="rounded-3xl border border-amber-400/25 bg-[radial-gradient(circle_at_top,_rgba(251,191,36,0.18),_rgba(15,23,42,0.94)_58%)] p-4 text-white">
              <div className=" text-base font-semibold">Premium</div>
              <ul className="space-y-1.5 text-sm text-slate-200">
                <li>Unlimited questions</li>
                <li>Deep-dive interpretations and remedies</li>
                <li>D9, D10, matching, and transit insights</li>
                <li>More value without predatory pricing</li>
                <li className=" text-xs text-amber-200/90">Rs. 99 monthly</li>
              </ul>
              <div className="">
                <button
                  type="button"
                  onClick={() => setBillingOpen(true)}
                  className=" rounded-full border border-amber-200/18 bg-amber-300/12 px-4 py-2 text-sm font-medium text-amber-50 transition-colors hover:bg-amber-300/18"
                >
                  View premium access
                </button>
                
              </div>
            </Card>
          </aside>
        </section>

        <section className="grid gap-4 lg:grid-cols-[1.05fr_0.95fr]">
          <Card className="rounded-[1.8rem] border border-white/10 bg-slate-950/72 p-6 text-white sm:p-7">
            <div className="text-sm font-semibold uppercase tracking-[0.18em] text-cyan-100">
              How Nakshatra AI reads a chart
            </div>
            <h2 className="mt-3 text-2xl font-semibold leading-tight">
              The kundli comes first, and the conversation stays loyal to that chart.
            </h2>
            <p className="mt-4 text-sm leading-7 text-slate-300 sm:text-[15px]">
              A useful Vedic astrology answer usually depends on more than one placement. Marriage, career, health, family, finances, and life direction often require the Lagna, house lords, yogas, planetary dignity, divisional charts, and dasha timing to be read together rather than cherry-picked one by one.
            </p>
            <p className="mt-4 text-sm leading-7 text-slate-300 sm:text-[15px]">
              That is why the product is built around chart context first and chat second. The aim is to make the AI answer feel more like a chart-based interpretation and less like a keyword-matching horoscope generator.
            </p>
          </Card>

          <Card className="rounded-[1.8rem] border border-cyan-400/14 bg-slate-950/72 p-6 text-white sm:p-7">
            <div className="text-sm font-semibold uppercase tracking-[0.18em] text-cyan-100">
              Why the project exists
            </div>
            <p className="mt-4 text-sm leading-7 text-slate-300 sm:text-[15px]">
              Too many astrology products monetize confusion with vague language, shallow reports, or fear-driven upsells. Nakshatra AI is meant to push in the opposite direction: clearer reasoning, fairer access, and answers that at least try to remain faithful to the underlying Vedic chart.
            </p>
            <p className="mt-4 text-sm leading-7 text-slate-300 sm:text-[15px]">
              The product is still early, but the long-term direction is simple: become a genuinely useful place for free kundli generation, chart-based AI readings, compatibility analysis, divisional chart exploration, and Vedic timing guidance.
            </p>
          </Card>
        </section>

        <section className="grid gap-4 md:grid-cols-3">
          {conceptCards.map((card) => (
            <Card
              key={card.title}
              className="rounded-[1.6rem] border border-cyan-400/14 bg-slate-950/68 p-5 text-white"
            >
              <h3 className="text-lg font-semibold">{card.title}</h3>
              <p className="mt-3 text-sm leading-6 text-slate-300">{card.body}</p>
            </Card>
          ))}
        </section>

        <section className="rounded-[2rem] border border-white/10 bg-slate-950/72 p-6 text-white sm:p-7">
          <div className="max-w-3xl">
            <div className="text-sm font-semibold uppercase tracking-[0.18em] text-cyan-100">
              How the reading flow works
            </div>
            <h2 className="mt-3 text-2xl font-semibold leading-tight">
              Built for people who want a living chart conversation, not a one-time chart dump.
            </h2>
          </div>
          <div className="mt-6 grid gap-4 md:grid-cols-3">
            {featureCards.map((card) => (
              <div
                key={card.title}
                className="rounded-[1.4rem] border border-white/10 bg-white/4 p-4"
              >
                <h3 className="text-base font-semibold">{card.title}</h3>
                <p className="mt-3 text-sm leading-6 text-slate-300">{card.body}</p>
              </div>
            ))}
          </div>
        </section>

        <section className="rounded-[2rem] border border-white/10 bg-slate-950/72 p-6 text-white sm:p-7">
          <div className="max-w-3xl">
            <div className="text-sm font-semibold uppercase tracking-[0.18em] text-cyan-100">
              Sample Reading Prompts
            </div>
            <h2 className="mt-3 text-2xl font-semibold leading-tight">
              These are the kinds of questions the chart-aware flow is built to handle.
            </h2>
          </div>
          <div className="mt-6 grid gap-4 md:grid-cols-3">
            {sampleReadingCards.map((card) => (
              <Card
                key={card.title}
                className="rounded-[1.5rem] border border-white/10 bg-white/4 p-5 text-white"
              >
                <h3 className="text-base font-semibold">{card.title}</h3>
                <p className="mt-3 text-sm leading-6 text-slate-300">{card.body}</p>
              </Card>
            ))}
          </div>
        </section>

        <section className="grid gap-4 lg:grid-cols-[1fr_1fr]">
          <Card className="rounded-[1.8rem] border border-white/10 bg-slate-950/72 p-6 text-white sm:p-7">
            <div className="text-sm font-semibold uppercase tracking-[0.18em] text-cyan-100">
              Questions people actually bring here
            </div>
            <ul className="mt-4 space-y-3 text-sm leading-7 text-slate-300">
              <li>What does my chart show about marriage, relationships, and long-term compatibility?</li>
              <li>Which career patterns repeat in my chart, and when are they likely to mature?</li>
              <li>Why do I keep facing the same emotional or family-based challenges?</li>
              <li>Which planets or chart combinations deserve more attention before I take a major decision?</li>
            </ul>
          </Card>

          <Card className="rounded-[1.8rem] border border-white/10 bg-slate-950/72 p-6 text-white sm:p-7">
            <div className="text-sm font-semibold uppercase tracking-[0.18em] text-cyan-100">
              Privacy and trust
            </div>
            <p className="mt-4 text-sm leading-7 text-slate-300 sm:text-[15px]">
              A kundli can reveal intimate information about personality, family, timing, and vulnerability. That is why privacy is treated as part of the product, not as an afterthought. Your saved readings and question history are intended to remain personal, encrypted, and visible only to you online.
            </p>
          </Card>
        </section>

        <section className="rounded-[2rem] border border-white/10 bg-slate-950/72 p-6 text-white sm:p-7">
          <div className="max-w-3xl">
            <div className="text-sm font-semibold uppercase tracking-[0.18em] text-cyan-100">
              A note from the creator
            </div>
            <h2 className="mt-3 text-2xl font-semibold leading-tight">
              Nakshatra AI is still in its initial phase, and I&apos;m grateful you&apos;re here early.
            </h2>
            <p className="mt-4 text-sm leading-7 text-slate-300 sm:text-[15px]">
              Please forgive the occasional inconvenience while the platform matures. I&apos;m continuously improving the astrology logic, the product flow, and the quality of responses so the experience becomes more dependable with every release.
            </p>
            <p className="mt-4 text-sm leading-7 text-slate-300 sm:text-[15px]">
              If you run into a bug, a confusing result, or anything that feels broken, please use the report link or send an email. I would genuinely love to connect with fellow seekers and improve the platform through real feedback.
            </p>
            <div className="mt-6 flex flex-wrap gap-3 text-sm">
              <Link
                href="/contact"
                className="rounded-full border border-cyan-300/16 bg-cyan-400/10 px-4 py-2 text-cyan-100 transition-colors hover:bg-cyan-400/18"
              >
                Report an issue
              </Link>
              <a
                href="mailto:namantripathi937@gmail.com"
                className="rounded-full border border-white/12 bg-white/8 px-4 py-2 text-slate-100 transition-colors hover:bg-white/14"
              >
                Email Naman
              </a>
            </div>
            <p className="mt-5 text-sm font-medium text-cyan-100">🙏 Om Namah Shivay</p>
          </div>
        </section>

        <section className="rounded-[2rem] border border-white/10 bg-slate-950/72 p-6 text-white sm:p-7">
          <div className="max-w-3xl">
            <div className="text-sm font-semibold uppercase tracking-[0.18em] text-cyan-100">
              Explore By Search Intent
            </div>
            <h2 className="mt-3 text-2xl font-semibold leading-tight">
              Dedicated pages for the Vedic astrology topics people actually search for.
            </h2>
          </div>
          <div className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {queryClusterLinks.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className="rounded-[1.5rem] border border-white/10 bg-white/4 p-5 text-white transition-colors hover:border-cyan-300/25 hover:bg-white/8"
              >
                <h3 className="text-lg font-semibold">{item.title}</h3>
                <p className="mt-3 text-sm leading-6 text-slate-300">{item.body}</p>
              </Link>
            ))}
          </div>
        </section>

        <section className="rounded-[2rem] border border-white/10 bg-slate-950/72 p-6 text-white sm:p-7">
          <div className="max-w-3xl">
            <div className="text-sm font-semibold uppercase tracking-[0.18em] text-cyan-100">
              Frequently asked questions
            </div>
            <h2 className="mt-3 text-2xl font-semibold leading-tight">
              Questions people search before they generate a kundli
            </h2>
          </div>
          <div className="mt-6 grid gap-4 lg:grid-cols-2">
            {faqItems.map((item) => (
              <Card
                key={item.question}
                className="rounded-[1.5rem] border border-white/10 bg-white/4 p-5 text-white"
              >
                <h3 className="text-base font-semibold">{item.question}</h3>
                <p className="mt-3 text-sm leading-6 text-slate-300">{item.answer}</p>
              </Card>
            ))}
          </div>
        </section>
      </div>
    </div>
  )
}
