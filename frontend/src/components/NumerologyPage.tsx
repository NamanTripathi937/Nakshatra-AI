"use client"

import Link from "next/link"
import type { ReactNode } from "react"
import { useState } from "react"
import { CalendarDays, Loader2, Sparkles, UserRound } from "lucide-react"

import NumerologyCard from "@/components/NumerologyCard"
import StaticPageLayout from "@/components/StaticPageLayout"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  buildInsightSections,
  buildOrientationPanels,
  buildReadingSummary,
  type NumerologyKey,
  type NumerologyNumber,
} from "@/lib/numerology-content"
import { getBackendUrl } from "@/lib/utils"

type NumerologyResponse = {
  input: {
    full_name: string
    normalized_name: string
    date_of_birth: string
  }
  system: {
    name_method: string
    date_method: string
  }
  core_numbers: NumerologyNumber[]
  highlights: string[]
  notes: string[]
  name_breakdown: {
    all_letters: string[]
    vowels: string[]
    consonants: string[]
  }
}

const resultOrder: NumerologyKey[] = [
  "life_path",
  "destiny",
  "soul_urge",
  "personality",
  "birthday",
  "attitude",
]

const previewItems = [
  {
    title: "A central path",
    body:
      "Your Life Path becomes the main arc of the reading, showing the deeper qualities your life keeps developing over time.",
  },
  {
    title: "A private inner truth",
    body:
      "Your Soul Urge reveals what your heart wants beneath performance, obligation, and social roles.",
  },
  {
    title: "A visible outer style",
    body:
      "Your Destiny and Personality numbers explain how your gifts, presence, and contribution tend to be felt by others.",
  },
  {
    title: "A layered reflection",
    body:
      "Instead of a raw list of numbers, the page turns your profile into a guided reading with long-form interpretation and quieter detail.",
  },
]

const NUMEROLOGY_GUIDES: Record<NumerologyKey, { href: string; label: string }> = {
  life_path: {
    href: "/guides/what-life-path-number-means",
    label: "Life Path",
  },
  destiny: {
    href: "/guides/what-destiny-number-means",
    label: "Destiny",
  },
  soul_urge: {
    href: "/guides/what-soul-urge-number-means",
    label: "Soul Urge",
  },
  personality: {
    href: "/guides/what-personality-number-means",
    label: "Personality",
  },
  birthday: {
    href: "/guides/what-birthday-number-means",
    label: "Birthday Number",
  },
  attitude: {
    href: "/guides/what-attitude-number-means",
    label: "Attitude Number",
  },
}

function GuideTextLink({
  guide,
  children,
}: {
  guide: { href: string; label: string }
  children?: ReactNode
}) {
  return (
    <Link
      href={guide.href}
      className="font-medium text-cyan-200 underline decoration-cyan-300/60 underline-offset-4 transition-colors hover:text-white hover:decoration-cyan-100"
    >
      {children || guide.label}
    </Link>
  )
}

function formatFriendlyDate(value: string) {
  const [year, month, day] = value.split("-").map(Number)
  if (!year || !month || !day) return value

  return new Intl.DateTimeFormat("en-US", {
    month: "long",
    day: "numeric",
    year: "numeric",
    timeZone: "UTC",
  }).format(new Date(Date.UTC(year, month - 1, day)))
}

