"use client"

import React, { useEffect, useState } from "react"
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
    title: "5 free questions every day",
    body:
      "Every account gets five free queries daily before you ever need to upgrade. You can ask about your own chart or provide someone else's birth details when you are reading for family, friends, or loved ones.",
  },
  {
    title: "Private by default",
    body:
      "Birth details, generated charts, and question history are deeply personal. Nakshatra AI is built so that this material stays attached to your account and visible only to you online.",
  },
  {
    title: "Meaning over exploitation",
    body:
      "Astrology should help people, not scare or overcharge them. The goal here is to deliver answers that feel worth the price, instead of vague content padded with fear, urgency, or gimmicks.",
  },
]

const featureCards = [
  {
    title: "Ask about any chart",
    body:
      "You are not limited to your own horoscope. If you have the birth details, you can generate a chart and explore questions for parents, partners, children, or anyone else you are studying sincerely.",
  },
  {
    title: "Context stays with the session",
    body:
      "A useful reading should not restart from zero after every message. The chart context stays attached to the session so follow-up questions remain grounded in the same kundli.",
  },
  {
    title: "Upgrade only when it feels justified",
    body:
      "The free tier is meant to be genuinely usable. Premium exists for people who want more depth, more continuity, and advanced tools such as divisional charts, remedies, and compatibility analysis.",
  },
]

const faqItems = [
  {
    question: "What kind of questions is Nakshatra AI built for?",
    answer:
      "The site is built for chart-based questions on themes such as relationships, marriage, career, finances, life direction, strengths, recurring obstacles, timing patterns, and the deeper meaning of placements through Vedic astrology.",
  },
  {
    question: "Can I use it for charts other than my own?",
    answer:
      "Yes. The free and premium experience are not restricted to your own chart. If you have someone's birth details, you can generate their kundli and ask questions from that chart context too.",
  },
  {
    question: "How private is my chart data?",
    answer:
      "Birth details, generated readings, and follow-up questions are intended to stay private inside your account. The platform is built around privacy because chart data often touches sensitive personal and family matters.",
  },
  {
    question: "Is the platform still in an early phase?",
    answer:
      "Yes. Nakshatra AI is still in its initial phase, and the experience will continue to improve. If you notice bugs or rough edges, please report them. Thoughtful feedback from real seekers is a major part of how the platform gets better.",
  },
]

