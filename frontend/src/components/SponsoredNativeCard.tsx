"use client"

import React from "react"
import { Crown, Sparkles } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"

type SponsoredNativeCardProps = {
  onOpenBilling: () => void
}

export default function SponsoredNativeCard({ onOpenBilling }: SponsoredNativeCardProps) {
  return (
    <Card className="border border-cyan-400/15 bg-[linear-gradient(135deg,rgba(8,47,73,0.92),rgba(15,23,42,0.98))] px-4 py-4 text-white shadow-md">
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-cyan-200">Sponsored</div>
          <div className="mt-2 text-base font-semibold text-white">Consult a live astrologer</div>
          <p className="mt-2 text-sm leading-6 text-slate-200">
            Prefer a human touch for major life questions? Unlock richer chart analysis now and stay ready for live consultation add-ons.
          </p>
        </div>
        <div className="hidden rounded-full bg-amber-500/15 px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.16em] text-amber-200 sm:inline-flex">
          <Sparkles className="mr-1 h-3.5 w-3.5" />
          Premium
        </div>
      </div>

      <div className="mt-4 flex justify-start">
        <Button
          type="button"
          onClick={onOpenBilling}
          className="bg-amber-500 text-slate-950 hover:bg-amber-400"
        >
          <Crown className="mr-2 h-4 w-4" />
          Explore Premium
        </Button>
      </div>
    </Card>
  )
}
