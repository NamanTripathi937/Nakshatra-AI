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
        <div className="flex flex-1 items-center justify-center px-4 py-8 sm:py-12">
          <BillingPlansModal
            backendUrl={backendUrl}
            open={billingOpen}
            onClose={() => setBillingOpen(false)}
          />
          <div className="grid w-full max-w-6xl gap-6 lg:grid-cols-[minmax(0,420px)_minmax(0,520px)] lg:items-center">
            <section className="space-y-5">
              <div className="space-y-3">
                <div className="inline-flex rounded-full border border-cyan-400/20 bg-cyan-500/10 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.18em] text-cyan-200">
                  Monetized Reading Flow
                </div>
                <h2 className="max-w-xl text-3xl font-semibold leading-tight text-white sm:text-4xl">
                  Secure your chart, track your usage, and unlock Premium astrology tools.
                </h2>
                <p className="max-w-xl text-sm leading-6 text-slate-300 sm:text-base">
                  Free accounts get 5 questions per day and a concise kundli summary. Premium unlocks full readings, D9 and D10 charts, remedies, matchmaking, transit insights, and downloadable reports.
                </p>
              </div>

              <div className="grid gap-3 sm:grid-cols-2">
                <Card className="rounded-3xl border border-white/10 bg-slate-950/60 p-4 text-white">
                  <div className="mb-2 text-lg font-semibold">Free</div>
                  <ul className="space-y-2 text-sm text-slate-300">
                    <li>5 questions per day</li>
                    <li>Basic kundli summary</li>
                    <li>Lagna chart access</li>
                    <li>Sponsored experience</li>
                  </ul>
                </Card>
                <Card className="rounded-3xl border border-amber-400/25 bg-[radial-gradient(circle_at_top,_rgba(251,191,36,0.18),_rgba(15,23,42,0.94)_58%)] p-4 text-white">
                  <div className="mb-2 text-lg font-semibold">Premium</div>
                  <ul className="space-y-2 text-sm text-slate-200">
                    <li>Unlimited questions</li>
                    <li>Full detailed readings</li>
                    <li>D9, D10, remedies, matching</li>
                    <li>Daily transits and PDF reports</li>
                  </ul>
                  <div className="mt-3 text-xs text-amber-200/90">Rs. 99 monthly</div>
                </Card>
              </div>

              {!user ? (
                <Card id="auth-panel" className="rounded-3xl border border-white/10 bg-slate-950/70 p-5 text-white">
                  <div className="mb-2 text-lg font-semibold">Sign In / Sign Up to begin</div>
                  <p className="mb-4 text-sm text-slate-300">
                    Your readings now live under your account instead of a temporary browser session.
                  </p>
                  <div className="mb-3 inline-flex rounded-full border border-blue-400/20 bg-blue-500/10 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.18em] text-blue-200">
                    Continue With Google
                  </div>
                  <GoogleSignInButton text="signup_with" />
                  {authError ? <p className="mt-3 text-sm text-rose-300">{authError}</p> : null}
                </Card>
              ) : (
                <div className="space-y-4">
                  <Card className="rounded-3xl border border-emerald-400/20 bg-emerald-500/10 p-4 text-white">
                    <div className="text-sm font-medium text-emerald-100">Signed in as {user.email}</div>
                    <div className="mt-1 text-xs text-emerald-200/90">
                      {user.plan_access.is_premium
                        ? `Premium access active${user.billing?.premium_until ? ` until ${new Date(user.billing.premium_until).toLocaleDateString()}` : ""}.`
                        : `${user.plan_access.daily_questions_remaining ?? 0} questions available today${(user.plan_access.extra_questions_balance ?? 0) > 0 ? ` (${user.plan_access.extra_questions_balance} paid booster)` : ""}.`}
                    </div>
                    <div className="mt-3">
                      <Button
                        type="button"
                        onClick={() => setBillingOpen(true)}
                        className={user.plan_access.is_premium ? "bg-amber-500 text-slate-950 hover:bg-amber-400" : "bg-cyan-600 text-white hover:bg-cyan-500"}
                      >
                        {user.plan_access.is_premium ? "Manage Premium" : "Upgrade / Buy Questions"}
                      </Button>
                    </div>
                  </Card>
                  <AccountHistory backendUrl={backendUrl} variant="embedded" limit={3} />
                </div>
              )}
            </section>

            <div className="flex justify-center lg:justify-end">
              {authLoading ? (
                <Card className="w-full max-w-md rounded-3xl border border-white/10 bg-slate-950/70 p-6 text-sm text-slate-300">
                  Restoring your account…
                </Card>
              ) : user ? (
                <KundaliForm onSubmit={handleFormSubmit} loading={loading} />
              ) : (
                <Card className="w-full max-w-md rounded-3xl border border-white/10 bg-slate-950/70 p-6 text-center text-slate-300">
                  <div className="mb-3 text-lg font-semibold text-white">Birth form unlocks after sign-in</div>
                  <p className="text-sm leading-6">
                    We now attach every reading to your account so you can come back to the same chart, session, and premium entitlements later.
                  </p>
                </Card>
              )}
            </div>
          </div>
        </div>
  )
}
