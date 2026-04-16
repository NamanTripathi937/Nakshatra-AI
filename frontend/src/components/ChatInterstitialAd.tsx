"use client"

import React from "react"
import { X } from "lucide-react"

import AdSenseUnit from "@/components/AdSenseUnit"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"

type ChatInterstitialAdProps = {
  open: boolean
  onClose: () => void
}

const INTERSTITIAL_SLOT = process.env.NEXT_PUBLIC_ADSENSE_CHAT_INTERSTITIAL_SLOT

export default function ChatInterstitialAd({ open, onClose }: ChatInterstitialAdProps) {
  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/82 p-4 backdrop-blur-sm">
      <Card className="w-full max-w-xl rounded-3xl border border-cyan-400/18 bg-slate-950/96 p-4 text-white shadow-2xl">
        <div className="flex items-start justify-between gap-4">
          <div>
            <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-cyan-200">Sponsored</div>
            <h3 className="mt-2 text-xl font-semibold text-white">A quick sponsor break</h3>
            <p className="mt-2 text-sm leading-6 text-slate-300">
              Free readings are supported by ads. Thanks for helping keep Nakshatra AI accessible.
            </p>
          </div>
          <Button
            type="button"
            variant="ghost"
            onClick={onClose}
            className="text-slate-300 hover:bg-white/10 hover:text-white"
          >
            <X className="h-4 w-4" />
          </Button>
        </div>

        <div className="mt-4 rounded-3xl border border-white/8 bg-slate-900/75 p-3">
          <AdSenseUnit
            slot={INTERSTITIAL_SLOT}
            format="rectangle"
            className="mx-auto min-h-[250px] w-full max-w-[420px]"
            style={{ minHeight: 250 }}
          />
        </div>

        <div className="mt-4 flex justify-end">
          <Button
            type="button"
            onClick={onClose}
            className="bg-cyan-600 text-white hover:bg-cyan-500"
          >
            Continue Reading
          </Button>
        </div>
      </Card>
    </div>
  )
}
