"use client"

import React from "react"

import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { ScrollArea } from "@/components/ui/scroll-area"
import { buildAuthHeaders, useAuth } from "@/lib/auth"
import { ChevronDown, ChevronUp, Crown, Download, Loader2, Lock, X } from "lucide-react"

type ChartViewerProps = {
  backendUrl: string
  open: boolean
  onClose: () => void
  sessionId: string
}

type ChartPlanetDetail = {
  name: string
  short_name: string
  sign: string
  house: number
  degree_in_sign: number | null
  retrograde: boolean
  source_sign?: string | null
  source_house?: number | null
  statuses: string[]
  influence: "supportive" | "mixed" | "challenging"
  hover_summary: string
}

type ChartResponse = {
  chart_code: string
  chart_label: string
  style: string
  svg: string
  ascendant?: {
    sign?: string
    degree_in_sign?: number
  }
  details: ChartPlanetDetail[]
}

type ChartExportPayload = {
  chart_code: string
  chart_label: string
  summary: string
  ascendant?: {
    sign?: string
    degree_in_sign?: number
  }
  details: ChartPlanetDetail[]
  chart: {
    chart: string
    label: string
    source: string
    style: string
    ascendant?: {
      sign?: string
      degree_in_sign?: number
    }
    house_cusps_deg?: Record<string, number>
    planets?: Array<Record<string, unknown>>
    name?: string
    division?: number
    purpose?: string
    house_system?: string
    house_lords?: Record<string, unknown>
    janma_nakshatra?: Record<string, unknown>
  }
}

type ChartExportResponse = {
  name: string
  session_id: string
  style: string
  plan: string
  is_premium: boolean
  generated_at: string
  charts: ChartExportPayload[]
}

type GemstoneRemedy = {
  planet: string
  gemstone: string
  recommendation: string
  why: string
  caution: string
}

type MantraRemedy = {
  planet: string
  mantra: string
  practice: string
  why: string
}

type FastingRemedy = {
  planet: string
  day: string
  practice: string
  why: string
}

type CharityRemedy = {
  planet: string
  recommendation: string
  why: string
}

type RudrakshaRemedy = {
  planet: string
  rudraksha: string
  recommendation: string
  why: string
}

type RemediesResponse = {
  overview: string
  gemstones: GemstoneRemedy[]
  mantras: MantraRemedy[]
  fasting: FastingRemedy[]
  charity: CharityRemedy[]
  rudraksha: RudrakshaRemedy[]
  notes: string[]
}

const CHART_OPTIONS = [
  { code: "D1", label: "Lagna / Rasi" },
  { code: "D9", label: "Navamsha" },
  { code: "D10", label: "Dashamsha" },
]

const STYLE_OPTIONS = [
  { value: "south", label: "South Indian" },
  { value: "north", label: "North Indian" },
]

const CHART_READING_AREAS: Record<string, string> = {
  D1: "identity, life direction, momentum, and visible life circumstances",
  D9: "marriage themes, maturity, inner values, and how the chart deepens over time",
  D10: "career reputation, authority, professional output, and public achievement",
}

const PLANET_OUTCOME_AREAS: Record<string, string> = {
  Sun: "leadership, visibility, authority, and confidence",
  Moon: "public response, emotional steadiness, adaptability, and support",
  Mars: "execution, courage, competition, and decisive action",
  Mercury: "thinking, writing, analysis, trade, planning, and communication",
  Jupiter: "mentorship, growth, credibility, wisdom, and expansion",
  Venus: "relationships, aesthetics, comfort, diplomacy, and attraction",
  Saturn: "discipline, responsibility, endurance, structure, and long-term results",
  Rahu: "ambition, amplification, unconventional moves, and worldly appetite",
  Ketu: "detachment, specialization, karmic residue, and inner sharpness",
}

const HOUSE_OUTCOME_AREAS: Record<number, string> = {
  1: "self-presentation, confidence, health, and the way life starts moving",
  2: "income, speech, family patterns, and what gets built over time",
  3: "effort, communication, self-made skill, courage, and initiative",
  4: "home life, emotional grounding, property matters, and private comfort",
  5: "creativity, intelligence, children, romance, and speculative thinking",
  6: "workload, competition, service, conflict, debt, and recovery",
  7: "partnerships, clients, contracts, visibility, and one-to-one dynamics",
  8: "crises, reinvention, secrecy, inheritance, and psychological pressure",
  9: "belief, luck, teachers, higher learning, travel, and dharma",
  10: "career reputation, authority, status, promotions, and public work",
  11: "gains, salary growth, networks, patrons, audience, and long-term rewards",
  12: "expenses, retreat, isolation, foreign links, sleep, and hidden drains",
}

const SIGN_OUTCOME_FLAVORS: Record<string, string> = {
  Aries: "through bold initiative, speed, and willingness to act first",
  Taurus: "through patience, stability, and tangible value creation",
  Gemini: "through communication, versatility, networking, and fast learning",
  Cancer: "through care, intuition, protection, and emotional intelligence",
  Leo: "through confidence, performance, leadership, and personal presence",
  Virgo: "through precision, systems, craft, and practical intelligence",
  Libra: "through diplomacy, partnerships, aesthetics, and balance",
  Scorpio: "through strategy, intensity, privacy, and deep transformation",
  Sagittarius: "through teaching, faith, exploration, and larger vision",
  Capricorn: "through discipline, structure, ambition, and measurable effort",
  Aquarius: "through unconventional thinking, community, and future-oriented moves",
  Pisces: "through imagination, empathy, surrender, and spiritual sensitivity",
}

