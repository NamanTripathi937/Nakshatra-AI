"use client"

import React from "react"

import { useAuth } from "@/lib/auth"

declare global {
  interface Window {
    google?: {
      accounts?: {
        id?: {
          initialize: (options: {
            client_id: string
            callback: (response: { credential?: string }) => void
          }) => void
          renderButton: (element: HTMLElement, options: Record<string, unknown>) => void
        }
      }
    }
  }
}

type GoogleSignInButtonProps = {
  className?: string
  theme?: "outline" | "filled_black" | "filled_blue"
  text?: "continue_with" | "signin_with" | "signup_with"
}

export default function GoogleSignInButton({
  className,
  theme = "outline",
  text = "continue_with",
}: GoogleSignInButtonProps) {
  const { signInWithGoogleCredential } = useAuth()
  const containerRef = React.useRef<HTMLDivElement | null>(null)
  const clientId = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID || ""
  const [googleReady, setGoogleReady] = React.useState(false)

  React.useEffect(() => {
    if (!clientId) return

    if (window.google?.accounts?.id) {
      setGoogleReady(true)
      return
    }

    const interval = window.setInterval(() => {
      if (window.google?.accounts?.id) {
        setGoogleReady(true)
        window.clearInterval(interval)
      }
    }, 250)

    return () => window.clearInterval(interval)
  }, [clientId])

  React.useEffect(() => {
    if (!clientId || !containerRef.current || !googleReady || !window.google?.accounts?.id) return

    const container = containerRef.current
    container.innerHTML = ""

    window.google.accounts.id.initialize({
      client_id: clientId,
      callback: ({ credential }) => {
        if (!credential) return
        void signInWithGoogleCredential(credential)
      },
    })

    window.google.accounts.id.renderButton(container, {
      theme,
      text,
      size: "large",
      shape: "pill",
      width: 280,
      logo_alignment: "left",
    })
  }, [clientId, googleReady, signInWithGoogleCredential, text, theme])

  if (!clientId) {
    return (
      <div className={className}>
        <div className="rounded-xl border border-amber-400/30 bg-amber-500/10 px-4 py-3 text-sm text-amber-100">
          Google sign-in is not configured yet. Add `NEXT_PUBLIC_GOOGLE_CLIENT_ID` to enable it.
        </div>
      </div>
    )
  }

  return (
    <div className={className}>
      {!googleReady ? (
        <div className="inline-flex h-11 min-w-[280px] items-center justify-center rounded-full border border-white/12 bg-white/6 px-5 text-sm font-medium text-slate-200">
          Loading Google sign-in…
        </div>
      ) : null}
      <div ref={containerRef} className={googleReady ? "" : "hidden"} />
    </div>
  )
}