export default function NumerologyPage() {
  const backendUrl = getBackendUrl()
  const [fullName, setFullName] = useState("")
  const [dateOfBirth, setDateOfBirth] = useState("")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")
  const [result, setResult] = useState<NumerologyResponse | null>(null)

  const orderedNumbers = result
    ? resultOrder
        .map((key) => result.core_numbers.find((item) => item.key === key))
        .filter((item): item is NumerologyNumber => Boolean(item))
    : []

  const numberLookup = Object.fromEntries(orderedNumbers.map((item) => [item.key, item])) as Partial<
    Record<NumerologyKey, NumerologyNumber>
  >

  const summaryParagraphs = result
    ? buildReadingSummary(result.input.full_name, numberLookup)
    : []
  const insightSections = buildInsightSections(numberLookup)
  const orientationPanels = buildOrientationPanels(numberLookup)

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setLoading(true)
    setError("")

    try {
      const response = await fetch(`${backendUrl}/numerology`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          fullName,
          dateOfBirth,
        }),
      })

      const payload = await response.json()
      if (!response.ok) {
        throw new Error(payload.detail || "Unable to prepare your numerology reading right now.")
      }

      setResult(payload)
    } catch (submitError) {
      setResult(null)
      setError(
        submitError instanceof Error
          ? submitError.message
          : "Something went wrong while preparing your reading."
      )
    } finally {
      setLoading(false)
    }
  }

  return (
    <StaticPageLayout
      eyebrow="Numerology Reading"
      title="Discover the deeper blueprint of your life journey."
      intro="Your birth date and full name hold a symbolic pattern of gifts, inner longings, visible strengths, and recurring lessons. This reading is designed to feel less like a calculation tool and more like a thoughtful mirror: revealing the style of growth your life keeps asking of you."
    >
      <section className="grid gap-5 xl:grid-cols-[minmax(340px,420px)_minmax(0,1fr)]">
        <Card className="rounded-[2rem] border border-cyan-300/14 bg-[linear-gradient(180deg,rgba(8,15,30,0.96),rgba(2,6,23,0.96))] p-6 text-white shadow-[0_22px_80px_rgba(3,8,20,0.34)] sm:p-7">
          <div className="inline-flex rounded-full border border-cyan-300/18 bg-cyan-400/8 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.22em] text-cyan-100">
            Begin Your Reading
          </div>
          <h2 className="mt-4 font-serif text-[2rem] leading-tight text-white">
            Reveal the numbers that quietly shape your path.
          </h2>
          <p className="mt-3 text-sm leading-7 text-slate-300">
            Enter the name you want this reading to reflect, along with your date of birth.
            You&apos;ll receive a detailed non-AI numerology interpretation focused on meaning,
            emotional resonance, and the kind of self-understanding people actually enjoy reading.
          </p>

          <form onSubmit={handleSubmit} className="mt-6 space-y-4">
            <div className="space-y-2">
              <Label htmlFor="numerology-name" className="text-slate-200">
                <UserRound className="h-4 w-4 text-cyan-200" />
                Full Name
              </Label>
              <Input
                id="numerology-name"
                type="text"
                value={fullName}
                onChange={(event) => setFullName(event.target.value)}
                placeholder="Enter your full name"
                className="h-11 rounded-xl border-white/10 bg-slate-900/85 px-4 text-white placeholder:text-slate-500"
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="numerology-dob" className="text-slate-200">
                <CalendarDays className="h-4 w-4 text-cyan-200" />
                Date of Birth
              </Label>
              <Input
                id="numerology-dob"
                type="date"
                value={dateOfBirth}
                onChange={(event) => setDateOfBirth(event.target.value)}
                className="h-11 rounded-xl border-white/10 bg-slate-900/85 px-4 text-white"
                required
              />
            </div>

            {error ? (
              <p className="rounded-xl border border-rose-300/10 bg-rose-500/8 px-4 py-3 text-sm text-rose-200">
                {error}
              </p>
            ) : null}

            <Button
              type="submit"
              disabled={loading}
              className="h-11 w-full rounded-full bg-[linear-gradient(90deg,rgba(251,191,36,0.96),rgba(103,232,249,0.96))] text-slate-950 shadow-lg hover:opacity-95"
            >
              {loading ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Preparing your reading
                </>
              ) : (
                <>
                  <Sparkles className="h-4 w-4" />
                  Reveal my numerology
                </>
              )}
            </Button>
          </form>
        </Card>

        <Card className="rounded-[2rem] border border-white/10 bg-[radial-gradient(circle_at_top_left,_rgba(251,191,36,0.12),_rgba(34,211,238,0.08)_24%,_rgba(2,6,23,0.94)_72%)] p-6 text-white shadow-[0_22px_80px_rgba(3,8,20,0.28)] sm:p-7">
          {result ? (
            <>
              <div className="inline-flex rounded-full border border-amber-300/18 bg-amber-300/10 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.22em] text-amber-100">
                Reading Opened
              </div>
              <h2 className="mt-4 font-serif text-[2rem] leading-tight">
                A first look at your inner pattern
              </h2>
              <p className="mt-3 text-sm leading-7 text-slate-300">
                This reading reflects{" "}
                <span className="font-medium text-white">{result.input.full_name}</span> and the
                birth date of{" "}
                <span className="font-medium text-white">
                  {formatFriendlyDate(result.input.date_of_birth)}
                </span>
                .
              </p>
              <div className="mt-5 rounded-[1.5rem] border border-white/10 bg-black/12 p-4 sm:p-5">
                <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-cyan-100">
                  Why these numbers are used
                </div>
                <p className="mt-3 text-sm leading-7 text-slate-300">
                  Numerology does not pick these labels randomly. It looks at different parts of
                  your birth date and name, then uses those patterns to answer different questions
                  about your life. If you are new to numerology, start with{" "}
                  <GuideTextLink guide={NUMEROLOGY_GUIDES.life_path} />, which is taken from your
                  birth date and acts like the central road of the reading.{" "}
                  <GuideTextLink guide={NUMEROLOGY_GUIDES.destiny} /> comes from the full name and
                  speaks to expression and contribution, while{" "}
                  <GuideTextLink guide={NUMEROLOGY_GUIDES.soul_urge} /> and{" "}
                  <GuideTextLink guide={NUMEROLOGY_GUIDES.personality} /> describe the private
                  inner world and the outer social impression. The supporting tones come from{" "}
                  <GuideTextLink guide={NUMEROLOGY_GUIDES.birthday} /> and{" "}
                  <GuideTextLink guide={NUMEROLOGY_GUIDES.attitude} />, which help explain your
                  natural style and the energy you lead with.
                </p>
                <div className="mt-4 flex flex-wrap gap-2">
                  {resultOrder.map((key) => (
                    <GuideTextLink key={key} guide={NUMEROLOGY_GUIDES[key]}>
                      <span className="inline-flex rounded-full border border-cyan-300/16 bg-cyan-400/8 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.16em]">
                        {NUMEROLOGY_GUIDES[key].label}
                      </span>
                    </GuideTextLink>
                  ))}
                </div>
              </div>
              <div className="mt-5 space-y-4">
                {summaryParagraphs.map((paragraph) => (
                  <p key={paragraph} className="text-[15px] leading-8 text-slate-200">
                    {paragraph}
                  </p>
                ))}
              </div>
            </>
          ) : (
            <>
              <div className="inline-flex rounded-full border border-white/10 bg-white/6 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.22em] text-slate-200">
                What You&apos;ll Receive
              </div>
              <h2 className="mt-4 font-serif text-[2rem] leading-tight">
                A reading meant to feel reflective, not mechanical
              </h2>
              <p className="mt-3 max-w-2xl text-sm leading-7 text-slate-300">
                Most numerology tools stop at labels and numbers. This one is being shaped as a
                layered reading: something calmer, more intimate, and more rewarding to spend time
                with.
              </p>
              <div className="mt-6 grid gap-4 sm:grid-cols-2">
                {previewItems.map((item) => (
                  <div
                    key={item.title}
                    className="rounded-[1.4rem] border border-white/10 bg-white/4 p-4"
                  >
                    <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-cyan-100">
                      {item.title}
                    </div>
                    <p className="mt-3 text-sm leading-7 text-slate-300">{item.body}</p>
                  </div>
                ))}
              </div>
            </>
          )}
        </Card>
      </section>

      {result && numberLookup.life_path ? (
        <>
          <section className="grid gap-4">
            <NumerologyCard item={numberLookup.life_path} featured />
          </section>

          <section className="grid gap-4">
            <div className="max-w-3xl">
              <div className="text-[11px] font-semibold uppercase tracking-[0.22em] text-cyan-100">
                Core Inner Landscape
              </div>
              <h2 className="mt-3 font-serif text-3xl leading-tight text-white">
                The inner motives and outer expression around your main path
              </h2>
              <p className="mt-3 text-sm leading-7 text-slate-300">
                <GuideTextLink guide={NUMEROLOGY_GUIDES.destiny} />,{" "}
                <GuideTextLink guide={NUMEROLOGY_GUIDES.soul_urge} />, and{" "}
                <GuideTextLink guide={NUMEROLOGY_GUIDES.personality} /> reveal how your deeper path
                becomes visible in daily life: what your heart seeks, how your gifts want to be
                expressed, and what kind of energy people often feel from you before they know your
                whole story.
              </p>
            </div>

            <div className="grid gap-4 lg:grid-cols-3">
              {numberLookup.destiny ? <NumerologyCard item={numberLookup.destiny} /> : null}
              {numberLookup.soul_urge ? <NumerologyCard item={numberLookup.soul_urge} /> : null}
              {numberLookup.personality ? <NumerologyCard item={numberLookup.personality} /> : null}
            </div>
          </section>

          <section className="grid gap-4">
            <div className="max-w-3xl">
              <div className="text-[11px] font-semibold uppercase tracking-[0.22em] text-cyan-100">
                Supporting Influences
              </div>
              <h2 className="mt-3 font-serif text-3xl leading-tight text-white">
                The smaller tones that color your everyday style
              </h2>
              <p className="mt-3 text-sm leading-7 text-slate-300">
                Your <GuideTextLink guide={NUMEROLOGY_GUIDES.birthday} /> and{" "}
                <GuideTextLink guide={NUMEROLOGY_GUIDES.attitude} /> are not the whole story, but
                they often explain a lot about your instinctive style, your first responses, and
                the subtle flavor people notice around you in ordinary life.
              </p>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              {numberLookup.birthday ? <NumerologyCard item={numberLookup.birthday} /> : null}
              {numberLookup.attitude ? <NumerologyCard item={numberLookup.attitude} /> : null}
            </div>
          </section>

          <section className="grid gap-4">
            <div className="max-w-3xl">
              <div className="text-[11px] font-semibold uppercase tracking-[0.22em] text-cyan-100">
                Read Together
              </div>
              <h2 className="mt-3 font-serif text-3xl leading-tight text-white">
                How these numbers speak to each other
              </h2>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              {insightSections.map((section) => (
                <Card
                  key={section.title}
                  className="rounded-[1.75rem] border border-white/10 bg-[linear-gradient(180deg,rgba(15,23,42,0.94),rgba(2,6,23,0.94))] p-6 text-white shadow-[0_18px_60px_rgba(4,10,24,0.22)]"
                >
                  <h3 className="font-serif text-[1.55rem] leading-tight">{section.title}</h3>
                  <p className="mt-4 text-sm leading-8 text-slate-300">{section.body}</p>
                </Card>
              ))}
            </div>
          </section>

          <section className="grid gap-4">
            <div className="max-w-3xl">
              <div className="text-[11px] font-semibold uppercase tracking-[0.22em] text-cyan-100">
                Life Themes
              </div>
              <h2 className="mt-3 font-serif text-3xl leading-tight text-white">
                Relationship, work, and pressure patterns
              </h2>
            </div>

            <div className="grid gap-4 lg:grid-cols-3">
              {orientationPanels.map((panel) => (
                <Card
                  key={panel.title}
                  className="rounded-[1.75rem] border border-white/10 bg-[linear-gradient(180deg,rgba(15,23,42,0.94),rgba(2,6,23,0.94))] p-6 text-white shadow-[0_18px_60px_rgba(4,10,24,0.22)]"
                >
                  <h3 className="font-serif text-[1.45rem] leading-tight">{panel.title}</h3>
                  <p className="mt-4 text-sm leading-8 text-slate-300">{panel.body}</p>
                </Card>
              ))}
            </div>
          </section>
        </>
      ) : null}

      <section className="grid gap-4">
        <Card className="rounded-[1.9rem] border border-white/10 bg-slate-950/72 p-6 text-white shadow-[0_18px_60px_rgba(4,10,24,0.22)] sm:p-7">
          <div className="text-[11px] font-semibold uppercase tracking-[0.22em] text-cyan-100">
            How It Works
          </div>
          <h2 className="mt-3 font-serif text-[1.9rem] leading-tight">
            A quieter note on the method
          </h2>
          <p className="mt-3 max-w-3xl text-sm leading-7 text-slate-300">
            The main reading stays focused on interpretation, not mechanics. If you want the
            technical explanation, you can open the notes below.
          </p>

          <details className="mt-5 rounded-[1.35rem] border border-white/8 bg-white/4 px-5 py-4 text-sm text-slate-300">
            <summary className="cursor-pointer list-none font-medium text-slate-100 marker:hidden">
              Open methodology notes
            </summary>
            <div className="mt-4 space-y-3 border-t border-white/6 pt-4 text-sm leading-7 text-slate-400">
              <p>
                Name system: {result?.system.name_method || "Pythagorean numerology"}.
              </p>
              <p>
                Date system:{" "}
                {result?.system.date_method ||
                  "Digit reduction with master numbers 11, 22, and 33 preserved"}
                .
              </p>
              {(result?.notes || [
                "This reading uses the full birth name you enter and reduces date totals while preserving master numbers 11, 22, and 33.",
                "For simplicity, vowels are counted as A, E, I, O, and U, while Y is treated as a consonant in this version.",
              ]).map((item) => (
                <p key={item}>{item}</p>
              ))}
              {result ? (
                <p>
                  The current reading is based on the normalized name{" "}
                  <span className="font-medium text-slate-200">
                    {result.input.normalized_name}
                  </span>{" "}
                  and the birth date{" "}
                  <span className="font-medium text-slate-200">
                    {formatFriendlyDate(result.input.date_of_birth)}
                  </span>
                  .
                </p>
              ) : null}
            </div>
          </details>
        </Card>
      </section>

      <Card className="rounded-[1.9rem] border border-white/10 bg-slate-950/72 p-6 text-white shadow-[0_18px_60px_rgba(4,10,24,0.22)] sm:p-7">
        <h2 className="font-serif text-[1.9rem] leading-tight">Keep exploring</h2>
        <p className="mt-3 max-w-3xl text-sm leading-7 text-slate-300">
          If this reading resonates, you can continue deeper into the rest of Nakshatra AI and
          explore your astrology journey from another angle too.
        </p>

        <div className="mt-5 grid gap-4 md:grid-cols-3">
          <Link
            href="/"
            className="rounded-[1.4rem] border border-white/10 bg-white/4 p-4 transition-colors hover:border-cyan-300/25 hover:bg-white/8"
          >
            <div className="text-base font-semibold">Free Kundli</div>
            <p className="mt-2 text-sm leading-6 text-slate-300">
              Step into the chart-based reading flow when you want a deeper astrological lens.
            </p>
          </Link>
          <Link
            href="/ai-vedic-astrologer"
            className="rounded-[1.4rem] border border-white/10 bg-white/4 p-4 transition-colors hover:border-cyan-300/25 hover:bg-white/8"
          >
            <div className="text-base font-semibold">AI Vedic Astrologer</div>
            <p className="mt-2 text-sm leading-6 text-slate-300">
              Continue with a more conversational, chart-aware reading experience.
            </p>
          </Link>
          <Link
            href="/contact"
            className="rounded-[1.4rem] border border-white/10 bg-white/4 p-4 transition-colors hover:border-cyan-300/25 hover:bg-white/8"
          >
            <div className="text-base font-semibold">Share feedback</div>
            <p className="mt-2 text-sm leading-6 text-slate-300">
              Tell us what felt valuable and what would make the numerology experience even stronger.
            </p>
          </Link>
        </div>
      </Card>
    </StaticPageLayout>
  )
}