const ASTROLOGY_TERM_EXPLANATIONS: Record<string, string> = {
  exalted: "An exalted planet expresses its strength very clearly in that sign, so its positive qualities tend to operate with confidence and support.",
  debilitated: "A debilitated planet is in a sign where its natural style feels weakened or uncomfortable, so its results often need more maturity and conscious handling.",
  retrograde: "A retrograde planet turns its energy inward and makes that area of life more reflective, karmic, delayed, or intense than usual.",
  combust: "A combust planet sits too close to the Sun, so its independent voice can get overshadowed and become harder to express smoothly.",
  vargottama: "A vargottama planet repeats the same sign across key charts, which usually strengthens and stabilizes that planet's core influence.",
  "own sign": "A planet in its own sign works from familiar ground, so it usually expresses its nature more cleanly and reliably.",
  moolatrikona: "Moolatrikona is a special zone of strength where a planet can express its deeper purpose in a steady and effective way.",
}

function cacheKey(chartCode: string, style: string) {
  return `${chartCode}:${style}`
}

function formatDegree(value?: number | null) {
  if (typeof value !== "number" || Number.isNaN(value)) {
    return "Degree unavailable"
  }
  return `${value.toFixed(2)}°`
}

function getChartWidth(style: string) {
  return style === "north" ? "w-full max-w-[470px] xl:max-w-[500px]" : "w-full max-w-[530px] xl:max-w-[560px]"
}

function getStatusClasses(status: string) {
  const normalized = status.toLowerCase()

  if (normalized === "exalted" || normalized === "vargottama") {
    return "border-emerald-400/30 bg-emerald-500/12 text-emerald-200"
  }
  if (normalized === "debilitated" || normalized === "combust") {
    return "border-rose-400/30 bg-rose-500/12 text-rose-200"
  }
  if (normalized === "retrograde") {
    return "border-amber-400/30 bg-amber-500/12 text-amber-100"
  }
  if (normalized === "own sign" || normalized === "moolatrikona") {
    return "border-cyan-400/30 bg-cyan-500/12 text-cyan-100"
  }
  return "border-white/12 bg-white/6 text-slate-200"
}

function getInfluenceClasses(influence: ChartPlanetDetail["influence"]) {
  if (influence === "supportive") {
    return "border-emerald-400/30 bg-emerald-500/12 text-emerald-200"
  }
  if (influence === "challenging") {
    return "border-rose-400/30 bg-rose-500/12 text-rose-200"
  }
  return "border-amber-400/30 bg-amber-500/12 text-amber-100"
}

function getInfluenceLabel(influence: ChartPlanetDetail["influence"]) {
  if (influence === "supportive") return "Good Support"
  if (influence === "challenging") return "Needs Care"
  return "Mixed"
}

function TermHint({ term, className }: { term: string; className: string }) {
  const explanation = ASTROLOGY_TERM_EXPLANATIONS[term.toLowerCase()]

  if (!explanation) {
    return <span className={className}>{term}</span>
  }

  return (
    <span className="group relative inline-flex">
      <span
        tabIndex={0}
        className={`${className} cursor-help outline-none transition-transform duration-150 group-hover:scale-[1.03] group-focus-visible:scale-[1.03] group-focus-visible:ring-2 group-focus-visible:ring-cyan-300/50`}
        aria-label={`${term}: ${explanation}`}
      >
        {term}
      </span>
      <span
        role="tooltip"
        className="pointer-events-none absolute bottom-full left-1/2 z-20 mb-2 w-56 -translate-x-1/2 rounded-2xl border border-cyan-300/20 bg-slate-950/96 px-3 py-2 text-left text-[11px] font-normal leading-4 text-slate-100 opacity-0 shadow-[0_18px_48px_rgba(2,6,23,0.52)] transition-all duration-150 group-hover:-translate-y-1 group-hover:opacity-100 group-focus-within:-translate-y-1 group-focus-within:opacity-100"
      >
        <span className="block text-[10px] font-semibold uppercase tracking-[0.16em] text-cyan-200">{term}</span>
        <span className="mt-1 block">{explanation}</span>
      </span>
    </span>
  )
}

function renderEmptyRemedyState() {
  return (
    <div className="rounded-2xl border border-white/8 bg-slate-950/50 px-3 py-3 text-xs text-slate-500">
      No strong remedy signal is standing out here.
    </div>
  )
}

function insightKey(chartCode: string, planetName: string) {
  return `${chartCode}-${planetName}`
}

function slugifyFilenamePart(value: string) {
  return value
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
}

function escapeHtml(value: string) {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;")
}

function sanitizeChartSvg(svg: string) {
  return svg
    .replace(/<\?xml[\s\S]*?\?>/gi, "")
    .replace(/<!DOCTYPE[\s\S]*?>/gi, "")
    .trim()
}

function downloadBlob(blob: Blob, filename: string) {
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement("a")
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  link.remove()
  window.URL.revokeObjectURL(url)
}

function joinNaturalLanguage(items: string[]) {
  if (items.length === 0) return ""
  if (items.length === 1) return items[0]
  if (items.length === 2) return `${items[0]} and ${items[1]}`
  return `${items.slice(0, -1).join(", ")}, and ${items[items.length - 1]}`
}

function formatHouseOrdinal(house: number) {
  if (house % 10 === 1 && house % 100 !== 11) return `${house}st`
  if (house % 10 === 2 && house % 100 !== 12) return `${house}nd`
  if (house % 10 === 3 && house % 100 !== 13) return `${house}rd`
  return `${house}th`
}

function getStatusOutcomeNote(planet: ChartPlanetDetail) {
  const statusSet = new Set(planet.statuses)
  if (statusSet.has("Exalted")) {
    return "Because it is exalted, this result can come with unusual competence, credibility, and repeatability."
  }
  if (statusSet.has("Own Sign") || statusSet.has("Moolatrikona")) {
    return "Because it is working from its own ground, the planet tends to deliver more steadily and with less internal conflict."
  }
  if (statusSet.has("Debilitated")) {
    return "Because it is debilitated, the promise is still present, but results usually demand correction, humility, or stronger structure first."
  }
  if (statusSet.has("Combust")) {
    return "Because it is combust, the issue may stay active internally before it becomes easy to express outwardly."
  }
  if (planet.retrograde) {
    return "Because it is retrograde, results often arrive through revision, rethinking, delayed timing, or second attempts."
  }
  return ""
}

