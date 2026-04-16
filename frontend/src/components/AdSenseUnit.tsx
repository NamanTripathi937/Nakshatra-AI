"use client"

import React from "react"

declare global {
  interface Window {
    adsbygoogle?: Array<Record<string, unknown>>
  }
}

type AdSenseUnitProps = {
  slot?: string
  format?: "auto" | "horizontal" | "rectangle"
  className?: string
  style?: React.CSSProperties
}

const ADSENSE_CLIENT_ID = process.env.NEXT_PUBLIC_ADSENSE_CLIENT_ID

export default function AdSenseUnit({
  slot,
  format = "auto",
  className = "",
  style,
}: AdSenseUnitProps) {
  const adRef = React.useRef<HTMLModElement | null>(null)
  const canRenderLiveAd = Boolean(ADSENSE_CLIENT_ID && slot)
  const isDevelopment = process.env.NODE_ENV !== "production"

  React.useEffect(() => {
    if (!canRenderLiveAd || !adRef.current) return

    const element = adRef.current
    if (element.dataset.adStatus === "loaded") return

    try {
      ;(window.adsbygoogle = window.adsbygoogle || []).push({})
      element.dataset.adStatus = "loaded"
    } catch {
      // Leave the slot empty if AdSense has not initialized yet.
    }
  }, [canRenderLiveAd, slot])

  if (!canRenderLiveAd) {
    if (!isDevelopment) return null
    return (
      <div
        className={`flex items-center justify-center rounded-2xl border border-dashed border-cyan-400/20 bg-slate-950/55 px-4 py-4 text-center text-xs text-slate-400 ${className}`}
        style={style}
      >
        AdSense slot preview. Add `NEXT_PUBLIC_ADSENSE_CLIENT_ID` and a slot id to render a live ad here.
      </div>
    )
  }

  return (
    <ins
      ref={adRef}
      className={`adsbygoogle block overflow-hidden ${className}`}
      style={{ display: "block", ...style }}
      data-ad-client={ADSENSE_CLIENT_ID}
      data-ad-slot={slot}
      data-ad-format={format}
      data-full-width-responsive="true"
    />
  )
}