export default function KundaliPage() {
  const [loading, setLoading] = useState(false)
  const [billingOpen, setBillingOpen] = useState(false)

  const router = useRouter()
  const backendUrl = getBackendUrl()
  const { user, token, loading: authLoading, error: authError } = useAuth()

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
        <section className="overflow-hidden rounded-[2rem] border border-cyan-400/18 bg-[radial-gradient(circle_at_top_left,_rgba(34,211,238,0.14),_rgba(8,15,30,0.94)_38%,_rgba(5,10,20,0.98)_100%)] p-6 text-white shadow-[0_24px_90px_rgba(6,11,24,0.45)] sm:p-8">
          <div className="inline-flex rounded-full border border-cyan-300/18 bg-cyan-400/8 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.22em] text-cyan-100">
            Meaningful Vedic Astrology
          </div>
          <div className="mt-5 grid gap-6 lg:grid-cols-[1.1fr_0.9fr] lg:items-start">
            <div className="max-w-3xl">
              <h1 className="bg-gradient-to-r from-white via-cyan-100 to-amber-200 bg-clip-text text-4xl font-semibold leading-none tracking-tight text-transparent sm:text-5xl lg:text-[4rem]">
                Nakshatra AI
              </h1>
              <h2 className="mt-3 max-w-2xl text-lg font-medium leading-relaxed text-cyan-100 sm:text-xl lg:text-[1.45rem]">
                For the seekers who still believe there is meaning in the sky, timing in the chart, and light in the questions they carry.
              </h2>
              <p className="mt-4 text-sm leading-7 text-slate-200 sm:text-base">
                I created Nakshatra AI because too many astrology platforms charge a lot of money for shallow, generic, or fear-driven content. This project is built around a simpler principle: if someone comes with a real question, the answer should be thoughtful, grounded in the chart, respectful of their privacy, and genuinely worth the price.
              </p>
              <p className="mt-4 text-sm leading-7 text-slate-300 sm:text-[15px]">
                Vedic astrology can illuminate timing, temperament, relationships, career direction, recurring life patterns, and deeper questions of purpose, but only when it is handled with discipline and honesty. Nakshatra AI is meant to bring that seriousness into a conversational product without turning sacred knowledge into a manipulative sales funnel.
              </p>
              <div className="mt-6 flex flex-wrap gap-3 text-sm">
                <a
                  href="#start-reading"
                  className="rounded-full border border-cyan-300/16 bg-cyan-400/10 px-4 py-2 text-cyan-100 transition-colors hover:bg-cyan-400/18"
                >
                  Start your free reading
                </a>
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

            <Card className="rounded-[1.8rem] border border-white/10 bg-slate-950/58 p-5 text-white shadow-[inset_0_1px_0_rgba(255,255,255,0.03)]">
              <div className="text-sm font-semibold uppercase tracking-[0.16em] text-cyan-100">
                What makes this different
              </div>
              <div className="mt-4 space-y-4 text-sm leading-6 text-slate-300">
                <p>
                  Every user gets five free queries each day, and those queries are not limited to just one chart. If you have the right birth details, you can explore your own horoscope or ask about someone else's chart with the same seriousness.
                </p>
                <p>
                  The product is designed to answer curious, personal, and meaningful questions through Vedic astrology and related chart sciences, not by producing vague motivational filler.
                </p>
                <p>
                  Privacy matters here. Your chart data, your questions, and your session history are intended to remain visible only to you inside your own account.
                </p>
              </div>
            </Card>
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

            {user ? (
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
                {authLoading ? (
                  <Card className="rounded-[1.75rem] border border-cyan-400/15 bg-slate-950/62 p-5 text-sm text-slate-300 shadow-[inset_0_1px_0_rgba(255,255,255,0.03)] backdrop-blur-md sm:p-6">
                    Restoring your account…
                  </Card>
                ) : !user ? (
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
                ) : (
                  <KundaliForm onSubmit={handleFormSubmit} loading={loading} />
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
                Choose your path and only upgrade when the value feels real.
              </h2>
              <p className="text-sm leading-6 text-slate-300 sm:text-[15px]">
                Free accounts are meant to be genuinely useful, not a teaser that gives you nothing. Premium exists for seekers who want deeper interpretation, more continuity, and advanced Vedic astrology tools at a price that respects their trust.
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
              Our philosophy
            </div>
            <h2 className="mt-3 text-2xl font-semibold leading-tight">
              Astrology should guide people, not exploit them.
            </h2>
            <p className="mt-4 text-sm leading-7 text-slate-300 sm:text-[15px]">
              The first rule of astrology, at least as I understand it, is that this knowledge should serve society and improve the future, not prey on uncertainty. People come to astrology when they are vulnerable, curious, confused, or hopeful. That makes integrity more important, not less.
            </p>
            <p className="mt-4 text-sm leading-7 text-slate-300 sm:text-[15px]">
              Nakshatra AI is my attempt to build an astrology product that keeps that ethic intact: meaningful answers, useful access, fair pricing, and a refusal to turn every question into a fear-based upsell.
            </p>
          </Card>

          <Card className="rounded-[1.8rem] border border-cyan-400/14 bg-slate-950/72 p-6 text-white sm:p-7">
            <div className="text-sm font-semibold uppercase tracking-[0.18em] text-cyan-100">
              What a valuable reading requires
            </div>
            <p className="mt-4 text-sm leading-7 text-slate-300 sm:text-[15px]">
              A worthwhile Vedic astrology answer cannot come from one placement taken in isolation. Questions around marriage, career, health, family, finances, and life direction usually depend on the Lagna, house lords, planetary dignity, yogas, divisional charts, and dasha timing working together.
            </p>
            <p className="mt-4 text-sm leading-7 text-slate-300 sm:text-[15px]">
              That is why the product is built around chart context first and chat second. The conversation is useful only when it stays loyal to the mathematical and interpretive reality of the kundli underneath it.
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
              Built for curious seekers who want a living conversation, not a one-time chart dump.
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
              Frequently asked questions
            </div>
            <h2 className="mt-3 text-2xl font-semibold leading-tight">
              Questions visitors often have before they begin
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
