"use client"

import React, { useState, useEffect } from "react"
import AccountHistory from "./AccountHistory"
import BillingPlansModal from "./BillingPlansModal"
import KundaliForm from "./KundaliForm"
import GoogleSignInButton from "./GoogleSignInButton"
import { Card } from "./ui/card"
import { Button } from "./ui/button"
import { buildAuthHeaders, useAuth } from "@/lib/auth"
import { getBackendUrl } from "@/lib/utils"
import { useRouter } from "next/navigation"

export default function KundaliPage() {
  const [loading, setLoading] = useState(false)
  const [billingOpen, setBillingOpen] = useState(false)

  const router = useRouter();
  const backendUrl = getBackendUrl();
  const { user, token, loading: authLoading, error: authError } = useAuth()

  useEffect(() => {
    fetch(`${backendUrl}/ping`).catch(() => { })
    console.log('Sent ping to backend')
  }, [backendUrl])

  const handleFormSubmit = async (data: any) => {
    if (loading || !token || !user) return;
    setLoading(true);

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
      router.push(`/chatWindow/${sessionId}`);
      const res = await fetch(`${backendUrl}/kundli`, {
        method: "POST",
        headers: buildAuthHeaders(token, {
          "Content-Type": "application/json",
          "X-Session-Id": sessionId,
        }),
        body: JSON.stringify(data),
      });

      if (!res.ok) {
        throw new Error("Unable to generate your kundli.")
      }
    } catch (err) {
      console.error("kundli API error", err);
    } finally {
      setLoading(false);
    }

  };
  return (
        <div className="flex flex-1 items-center justify-center px-4 py-6 sm:py-8 lg:h-full lg:px-8 lg:py-4 xl:px-12">
          <BillingPlansModal
            backendUrl={backendUrl}
            open={billingOpen}
            onClose={() => setBillingOpen(false)}
          />
          <div className="grid w-full gap-5 lg:h-full lg:grid-cols-[minmax(240px,1fr)_minmax(380px,440px)_minmax(260px,1fr)] lg:items-center">
            <aside className="order-2 space-y-3 lg:order-1 lg:justify-self-start lg:w-full lg:max-w-[300px]">
              <Card className="rounded-3xl border border-cyan-400/15 bg-slate-950/62 p-4 text-white shadow-[inset_0_1px_0_rgba(255,255,255,0.03)]">
                <div className="mb-2 text-sm font-semibold uppercase tracking-[0.18em] text-cyan-200">History</div>
                <p className="text-sm leading-5 text-slate-300">
                  Reopen your recent readings and continue from the same chart context whenever you come back.
                </p>
              </Card>

              {user ? (
                <AccountHistory backendUrl={backendUrl} variant="embedded" limit={3} />
              ) : (
                <Card className="rounded-3xl border border-white/10 bg-slate-950/58 p-4 text-white">
                  <div className="text-base font-semibold">History unlocks after sign-in</div>
                  <p className="mt-2 text-sm leading-5 text-slate-300">
                    Once you sign in, your readings stay attached to your account and appear here for quick access.
                  </p>
                </Card>
              )}
            </aside>

            <section className="order-1 flex justify-center lg:order-2 lg:justify-self-center">
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
                    <div className="mb-2 text-[1.45rem] font-semibold leading-tight sm:text-[1.75rem]">Sign In / Sign Up to begin</div>
                    <p className="mx-auto mb-4 max-w-sm text-sm leading-5 text-slate-300">
                      Your readings now live under your account instead of a temporary browser session.
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
            </section>

            <aside className="order-3 space-y-4 lg:justify-self-end lg:w-full lg:max-w-[340px]">
              <div className="space-y-2">
                <div className="inline-flex rounded-full border border-cyan-400/20 bg-cyan-500/10 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.18em] text-cyan-200">
                  Monetized Reading Flow
                </div>
                <h2 className="text-[1.9rem] font-semibold leading-tight text-white sm:text-[2.2rem]">
                  Secure your chart, track your usage, and unlock Premium astrology tools.
                </h2>
                <p className="text-sm leading-5 text-slate-300 sm:text-[15px]">
                  Free accounts get 5 questions per day and a concise kundli summary. Premium unlocks full readings, D9 and D10 charts, remedies, matchmaking, transit insights, and downloadable reports.
                </p>
              </div>

              <div className="grid gap-2.5">
                <Card className="rounded-3xl border border-white/10 bg-slate-950/60 p-4 text-white">
                  <div className="mb-2 text-base font-semibold">Free</div>
                  <ul className="space-y-1.5 text-sm text-slate-300">
                    <li>5 questions per day</li>
                    <li>Basic kundli summary</li>
                    <li>Lagna chart access</li>
                    <li>Sponsored experience</li>
                  </ul>
                </Card>
                <Card className="rounded-3xl border border-amber-400/25 bg-[radial-gradient(circle_at_top,_rgba(251,191,36,0.18),_rgba(15,23,42,0.94)_58%)] p-4 text-white">
                  <div className="mb-2 text-base font-semibold">Premium</div>
                  <ul className="space-y-1.5 text-sm text-slate-200">
                    <li>Unlimited questions</li>
                    <li>Full detailed readings</li>
                    <li>D9, D10, remedies, matching</li>
                    <li>Daily transits and PDF reports</li>
                  </ul>
                  <div className="mt-3 text-xs text-amber-200/90">Rs. 99 monthly</div>
                </Card>
              </div>
            </aside>
          </div>
        </div>
  )
}