function buildPlacementOutcome(chart: ChartResponse, planet: ChartPlanetDetail) {
  const chartArea = CHART_READING_AREAS[chart.chart_code] || "important life outcomes"
  const planetArea = PLANET_OUTCOME_AREAS[planet.name] || "major life themes"
  const houseArea = HOUSE_OUTCOME_AREAS[planet.house] || "important life outcomes"
  const signFlavor = SIGN_OUTCOME_FLAVORS[planet.sign] || "through the sign qualities operating here"
  const houseOrdinal = formatHouseOrdinal(planet.house)
  const statusNote = getStatusOutcomeNote(planet)

  if (planet.influence === "supportive") {
    return `${planet.name} in ${planet.sign} in the ${houseOrdinal} house can produce strong results in ${houseArea}. In ${chart.chart_label}, that usually means ${planetArea} starts paying off ${signFlavor}, so the native may see more concrete movement rather than just potential. ${statusNote}`.trim()
  }

  if (planet.influence === "challenging") {
    return `${planet.name} in the ${houseOrdinal} house can make ${houseArea} harder to stabilize. In a chart about ${chartArea}, this often shows up as delays, overcorrection, strain, or outcomes that improve only after discipline and realism increase. ${statusNote}`.trim()
  }

  return `${planet.name} in ${planet.sign} in the ${houseOrdinal} house gives mixed but usable results around ${houseArea}. In ${chart.chart_label}, it can still create meaningful outcomes through ${planetArea}, but timing and consistency matter more than raw intensity. ${statusNote}`.trim()
}

function buildChartOutcomeHighlights(chart: ChartResponse) {
  const supportive = chart.details.filter((planet) => planet.influence === "supportive")
  const challenging = chart.details.filter((planet) => planet.influence === "challenging")
  const mixed = chart.details.filter((planet) => planet.influence === "mixed")
  const strongStatus = chart.details.find((planet) =>
    planet.statuses.some((status) => ["Exalted", "Own Sign", "Moolatrikona", "Debilitated", "Combust"].includes(status))
  )
  const retrograde = chart.details.filter((planet) => planet.retrograde).map((planet) => planet.name)

  const highlights: string[] = []
  highlights.push(
    `${chart.chart_label} is mainly read for ${CHART_READING_AREAS[chart.chart_code] || "its major life outcomes"}, so the placements here are meant to describe lived results rather than abstract symbolism.`
  )

  if (supportive.length > 0) {
    highlights.push(buildPlacementOutcome(chart, supportive[0]))
  }

  if (challenging.length > 0) {
    highlights.push(buildPlacementOutcome(chart, challenging[0]))
  } else if (mixed.length > 0) {
    highlights.push(buildPlacementOutcome(chart, mixed[0]))
  }

  if (strongStatus) {
    highlights.push(
      `${strongStatus.name} is one of the defining technical anchors in this chart. In practical terms, that means its outcomes can show up more loudly in real life than a weaker placement would. ${getStatusOutcomeNote(strongStatus)}`.trim()
    )
  }

  if (retrograde.length > 0) {
    highlights.push(
      `Retrograde emphasis from ${joinNaturalLanguage(retrograde.slice(0, 3))} suggests that some results here unfold non-linearly: through revisiting decisions, repeating lessons, or succeeding on the second pass rather than the first.`
    )
  }

  return highlights.slice(0, 3)
}

function getChartPlacementBadges(chart: ChartResponse) {
  return chart.details
    .slice(0, 4)
    .map((planet) => `${planet.name} • ${planet.sign} • H${planet.house}`)
}

