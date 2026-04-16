"use client"

import React from "react"

import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { ScrollArea } from "@/components/ui/scroll-area"
import PlacesAutoComplete from "@/components/ui/placesAutoComplete"
import { HeartHandshake, Loader2, Sparkles, X } from "lucide-react"

type CompatibilityViewerProps = {
  backendUrl: string
  open: boolean
  onClose: () => void
  sessionId: string
}

type CompatibilityBreakdownItem = {
  key: string
  title: string
  score: number
  out_of: number
  meaning: string
  bride_value: string
  groom_value: string
  interpretation: string
  ratio: number
}

type CompatibilityResponse = {
  native_name: string
  partner_name: string
  native_role: "bride" | "groom"
  partner_role: "bride" | "groom"
  total_score: number
  out_of: number
  verdict: string
  score_summary: string
  compatibility_summary: string
  breakdown: CompatibilityBreakdownItem[]
  strengths: string[]
  challenges: string[]
  best_part_about_marriage: string
  traditional_note: string
}

function getBreakdownClasses(ratio: number) {
  if (ratio >= 0.75) {
    return "border-emerald-400/20 bg-emerald-500/8"
  }
  if (ratio <= 0.34) {
    return "border-rose-400/20 bg-rose-500/8"
  }
  return "border-amber-400/20 bg-amber-500/8"
}

