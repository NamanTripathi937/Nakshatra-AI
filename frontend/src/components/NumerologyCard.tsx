"use client"

import { Sparkles } from "lucide-react"

import { Card } from "@/components/ui/card"
import { cn } from "@/lib/utils"
import { buildCardCopy, type NumerologyNumber } from "@/lib/numerology-content"

type NumerologyCardProps = {
  item: NumerologyNumber
  featured?: boolean
}

export default function NumerologyCard({ item, featured = false }: NumerologyCardProps) {
  const copy = buildCardCopy(item)

  return (
    <Card
      className={cn(
        "overflow-hidden border text-white shadow-[0_20px_70px_rgba(4,10,24,0.28)] backdrop-blur-md",
        featured
          ? "rounded-[2rem] border-amber-300/18 bg-[radial-gradient(circle_at_top_left,_rgba(251,191,36,0.18),_rgba(34,211,238,0.09)_26%,_rgba(2,6,23,0.97)_78%)] p-7 sm:p-9"
          : "rounded-[1.75rem] border-white/10 bg-[linear-gradient(180deg,rgba(15,23,42,0.94),rgba(2,6,23,0.94))] p-6 sm:p-7"
      )}
    >
      <div className="flex items-start justify-between gap-5">
        <div className="min-w-0">
          <div className="inline-flex rounded-full border border-cyan-300/18 bg-cyan-400/8 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.22em] text-cyan-100">
            {item.label}
          </div>
          <h3
            className={cn(
              "mt-4 font-serif text-white",
              featured ? "text-4xl leading-tight sm:text-[3.25rem]" : "text-[1.7rem] leading-tight"
            )}
          >
            {item.title}
          </h3>
          <p
            className={cn(
              "mt-4 max-w-4xl text-slate-200",
              featured ? "text-[15px] leading-8 sm:text-base" : "text-sm leading-7"
            )}
          >
            {copy.intro}
          </p>
        </div>

        <div
          className={cn(
            "shrink-0 rounded-full border text-center font-semibold text-cyan-50 shadow-[inset_0_1px_0_rgba(255,255,255,0.12)]",
            featured
              ? "flex h-24 w-24 items-center justify-center border-amber-200/20 bg-amber-300/12 text-[2rem] sm:h-28 sm:w-28 sm:text-[2.3rem]"
              : "flex h-16 w-16 items-center justify-center border-cyan-200/12 bg-cyan-400/10 text-[1.45rem]"
          )}
        >
          {item.number}
        </div>
      </div>

      <p
        className={cn(
          "mt-6 text-slate-200",
          featured ? "max-w-4xl text-[15px] leading-8 sm:text-base" : "text-sm leading-7"
        )}
      >
        {copy.body}
      </p>

      <div className={cn("mt-6 grid gap-4", featured ? "lg:grid-cols-2" : "grid-cols-1")}>
        <div className="rounded-[1.35rem] border border-white/10 bg-black/14 p-4">
          <div className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.18em] text-cyan-100">
            <Sparkles className="h-3.5 w-3.5" />
            {copy.alignedTitle}
          </div>
          <p className="mt-3 text-sm leading-7 text-slate-300">{copy.alignedBody}</p>
        </div>

        <div className="rounded-[1.35rem] border border-white/10 bg-black/14 p-4">
          <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-amber-100">
            {copy.growthTitle}
          </div>
          <p className="mt-3 text-sm leading-7 text-slate-300">{copy.growthBody}</p>
        </div>
      </div>

      <div className="mt-5 flex flex-wrap gap-2">
        {item.keywords.map((keyword) => (
          <span
            key={keyword}
            className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-[11px] font-medium uppercase tracking-[0.16em] text-slate-200"
          >
            {keyword}
          </span>
        ))}
      </div>

      <details className="mt-6 rounded-[1.2rem] border border-white/8 bg-black/14 px-4 py-3 text-sm text-slate-300">
        <summary className="cursor-pointer list-none font-medium text-slate-200 marker:hidden">
          See Calculation
        </summary>
        <div className="mt-3 space-y-2 border-t border-white/6 pt-3 text-sm leading-6 text-slate-400">
          <p>{item.calculation}</p>
          <p>Reduction: {item.reduction}</p>
        </div>
      </details>
    </Card>
  )
}