function buildVisualChartsPrintDocument(params: {
  name: string
  styleLabel: string
  charts: ChartResponse[]
}) {
  const { name, styleLabel, charts } = params
  const chartPages = charts
    .map((chart) => {
      const ascLine = `Ascendant: ${chart.ascendant?.sign || "Unknown"} ${formatDegree(chart.ascendant?.degree_in_sign)}`
      const sanitizedSvg = sanitizeChartSvg(chart.svg)
      const outcomeHighlights = buildChartOutcomeHighlights(chart)
      const placementBadges = getChartPlacementBadges(chart)
      return `
        <section class="chart-page">
          <div class="chart-header">
            <div class="eyebrow">${escapeHtml(chart.chart_code)}</div>
            <h2>${escapeHtml(chart.chart_label)}</h2>
            <p>${escapeHtml(ascLine)}</p>
          </div>
          <div class="chart-layout">
            <div class="chart-frame chart-frame--${escapeHtml(chart.style)}">
              ${sanitizedSvg}
            </div>
            <aside class="chart-notes">
              <div class="notes-section">
                <div class="notes-label">Snapshot</div>
                <p>${escapeHtml(`This ${chart.chart_label} view is shown in ${styleLabel.toLowerCase()} format, matching the style selected inside Nakshatra AI. The notes below focus on practical outcomes and pressure points.`)}</p>
              </div>
              <div class="notes-section">
                <div class="notes-label">Likely Outcomes</div>
                <ul class="notes-list">
                  ${outcomeHighlights.map((fact) => `<li>${escapeHtml(fact)}</li>`).join("")}
                </ul>
              </div>
              <div class="notes-section">
                <div class="notes-label">Key Placements</div>
                <div class="badge-grid">
                  ${placementBadges.map((badge) => `<span class="placement-badge">${escapeHtml(badge)}</span>`).join("")}
                </div>
              </div>
            </aside>
          </div>
        </section>
      `
    })
    .join("")

  return `
    <!doctype html>
    <html lang="en">
      <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>${escapeHtml(name)} Charts</title>
        <style>
          @page {
            size: A4 landscape;
            margin: 10mm;
          }
          * {
            box-sizing: border-box;
            -webkit-print-color-adjust: exact;
            print-color-adjust: exact;
          }
          html, body {
            margin: 0;
            padding: 0;
            background: #f8fafc;
            color: #0f172a;
            font-family: "Georgia", "Times New Roman", serif;
          }
          body {
            padding: 0;
          }
          .cover,
          .chart-page {
            break-after: page;
            page-break-after: always;
          }
          .cover {
            min-height: calc(100vh - 20mm);
            display: flex;
            flex-direction: column;
            justify-content: center;
            gap: 14px;
            padding: 4mm 2mm;
          }
          .cover-mark {
            font-size: 12px;
            letter-spacing: 0.32em;
            text-transform: uppercase;
            color: #0369a1;
          }
          .cover h1 {
            margin: 0;
            font-size: 30px;
            line-height: 1.15;
            font-weight: 700;
          }
          .cover p {
            margin: 0;
            font-size: 14px;
            line-height: 1.6;
            color: #334155;
            max-width: 760px;
          }
          .chart-page {
            display: flex;
            flex-direction: column;
            gap: 8px;
            padding: 0;
            break-inside: avoid;
            page-break-inside: avoid;
            height: 185mm;
            overflow: hidden;
          }
          .chart-header {
            display: flex;
            flex-direction: column;
            gap: 3px;
          }
          .eyebrow {
            font-size: 11px;
            letter-spacing: 0.24em;
            text-transform: uppercase;
            color: #0369a1;
          }
          .chart-header h2 {
            margin: 0;
            font-size: 24px;
            line-height: 1.2;
            font-weight: 700;
          }
          .chart-header p {
            margin: 0;
            font-size: 12px;
            line-height: 1.4;
            color: #475569;
          }
          .chart-layout {
            display: grid;
            grid-template-columns: minmax(0, 1.05fr) minmax(260px, 0.95fr);
            gap: 10px;
            align-items: stretch;
            flex: 1;
            min-height: 0;
          }
          .chart-frame {
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 18px;
            border: 1px solid #cbd5e1;
            background: linear-gradient(180deg, #081120 0%, #020617 100%);
            padding: 10px;
            min-height: 0;
            height: 100%;
            overflow: hidden;
          }
          .chart-notes {
            display: flex;
            flex-direction: column;
            gap: 8px;
            min-height: 0;
            overflow: hidden;
          }
          .notes-section {
            border: 1px solid #dbe5f0;
            border-radius: 16px;
            background: #ffffff;
            padding: 11px 12px;
          }
          .notes-label {
            margin-bottom: 6px;
            font-size: 10px;
            font-weight: 700;
            letter-spacing: 0.22em;
            text-transform: uppercase;
            color: #0369a1;
          }
          .notes-section p {
            margin: 0;
            font-size: 11px;
            line-height: 1.5;
            color: #334155;
          }
          .notes-list {
            margin: 0;
            padding-left: 16px;
          }
          .notes-list li {
            margin: 0 0 5px;
            font-size: 11px;
            line-height: 1.45;
            color: #334155;
          }
          .notes-list li:last-child {
            margin-bottom: 0;
          }
          .badge-grid {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
          }
          .placement-badge {
            display: inline-flex;
            align-items: center;
            border-radius: 999px;
            background: #eaf5ff;
            border: 1px solid #bfdbfe;
            color: #0f3b63;
            padding: 5px 9px;
            font-size: 10px;
            line-height: 1.3;
          }
          .chart-frame--north svg {
            width: 100%;
            max-width: 300px;
            height: auto;
            display: block;
          }
          .chart-frame--south svg {
            width: 100%;
            max-width: 360px;
            height: auto;
            display: block;
          }
          svg {
            overflow: visible;
          }
          @media print {
            .chart-page:last-child {
              break-after: auto;
              page-break-after: auto;
            }
          }
        </style>
        <script>
          window.addEventListener("load", () => {
            window.setTimeout(() => {
              window.focus();
              window.print();
            }, 350);
          });
        </script>
      </head>
      <body>
        <section class="cover">
          <div class="cover-mark">Nakshatra AI</div>
          <h1>${escapeHtml(name)} Visual Charts</h1>
          <p>${escapeHtml(`This export contains the ${styleLabel} chart views currently selected in the charts panel.`)}</p>
          <p>${escapeHtml(`Included charts: ${charts.map((chart) => chart.chart_label).join(", ")}.`)}</p>
        </section>
        ${chartPages}
      </body>
    </html>
  `
}