export default function CompatibilityViewer({
  backendUrl,
  open,
  onClose,
  sessionId,
}: CompatibilityViewerProps) {
  const [role, setRole] = React.useState<"" | "bride" | "groom">("")
  const [partnerData, setPartnerData] = React.useState({
    fullName: "",
    year: "",
    month: "",
    date: "",
    hours: "",
    minutes: "",
    latitude: "",
    longitude: "",
  })
  const [placeSelected, setPlaceSelected] = React.useState(false)
  const [placeError, setPlaceError] = React.useState(false)
  const [loading, setLoading] = React.useState(false)
  const [error, setError] = React.useState("")
  const [result, setResult] = React.useState<CompatibilityResponse | null>(null)

  React.useEffect(() => {
    if (!open) return
    setError("")
  }, [open])

  function handlePlaceSelect(lat: number, lon: number) {
    setPlaceSelected(true)
    setPlaceError(false)
    setPartnerData((prev) => ({
      ...prev,
      latitude: lat.toString(),
      longitude: lon.toString(),
    }))
  }

  function resetForm() {
    setRole("")
    setPartnerData({
      fullName: "",
      year: "",
      month: "",
      date: "",
      hours: "",
      minutes: "",
      latitude: "",
      longitude: "",
    })
    setPlaceSelected(false)
    setPlaceError(false)
    setError("")
    setResult(null)
    setLoading(false)
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!placeSelected) {
      setPlaceError(true)
      return
    }
    if (!role) {
      setError("Please choose whether you are entering the chart as the bride or the groom.")
      return
    }

    setLoading(true)
    setError("")

    try {
      const res = await fetch(`${backendUrl}/compatibility`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Session-Id": sessionId,
        },
        body: JSON.stringify({
          native_role: role,
          partner: {
            fullName: partnerData.fullName,
            year: parseInt(partnerData.year, 10),
            month: parseInt(partnerData.month, 10),
            date: parseInt(partnerData.date, 10),
            hours: parseInt(partnerData.hours, 10),
            minutes: parseInt(partnerData.minutes, 10),
            seconds: 0,
            latitude: parseFloat(partnerData.latitude),
            longitude: parseFloat(partnerData.longitude),
            timezone: "Asia/Kolkata",
            settings: {
              observation_point: "topocentric",
              ayanamsha: "lahiri",
            },
          },
        }),
      })

      if (!res.ok) {
        let message = "Failed to compute compatibility."
        try {
          const data = await res.json()
          message = data?.detail || data?.error || message
        } catch {
          // ignore JSON parse failure and keep default message
        }
        throw new Error(message)
      }

      const data: CompatibilityResponse = await res.json()
      setResult(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to compute compatibility.")
    } finally {
      setLoading(false)
    }
  }

  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/82 p-1 backdrop-blur-sm">
      <Card className="flex h-[min(94vh,960px)] w-[min(96vw,1380px)] flex-col overflow-hidden border border-rose-500/20 bg-slate-950/95 text-white shadow-2xl">
        <div className="flex flex-wrap items-start justify-between gap-3 border-b border-white/10 px-5 py-3">
          <div>
            <h2 className="text-xl font-semibold text-white">Kundli Milan</h2>
            <p className="text-sm text-slate-400">
              Compute Ashtakoot matching, total gunas out of 36, likely marriage strengths, and likely challenges.
            </p>
          </div>
          <Button
            type="button"
            variant="ghost"
            onClick={() => {
              onClose()
            }}
            className="text-slate-300 hover:bg-white/10 hover:text-white"
          >
            <X className="h-4 w-4" />
            <span className="ml-2">Close</span>
          </Button>
        </div>

        <div className="flex-1 overflow-hidden">
          <ScrollArea className="h-full">
            <div className="grid gap-5 px-4 py-4 lg:grid-cols-[360px_minmax(0,1fr)]">
              <section className="rounded-3xl border border-rose-400/15 bg-[radial-gradient(circle_at_top,_rgba(244,63,94,0.12),_rgba(15,23,42,0.96)_60%)] p-4 shadow-[inset_0_1px_0_rgba(255,255,255,0.04)]">
                <div className="mb-4 flex items-center gap-2 text-white">
                  <HeartHandshake className="h-5 w-5 text-rose-300" />
                  <h3 className="text-lg font-semibold">Partner Details</h3>
                </div>

                <form onSubmit={handleSubmit} className="grid gap-3">
                  <div className="grid gap-1.5">
                    <Label className="text-xs font-medium text-slate-300">Your Role</Label>
                    <select
                      value={role}
                      onChange={(e) => setRole(e.target.value as "" | "bride" | "groom")}
                      className="h-10 rounded-md border border-gray-600 bg-black px-3 text-sm text-gray-100 outline-none focus:border-rose-400"
                      required
                    >
                      <option value="">Choose bride or groom</option>
                      <option value="bride">I am the Bride</option>
                      <option value="groom">I am the Groom</option>
                    </select>
                  </div>

                  <div className="grid gap-1.5">
                    <Label className="text-xs font-medium text-slate-300">Partner Name</Label>
                    <Input
                      type="text"
                      value={partnerData.fullName}
                      onChange={(e) => setPartnerData((prev) => ({ ...prev, fullName: e.target.value }))}
                      placeholder="Enter partner's full name"
                      className="h-10 bg-black border-gray-600 text-gray-100 text-sm placeholder:text-gray-400 focus:border-rose-400 focus:ring-rose-400"
                      required
                    />
                  </div>

                  <div className="grid gap-1.5">
                    <Label className="text-xs font-medium text-slate-300">Date of Birth</Label>
                    <div className="flex gap-2">
                      <Input
                        type="number"
                        placeholder="YYYY"
                        value={partnerData.year}
                        onChange={(e) => setPartnerData((prev) => ({ ...prev, year: e.target.value }))}
                        className="h-10 bg-black border-gray-600 text-gray-100 text-sm placeholder:text-gray-400 focus:border-rose-400 focus:ring-rose-400"
                        required
                      />
                      <Input
                        type="number"
                        placeholder="MM"
                        value={partnerData.month}
                        onChange={(e) => setPartnerData((prev) => ({ ...prev, month: e.target.value }))}
                        className="h-10 bg-black border-gray-600 text-gray-100 text-sm placeholder:text-gray-400 focus:border-rose-400 focus:ring-rose-400"
                        required
                      />
                      <Input
                        type="number"
                        placeholder="DD"
                        value={partnerData.date}
                        onChange={(e) => setPartnerData((prev) => ({ ...prev, date: e.target.value }))}
                        className="h-10 bg-black border-gray-600 text-gray-100 text-sm placeholder:text-gray-400 focus:border-rose-400 focus:ring-rose-400"
                        required
                      />
                    </div>
                  </div>

                  <div className="grid gap-1.5">
                    <Label className="text-xs font-medium text-slate-300">Time of Birth</Label>
                    <div className="flex gap-2">
                      <Input
                        type="number"
                        placeholder="HH"
                        value={partnerData.hours}
                        onChange={(e) => setPartnerData((prev) => ({ ...prev, hours: e.target.value }))}
                        className="h-10 bg-black border-gray-600 text-gray-100 text-sm placeholder:text-gray-400 focus:border-rose-400 focus:ring-rose-400"
                        required
                      />
                      <Input
                        type="number"
                        placeholder="Min"
                        value={partnerData.minutes}
                        onChange={(e) => setPartnerData((prev) => ({ ...prev, minutes: e.target.value }))}
                        className="h-10 bg-black border-gray-600 text-gray-100 text-sm placeholder:text-gray-400 focus:border-rose-400 focus:ring-rose-400"
                        required
                      />
                    </div>
                    <p className="text-[11px] text-slate-500">Use 24-hour format. Timezone is currently fixed to India.</p>
                  </div>

                  <div className="grid gap-1.5">
                    <Label className="text-xs font-medium text-slate-300">Birth Place</Label>
                    <PlacesAutoComplete onPlaceSelect={handlePlaceSelect} />
                    {placeError ? (
                      <p className="text-[11px] text-rose-300">Please select the place from the dropdown.</p>
                    ) : null}
                  </div>

                  {error ? (
                    <div className="rounded-2xl border border-rose-400/20 bg-rose-500/8 px-3 py-2 text-xs text-rose-200">
                      {error}
                    </div>
                  ) : null}

                  <div className="mt-1 flex gap-2">
                    <Button
                      type="submit"
                      disabled={loading}
                      className="flex-1 bg-gradient-to-r from-rose-600 to-orange-500 text-white hover:from-rose-500 hover:to-orange-400"
                    >
                      {loading ? (
                        <>
                          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                          Matching...
                        </>
                      ) : (
                        <>
                          <Sparkles className="mr-2 h-4 w-4" />
                          Match Gunas
                        </>
                      )}
                    </Button>
                    <Button
                      type="button"
                      variant="outline"
                      onClick={resetForm}
                      className="border-white/15 bg-slate-900/80 text-slate-200 hover:bg-slate-800"
                    >
                      Reset
                    </Button>
                  </div>
                </form>
              </section>

              <section className="rounded-3xl border border-blue-400/15 bg-[radial-gradient(circle_at_top,_rgba(59,130,246,0.10),_rgba(15,23,42,0.96)_60%)] p-4 shadow-[inset_0_1px_0_rgba(255,255,255,0.04)]">
                {!result ? (
                  <div className="flex min-h-[420px] items-center justify-center rounded-3xl border border-white/8 bg-slate-950/50 px-6 text-center text-sm text-slate-400">
                    Fill in the partner details and compute the Ashtakoot match to see the guna score, marriage strengths, challenges, and full koota breakdown.
                  </div>
                ) : (
                  <div className="grid gap-4">
                    <div className="rounded-3xl border border-white/8 bg-slate-950/58 p-5">
                      <div className="flex flex-wrap items-end justify-between gap-4">
                        <div>
                          <div className="text-sm text-slate-400">
                            {result.native_name} and {result.partner_name}
                          </div>
                          <div className="mt-2 text-4xl font-semibold text-white">
                            {result.total_score}
                            <span className="ml-2 text-lg text-slate-400">/ {result.out_of}</span>
                          </div>
                          <div className="mt-2 text-sm font-medium text-rose-200">{result.verdict}</div>
                        </div>
                        <div className="rounded-2xl border border-rose-400/20 bg-rose-500/10 px-4 py-3 text-sm text-slate-200">
                          {result.score_summary}
                        </div>
                      </div>
                      <p className="mt-4 text-sm leading-6 text-slate-300">{result.compatibility_summary}</p>
                      <p className="mt-2 text-xs text-slate-500">{result.traditional_note}</p>
                    </div>

                    <div className="grid gap-4 xl:grid-cols-2">
                      <div className="rounded-3xl border border-emerald-400/15 bg-slate-950/58 p-4">
                        <div className="mb-3 text-sm font-semibold text-white">Best Part About Marriage</div>
                        <p className="text-sm leading-6 text-slate-200">{result.best_part_about_marriage}</p>
                      </div>

                      <div className="rounded-3xl border border-amber-400/15 bg-slate-950/58 p-4">
                        <div className="mb-3 text-sm font-semibold text-white">Likely Challenges</div>
                        <div className="grid gap-2">
                          {result.challenges.length ? result.challenges.map((item, index) => (
                            <div
                              key={`challenge-${index}`}
                              className="rounded-2xl border border-white/8 bg-white/[0.03] px-3 py-3 text-sm leading-6 text-slate-200"
                            >
                              {item}
                            </div>
                          )) : (
                            <div className="rounded-2xl border border-white/8 bg-white/[0.03] px-3 py-3 text-sm text-slate-300">
                              No major challenge dominates the match strongly.
                            </div>
                          )}
                        </div>
                      </div>
                    </div>

                    <div className="rounded-3xl border border-white/8 bg-slate-950/58 p-4">
                      <div className="mb-3 text-sm font-semibold text-white">Strong Areas</div>
                      <div className="grid gap-2">
                        {result.strengths.length ? result.strengths.map((item, index) => (
                          <div
                            key={`strength-${index}`}
                            className="rounded-2xl border border-white/8 bg-white/[0.03] px-3 py-3 text-sm leading-6 text-slate-200"
                          >
                            {item}
                          </div>
                        )) : (
                          <div className="rounded-2xl border border-white/8 bg-white/[0.03] px-3 py-3 text-sm text-slate-300">
                            This match is more mixed than strongly polarized, so no single factor dominates the strengths heavily.
                          </div>
                        )}
                      </div>
                    </div>

                    <div className="rounded-3xl border border-white/8 bg-slate-950/58 p-4">
                      <div className="mb-3 text-sm font-semibold text-white">Ashtakoot Breakdown</div>
                      <div className="grid gap-3 xl:grid-cols-2">
                        {result.breakdown.map((item) => (
                          <div
                            key={item.key}
                            className={`rounded-2xl border p-4 ${getBreakdownClasses(item.ratio)}`}
                          >
                            <div className="flex items-start justify-between gap-3">
                              <div>
                                <div className="text-sm font-semibold text-white">{item.title}</div>
                                <div className="text-xs text-slate-400">{item.meaning}</div>
                              </div>
                              <div className="rounded-full border border-white/10 bg-white/6 px-2.5 py-1 text-xs text-slate-100">
                                {item.score}/{item.out_of}
                              </div>
                            </div>
                            <div className="mt-3 grid gap-1 text-xs text-slate-300">
                              <div>Bride: {item.bride_value}</div>
                              <div>Groom: {item.groom_value}</div>
                            </div>
                            <p className="mt-3 text-sm leading-6 text-slate-200">{item.interpretation}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                )}
              </section>
            </div>
          </ScrollArea>
        </div>
      </Card>
    </div>
  )
}
