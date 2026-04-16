"use client"

import React from "react"

import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { ScrollArea } from "@/components/ui/scroll-area"
import { ChevronDown, ChevronUp, Loader2, X } from "lucide-react"

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

export default function ChartViewer({
  backendUrl,
  open,
  onClose,
  sessionId,
}: ChartViewerProps) {
  const [style, setStyle] = React.useState("north")
  const [cache, setCache] = React.useState<Record<string, ChartResponse>>({})
  const [loading, setLoading] = React.useState(false)
  const [error, setError] = React.useState("")
  const [remedies, setRemedies] = React.useState<RemediesResponse | null>(null)
  const [remediesLoading, setRemediesLoading] = React.useState(false)
  const [remediesError, setRemediesError] = React.useState("")
  const [expandedInsights, setExpandedInsights] = React.useState<Record<string, boolean>>({})
  const planetRowRefs = React.useRef<Record<string, HTMLDivElement | null>>({})
  const visibleCharts = CHART_OPTIONS.map((option) => cache[cacheKey(option.code, style)]).filter(
    (chart): chart is ChartResponse => Boolean(chart)
  )

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

  React.useEffect(() => {
    setRemedies(null)
    setRemediesError("")
  }, [sessionId])

  React.useEffect(() => {
    if (!open || !sessionId || remedies) return

    let isCancelled = false

    async function loadRemedies() {
      setRemediesLoading(true)
      setRemediesError("")
      try {
        const res = await fetch(`${backendUrl}/remedies`, {
          headers: {
            "X-Session-Id": sessionId,
          },
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
  }, [backendUrl, open, remedies, sessionId])

  React.useEffect(() => {
    if (!open || !sessionId) return

    let isCancelled = false
    const missingOptions = CHART_OPTIONS.filter((option) => !cache[cacheKey(option.code, style)])

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
                headers: {
                  "X-Session-Id": sessionId,
                },
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
  }, [backendUrl, cache, open, sessionId, style])

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
                                    <span
                                      key={`${planet.name}-${status}`}
                                      className={`rounded-full border px-2 py-0.5 text-[11px] font-medium ${getStatusClasses(status)}`}
                                    >
                                      {status}
                                    </span>
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
                </div>
                <section className="mt-6 rounded-3xl border border-emerald-400/15 bg-[radial-gradient(circle_at_top,_rgba(16,185,129,0.12),_rgba(15,23,42,0.96)_60%)] p-4 shadow-[inset_0_1px_0_rgba(255,255,255,0.04)]">
                  <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <h3 className="text-lg font-semibold text-white">Personalized Remedies</h3>
                      <p className="text-sm text-slate-400">
                        Rule-based remedies derived from weak supportive planets and afflicted natal placements.
                      </p>
                    </div>
                  </div>

                  {remediesLoading && !remedies ? (
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