export default function ChartViewer({
  backendUrl,
  open,
  onClose,
  sessionId,
}: ChartViewerProps) {
  const { token, user } = useAuth()
  const [style, setStyle] = React.useState("north")
  const [cache, setCache] = React.useState<Record<string, ChartResponse>>({})
  const [loading, setLoading] = React.useState(false)
  const [error, setError] = React.useState("")
  const [remedies, setRemedies] = React.useState<RemediesResponse | null>(null)
  const [remediesLoading, setRemediesLoading] = React.useState(false)
  const [remediesError, setRemediesError] = React.useState("")
  const [downloadingVisualPdf, setDownloadingVisualPdf] = React.useState(false)
  const [downloadingJson, setDownloadingJson] = React.useState(false)
  const [exportError, setExportError] = React.useState("")
  const [expandedInsights, setExpandedInsights] = React.useState<Record<string, boolean>>({})
  const planetRowRefs = React.useRef<Record<string, HTMLDivElement | null>>({})
  const canSeeDivisional = Boolean(user?.plan_access.features.divisional_charts)
  const canSeeRemedies = Boolean(user?.plan_access.features.remedies)
  const visibleOptions = React.useMemo(
    () => (canSeeDivisional ? CHART_OPTIONS : CHART_OPTIONS.filter((option) => option.code === "D1")),
    [canSeeDivisional]
  )
  const visibleCharts = React.useMemo(
    () =>
      visibleOptions
        .map((option) => cache[cacheKey(option.code, style)])
        .filter((chart): chart is ChartResponse => Boolean(chart)),
    [cache, style, visibleOptions]
  )
  const styleLabel = STYLE_OPTIONS.find((option) => option.value === style)?.label || style
  const isExportReady = visibleCharts.length > 0 && visibleCharts.length === visibleOptions.length && !loading

  function toggleInsight(key: string) {
    setExpandedInsights((prev) => ({
      ...prev,
      [key]: !prev[key],
    }))
  }

  const openInsightAndScroll = React.useCallback((chartCode: string, planetName: string) => {
    const key = insightKey(chartCode, planetName)
    setExpandedInsights((prev) => ({
      ...prev,
      [key]: true,
    }))

    window.setTimeout(() => {
      planetRowRefs.current[key]?.scrollIntoView({
        behavior: "smooth",
        block: "center",
        inline: "nearest",
      })
    }, 180)
  }, [])

  const handleChartPlanetClick = React.useCallback(
    (chartCode: string, event: React.MouseEvent<HTMLDivElement>) => {
      const target = event.target as Element | null
      const node = target?.closest?.("[data-planet]")
      const planetName = node?.getAttribute("data-planet")
      if (!planetName) return
      openInsightAndScroll(chartCode, planetName)
    },
    [openInsightAndScroll]
  )

  const handleDownloadVisualPdf = React.useCallback(async () => {
    if (!isExportReady || visibleCharts.length === 0) {
      setExportError("Please wait for the charts to finish loading before exporting.")
      return
    }

    setDownloadingVisualPdf(true)
    setExportError("")

    try {
      const printDocument = buildVisualChartsPrintDocument({
        name: user?.name || "Nakshatra User",
        styleLabel,
        charts: visibleCharts,
      })
      const printBlob = new Blob([printDocument], { type: "text/html;charset=utf-8" })
      const printUrl = window.URL.createObjectURL(printBlob)
      const printWindow = window.open(printUrl, "_blank", "width=1200,height=900")
      if (!printWindow) {
        throw new Error("Please allow pop-ups so the chart PDF can open in a print window.")
      }
      window.setTimeout(() => {
        window.URL.revokeObjectURL(printUrl)
      }, 60_000)
    } catch (err) {
      setExportError(err instanceof Error ? err.message : "Failed to prepare the chart PDF.")
    } finally {
      setDownloadingVisualPdf(false)
    }
  }, [isExportReady, styleLabel, user?.name, visibleCharts])

  const handleDownloadChartData = React.useCallback(async () => {
    if (!token || !sessionId) return

    setDownloadingJson(true)
    setExportError("")

    try {
      const res = await fetch(
        `${backendUrl}/charts/export-data?style=${encodeURIComponent(style)}`,
        {
          headers: buildAuthHeaders(token, {
            "X-Session-Id": sessionId,
          }),
        }
      )

      if (!res.ok) {
        let message = "Failed to download chart data."
        try {
          const data = await res.json()
          message = data?.detail || data?.error || message
        } catch {
          // ignore JSON parse failure and keep default message
        }
        throw new Error(message)
      }

      const data: ChartExportResponse = await res.json()
      const fileRoot = slugifyFilenamePart(data.name || sessionId) || "kundli-charts"
      const blob = new Blob([JSON.stringify(data, null, 2)], {
        type: "application/json;charset=utf-8",
      })
      downloadBlob(blob, `${fileRoot}-${style}-chart-data.json`)
    } catch (err) {
      setExportError(err instanceof Error ? err.message : "Failed to download chart data.")
    } finally {
      setDownloadingJson(false)
    }
  }, [backendUrl, sessionId, style, token])

  React.useEffect(() => {
    setRemedies(null)
    setRemediesError("")
  }, [sessionId])

  React.useEffect(() => {
    setExportError("")
  }, [sessionId, style])

  React.useEffect(() => {
    if (!open || !sessionId || remedies || !token || !canSeeRemedies) return

    let isCancelled = false

    async function loadRemedies() {
      setRemediesLoading(true)
      setRemediesError("")
      try {
        const res = await fetch(`${backendUrl}/remedies`, {
          headers: buildAuthHeaders(token, {
            "X-Session-Id": sessionId,
          }),
        })

        if (!res.ok) {
          let message = "Failed to load remedies."
          try {
            const data = await res.json()
            message = data?.detail || data?.error || message
          } catch {
            // ignore JSON parse failure and keep default message
          }
          throw new Error(message)
        }

        const data: RemediesResponse = await res.json()
        if (!isCancelled) {
          setRemedies(data)
        }
      } catch (err) {
        if (!isCancelled) {
          setRemediesError(err instanceof Error ? err.message : "Failed to load remedies.")
        }
      } finally {
        if (!isCancelled) {
          setRemediesLoading(false)
        }
      }
    }

    loadRemedies()
    return () => {
      isCancelled = true
    }
  }, [backendUrl, canSeeRemedies, open, remedies, sessionId, token])

  React.useEffect(() => {
    if (!open || !sessionId || !token) return

    let isCancelled = false
    const missingOptions = visibleOptions.filter((option) => !cache[cacheKey(option.code, style)])

    if (missingOptions.length === 0) return

    async function loadCharts() {
      setLoading(true)
      setError("")
      try {
        const chartEntries = await Promise.all(
          missingOptions.map(async (option) => {
            const res = await fetch(
              `${backendUrl}/charts?code=${encodeURIComponent(option.code)}&style=${encodeURIComponent(style)}`,
              {
                headers: buildAuthHeaders(token, {
                  "X-Session-Id": sessionId,
                }),
              }
            )

            if (!res.ok) {
              let message = "Failed to load chart."
              try {
                const data = await res.json()
                message = data?.detail || data?.error || message
              } catch {
                // ignore JSON parse failure and keep default message
              }
              throw new Error(message)
            }

            const data: ChartResponse = await res.json()
            return [cacheKey(option.code, style), data] as const
          })
        )

        if (!isCancelled) {
          setCache((prev) => ({
            ...prev,
            ...Object.fromEntries(chartEntries),
          }))
        }
      } catch (err) {
        if (!isCancelled) {
          setError(err instanceof Error ? err.message : "Failed to load charts.")
        }
      } finally {
        if (!isCancelled) {
          setLoading(false)
        }
      }
    }

    loadCharts()
    return () => {
      isCancelled = true
    }
  }, [backendUrl, cache, open, sessionId, style, token, visibleOptions])

  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/82 p-1 backdrop-blur-sm">
      <Card className="flex h-[min(94vh,940px)] w-[min(98vw,1740px)] flex-col overflow-hidden border border-blue-500/20 bg-slate-950/95 text-white shadow-2xl">
        <div className="flex flex-wrap items-start justify-between gap-3 border-b border-white/10 px-5 py-3">
          <div>
            <h2 className="text-xl font-semibold text-white">Kundli Charts</h2>
            <p className="text-sm text-slate-400">
              Lagna, Navamsha, and Dashamsha stay visible together. Switch only the chart style.
            </p>
          </div>
          <div className="ml-auto flex flex-wrap items-center gap-2">
            {STYLE_OPTIONS.map((option) => (
              <Button
                key={option.value}
                type="button"
                variant={style === option.value ? "default" : "outline"}
                onClick={() => setStyle(option.value)}
                className={
                  style === option.value
                    ? "bg-cyan-700 text-white hover:bg-cyan-600"
                    : "border-white/15 bg-slate-900/80 text-slate-200 hover:bg-slate-800"
                }
              >
                {option.label}
              </Button>
            ))}
            <Button
              type="button"
              variant="outline"
              onClick={handleDownloadVisualPdf}
              disabled={downloadingVisualPdf || !isExportReady}
              className="border-cyan-400/25 bg-cyan-500/10 text-cyan-100 hover:bg-cyan-500/20"
            >
              {downloadingVisualPdf ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Download className="h-4 w-4" />
              )}
              <span className="ml-2">Download Visual Charts (PDF)</span>
            </Button>
            <Button
              type="button"
              variant="outline"
              onClick={handleDownloadChartData}
              disabled={downloadingJson || !token}
              className="border-white/15 bg-slate-900/80 text-slate-200 hover:bg-slate-800"
            >
              {downloadingJson ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Download className="h-4 w-4" />
              )}
              <span className="ml-2">Download Chart Data (JSON)</span>
            </Button>
            <Button
              type="button"
              variant="ghost"
              onClick={onClose}
              className="text-slate-300 hover:bg-white/10 hover:text-white"
            >
              <X className="h-4 w-4" />
              <span className="ml-2">Close</span>
            </Button>
          </div>
        </div>

        <div className="flex-1 overflow-hidden">
          <ScrollArea className="h-full">
            <div className="w-full px-3 py-4 sm:px-4 lg:px-5">
            {loading && visibleCharts.length === 0 ? (
              <div className="flex min-h-[440px] items-center justify-center text-slate-300">
                <Loader2 className="mr-3 h-5 w-5 animate-spin" />
                Rendering charts...
              </div>
            ) : error && visibleCharts.length === 0 ? (
              <div className="flex min-h-[440px] items-center justify-center text-center text-sm text-rose-300">
                {error}
              </div>
            ) : (
              <>
                <div className="mb-4 flex items-center justify-between gap-3 text-xs text-slate-400">
                  <span>Open any planet to see a deeper insight tailored to your own chart.</span>
                  <span>{STYLE_OPTIONS.find((option) => option.value === style)?.label}</span>
                </div>
                {!canSeeDivisional ? (
                  <div className="mb-4 rounded-3xl border border-amber-400/20 bg-amber-500/10 p-4 text-sm text-amber-100">
                    <div className="flex items-start gap-3">
                      <Crown className="mt-0.5 h-5 w-5 shrink-0 text-amber-200" />
                      <div>
                        <div className="font-semibold text-white">Premium unlocks D9 and D10</div>
                        <p className="mt-1 text-amber-100/90">
                          Free accounts can export the Lagna chart as a visual PDF or JSON. Premium adds Navamsha, Dashamsha, remedies, and the full multi-chart export set.
                        </p>
                      </div>
                    </div>
                  </div>
                ) : null}
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                  {visibleCharts.map((chart) => (
                    <section
                      key={cacheKey(chart.chart_code, chart.style)}
                      className="rounded-3xl border border-blue-400/15 bg-[radial-gradient(circle_at_top,_rgba(56,189,248,0.12),_rgba(15,23,42,0.96)_58%)] p-3 shadow-[inset_0_1px_0_rgba(255,255,255,0.04)]"
                    >
                      <div className="mb-3 flex items-start justify-between gap-3">
                        <div>
                          <h3 className="text-lg font-semibold text-white">{chart.chart_label}</h3>
                          <p className="text-xs text-slate-400">
                            Ascendant: {chart.ascendant?.sign || "Unknown"} {formatDegree(chart.ascendant?.degree_in_sign)}
                          </p>
                        </div>
                        <span className="rounded-full border border-white/10 bg-white/6 px-2.5 py-1 text-[11px] text-slate-300">
                          {chart.chart_code}
                        </span>
                      </div>

                      <div className="rounded-[1.75rem] border border-white/8 bg-slate-950/72 p-2.5 shadow-[inset_0_1px_0_rgba(255,255,255,0.03)]">
                        <div className="rounded-2xl border border-white/6 bg-[linear-gradient(180deg,rgba(15,23,42,0.92),rgba(2,6,23,0.96))] p-3">
                          <div className={`mx-auto ${getChartWidth(chart.style)}`}>
                            <div
                              className="mx-auto w-full [&_svg]:h-auto [&_svg]:w-full [&_svg]:overflow-visible"
                              onClick={(event) => handleChartPlanetClick(chart.chart_code, event)}
                              dangerouslySetInnerHTML={{ __html: chart.svg }}
                            />
                          </div>
                        </div>
                      </div>

                      <div className="mt-3">
                        <div className="mb-2 text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-400">
                          Detailed Placements
                        </div>
                        <div className="grid gap-2">
                          {chart.details.map((planet) => (
                            <div
                              key={insightKey(chart.chart_code, planet.name)}
                              ref={(node) => {
                                planetRowRefs.current[insightKey(chart.chart_code, planet.name)] = node
                              }}
                              className="rounded-2xl border border-white/8 bg-slate-950/62 px-3 py-2.5 transition-colors hover:border-cyan-400/25"
                            >
                              <div className="flex items-start justify-between gap-3">
                                <div>
                                  <div className="flex items-center gap-2">
                                    <div className="text-sm font-medium text-white">{planet.name}</div>
                                    <span
                                      className={`rounded-full border px-2 py-0.5 text-[10px] font-medium ${getInfluenceClasses(planet.influence)}`}
                                    >
                                      {getInfluenceLabel(planet.influence)}
                                    </span>
                                  </div>
                                  <div className="text-xs text-slate-400">
                                    {planet.sign} • House {planet.house}
                                  </div>
                                </div>
                                <div className="text-right">
                                  <div className="text-sm font-medium text-slate-100">
                                    {formatDegree(planet.degree_in_sign)}
                                  </div>
                                  {planet.source_sign && planet.source_house ? (
                                    <div className="text-[11px] text-slate-500">
                                      From {planet.source_sign} • {planet.source_house}H
                                    </div>
                                  ) : null}
                                </div>
                              </div>
                              <div className="mt-2 flex items-center justify-between gap-3">
                                <div className="text-[11px] text-slate-500">
                                  Open insight for a quick interpretation
                                </div>
                                <Button
                                  type="button"
                                  variant="outline"
                                  onClick={() => toggleInsight(insightKey(chart.chart_code, planet.name))}
                                  className="h-7 border-white/15 bg-slate-900/80 px-2.5 text-[11px] text-slate-200 hover:bg-slate-800"
                                >
                                  {expandedInsights[insightKey(chart.chart_code, planet.name)] ? "Hide Insight" : "Get Insight"}
                                  {expandedInsights[insightKey(chart.chart_code, planet.name)] ? (
                                    <ChevronUp className="ml-1.5 h-3.5 w-3.5" />
                                  ) : (
                                    <ChevronDown className="ml-1.5 h-3.5 w-3.5" />
                                  )}
                                </Button>
                              </div>
                              {planet.statuses.length > 0 ? (
                                <div className="mt-2 flex flex-wrap gap-1.5">
                                  {planet.statuses.map((status) => (
                                    <TermHint
                                      key={`${planet.name}-${status}`}
                                      term={status}
                                      className={`rounded-full border px-2 py-0.5 text-[11px] font-medium ${getStatusClasses(status)}`}
                                    />
                                  ))}
                                </div>
                              ) : (
                                <div className="mt-2 text-[11px] text-slate-500">
                                  No special dignity or motion flag.
                                </div>
                              )}
                              <div
                                className={`grid transition-all duration-300 ease-out ${
                                  expandedInsights[insightKey(chart.chart_code, planet.name)]
                                    ? "mt-3 grid-rows-[1fr] opacity-100"
                                    : "grid-rows-[0fr] opacity-0"
                                }`}
                              >
                                <div className="overflow-hidden">
                                  <div className="rounded-2xl border border-cyan-400/20 bg-slate-950/96 p-3">
                                    <div className="mb-1 flex items-center justify-between gap-3">
                                      <div className="text-sm font-semibold text-white">{planet.name}</div>
                                      <span
                                        className={`rounded-full border px-2 py-0.5 text-[10px] font-medium ${getInfluenceClasses(planet.influence)}`}
                                      >
                                        {getInfluenceLabel(planet.influence)}
                                      </span>
                                    </div>
                                    <p className="text-xs leading-5 text-slate-200">{planet.hover_summary}</p>
                                  </div>
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    </section>
                  ))}
                  {!canSeeDivisional ? (
                    <>
                      {["Navamsha (D9)", "Dashamsha (D10)"].map((label) => (
                        <section
                          key={label}
                          className="rounded-3xl border border-dashed border-white/12 bg-slate-950/55 p-5 text-slate-300"
                        >
                          <div className="mb-3 flex items-center gap-2 text-white">
                            <Lock className="h-4 w-4 text-amber-300" />
                            <h3 className="text-lg font-semibold">{label}</h3>
                          </div>
                          <p className="text-sm leading-6 text-slate-400">
                            Premium adds this chart, its detailed placements, and its chart-specific interpretation.
                          </p>
                        </section>
                      ))}
                    </>
                  ) : null}
                </div>
                <section className="mt-6 rounded-3xl border border-emerald-400/15 bg-[radial-gradient(circle_at_top,_rgba(16,185,129,0.12),_rgba(15,23,42,0.96)_60%)] p-4 shadow-[inset_0_1px_0_rgba(255,255,255,0.04)]">
                  <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <h3 className="text-lg font-semibold text-white">Personalized Remedies</h3>
                      <p className="text-sm text-slate-400">
                        Rule-based remedies derived from weak supportive planets and afflicted natal placements.
                      </p>
                    </div>
                    {!canSeeRemedies ? (
                      <span className="inline-flex items-center rounded-full bg-amber-500/15 px-2.5 py-1 text-[11px] font-semibold uppercase tracking-[0.16em] text-amber-200">
                        <Lock className="mr-1 h-3.5 w-3.5" />
                        Premium
                      </span>
                    ) : null}
                  </div>

                  {!canSeeRemedies ? (
                    <div className="rounded-2xl border border-dashed border-white/12 bg-slate-950/55 p-4 text-sm leading-6 text-slate-300">
                      Upgrade to Premium to unlock personalized remedies, daily transit predictions, and full D1, D9, and D10 visual and data exports.
                    </div>
                  ) : remediesLoading && !remedies ? (
                    <div className="flex min-h-[180px] items-center justify-center text-slate-300">
                      <Loader2 className="mr-3 h-5 w-5 animate-spin" />
                      Preparing remedies...
                    </div>
                  ) : remediesError && !remedies ? (
                    <div className="rounded-2xl border border-rose-400/20 bg-rose-500/8 px-4 py-3 text-sm text-rose-200">
                      {remediesError}
                    </div>
                  ) : remedies ? (
                    <>
                      <p className="mb-4 max-w-4xl text-sm leading-6 text-slate-300">{remedies.overview}</p>
                      <div className="grid gap-4 xl:grid-cols-2">
                        <div className="rounded-2xl border border-white/8 bg-slate-950/58 p-4">
                          <div className="mb-3 text-sm font-semibold text-white">Gemstones</div>
                          <div className="grid gap-3">
                            {remedies.gemstones.length ? remedies.gemstones.map((item) => (
                              <div key={`gem-${item.planet}`} className="rounded-2xl border border-white/8 bg-white/[0.03] p-3">
                                <div className="text-sm font-medium text-white">{item.gemstone} for {item.planet}</div>
                                <div className="mt-1 text-xs leading-5 text-slate-300">{item.why}</div>
                                <div className="mt-2 text-xs text-cyan-200">{item.recommendation}</div>
                                <div className="mt-2 text-[11px] text-amber-200">{item.caution}</div>
                              </div>
                            )) : renderEmptyRemedyState()}
                          </div>
                        </div>

                        <div className="rounded-2xl border border-white/8 bg-slate-950/58 p-4">
                          <div className="mb-3 text-sm font-semibold text-white">Mantras</div>
                          <div className="grid gap-3">
                            {remedies.mantras.length ? remedies.mantras.map((item) => (
                              <div key={`mantra-${item.planet}`} className="rounded-2xl border border-white/8 bg-white/[0.03] p-3">
                                <div className="text-sm font-medium text-white">{item.planet}</div>
                                <div className="mt-1 text-xs font-medium text-cyan-200">{item.mantra}</div>
                                <div className="mt-2 text-xs leading-5 text-slate-300">{item.why}</div>
                                <div className="mt-2 text-[11px] text-slate-400">{item.practice}</div>
                              </div>
                            )) : renderEmptyRemedyState()}
                          </div>
                        </div>

                        <div className="rounded-2xl border border-white/8 bg-slate-950/58 p-4">
                          <div className="mb-3 text-sm font-semibold text-white">Fasting Days</div>
                          <div className="grid gap-3">
                            {remedies.fasting.length ? remedies.fasting.map((item) => (
                              <div key={`fast-${item.planet}`} className="rounded-2xl border border-white/8 bg-white/[0.03] p-3">
                                <div className="text-sm font-medium text-white">{item.day} for {item.planet}</div>
                                <div className="mt-1 text-xs leading-5 text-slate-300">{item.why}</div>
                                <div className="mt-2 text-[11px] text-slate-400">{item.practice}</div>
                              </div>
                            )) : renderEmptyRemedyState()}
                          </div>
                        </div>

                        <div className="rounded-2xl border border-white/8 bg-slate-950/58 p-4">
                          <div className="mb-3 text-sm font-semibold text-white">Charity</div>
                          <div className="grid gap-3">
                            {remedies.charity.length ? remedies.charity.map((item) => (
                              <div key={`charity-${item.planet}`} className="rounded-2xl border border-white/8 bg-white/[0.03] p-3">
                                <div className="text-sm font-medium text-white">{item.planet}</div>
                                <div className="mt-1 text-xs leading-5 text-slate-300">{item.why}</div>
                                <div className="mt-2 text-[11px] text-slate-400">{item.recommendation}</div>
                              </div>
                            )) : renderEmptyRemedyState()}
                          </div>
                        </div>

                        <div className="rounded-2xl border border-white/8 bg-slate-950/58 p-4 xl:col-span-2">
                          <div className="mb-3 text-sm font-semibold text-white">Rudraksha</div>
                          <div className="grid gap-3 md:grid-cols-2">
                            {remedies.rudraksha.length ? remedies.rudraksha.map((item) => (
                              <div key={`rudraksha-${item.planet}`} className="rounded-2xl border border-white/8 bg-white/[0.03] p-3">
                                <div className="text-sm font-medium text-white">{item.rudraksha} for {item.planet}</div>
                                <div className="mt-1 text-xs leading-5 text-slate-300">{item.why}</div>
                                <div className="mt-2 text-[11px] text-slate-400">{item.recommendation}</div>
                              </div>
                            )) : renderEmptyRemedyState()}
                          </div>
                        </div>
                      </div>

                      {remedies.notes.length ? (
                        <div className="mt-4 grid gap-2">
                          {remedies.notes.map((note, index) => (
                            <div
                              key={`remedy-note-${index}`}
                              className="rounded-2xl border border-white/8 bg-slate-950/50 px-4 py-3 text-xs leading-5 text-slate-300"
                            >
                              {note}
                            </div>
                          ))}
                        </div>
                      ) : null}
                    </>
                  ) : null}
                </section>
                {loading ? (
                  <div className="mt-4 flex items-center justify-center text-xs text-slate-400">
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Updating charts...
                  </div>
                ) : null}
                {exportError ? (
                  <div className="mt-4 text-center text-xs text-rose-300">{exportError}</div>
                ) : null}
                {error && visibleCharts.length > 0 ? (
                  <div className="mt-4 text-center text-xs text-rose-300">{error}</div>
                ) : null}
              </>
            )}
            </div>
          </ScrollArea>
        </div>
      </Card>
    </div>
  )
}
