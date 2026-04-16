"use client"

import React from "react"

import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { buildAuthHeaders, useAuth } from "@/lib/auth"
import { Crown, Loader2, Sparkles, X } from "lucide-react"

type BillingPlansModalProps = {
  backendUrl: string
  open: boolean
  onClose: () => void
}

type BillingPlan = {
  code: string
  kind: "addon_questions" | "membership"
  name: string
  tagline: string
  description: string
  amount_paise: number
  currency: string
  display_price: string
  benefits: string[]
  badge?: string
  question_credits?: number
  duration_days?: number
}

type BillingPlansResponse = {
  configured: boolean
  gateway: string
  plans: BillingPlan[]
}

type CheckoutResponse = {
  plan: BillingPlan
  checkout: {
    key: string
    order_id: string
    amount: number
    currency: string
    name: string
    description: string
    prefill: {
      name?: string
      email?: string
    }
    theme?: {
      color?: string
    }
  }
}

declare global {
  interface Window {
    Razorpay?: new (options: Record<string, unknown>) => {
      open: () => void
      on: (event: string, callback: (payload: any) => void) => void
    }
  }
}

let razorpayScriptPromise: Promise<boolean> | null = null

function loadRazorpayScript(): Promise<boolean> {
  if (typeof window === "undefined") return Promise.resolve(false)
  if (window.Razorpay) return Promise.resolve(true)
  if (razorpayScriptPromise) return razorpayScriptPromise

  razorpayScriptPromise = new Promise((resolve) => {
    const script = document.createElement("script")
    script.src = "https://checkout.razorpay.com/v1/checkout.js"
    script.async = true
    script.onload = () => resolve(true)
    script.onerror = () => resolve(false)
    document.body.appendChild(script)
  })

  return razorpayScriptPromise
}

function formatDateTime(value?: string | null) {
  if (!value) return null
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return null
  return new Intl.DateTimeFormat(undefined, {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
  }).format(date)
}

export default function BillingPlansModal({ backendUrl, open, onClose }: BillingPlansModalProps) {
  const { token, user, refreshUser } = useAuth()
  const [plans, setPlans] = React.useState<BillingPlan[]>([])
  const [configured, setConfigured] = React.useState(true)
  const [loading, setLoading] = React.useState(false)
  const [error, setError] = React.useState("")
  const [status, setStatus] = React.useState("")
  const [payingPlanCode, setPayingPlanCode] = React.useState("")

  React.useEffect(() => {
    if (!open || !token) return

    let cancelled = false

    async function loadPlans() {
      setLoading(true)
      setError("")
      try {
        const res = await fetch(`${backendUrl}/billing/plans`, {
          headers: buildAuthHeaders(token),
        })
        if (!res.ok) {
          let message = "Failed to load plans."
          try {
            const data = await res.json()
            message = data?.detail?.message || data?.detail || data?.error || message
          } catch {
            // ignore parse failures
          }
          throw new Error(message)
        }
        const data: BillingPlansResponse = await res.json()
        if (!cancelled) {
          setPlans(data.plans || [])
          setConfigured(Boolean(data.configured))
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Failed to load plans.")
        }
      } finally {
        if (!cancelled) {
          setLoading(false)
        }
      }
    }

    void loadPlans()
    return () => {
      cancelled = true
    }
  }, [backendUrl, open, token])

  React.useEffect(() => {
    if (!open) {
      setError("")
      setStatus("")
      setPayingPlanCode("")
    }
  }, [open])

  async function startCheckout(plan: BillingPlan) {
    if (!token || !user) return
    setPayingPlanCode(plan.code)
    setError("")
    setStatus("")

    try {
      const scriptLoaded = await loadRazorpayScript()
      if (!scriptLoaded || !window.Razorpay) {
        throw new Error("Unable to load the payment window right now.")
      }

      const checkoutRes = await fetch(`${backendUrl}/billing/checkout`, {
        method: "POST",
        headers: buildAuthHeaders(token, { "Content-Type": "application/json" }),
        body: JSON.stringify({ plan_code: plan.code }),
      })

      if (!checkoutRes.ok) {
        let message = "Failed to start checkout."
        try {
          const data = await checkoutRes.json()
          message = data?.detail?.message || data?.detail || data?.error || message
        } catch {
          // ignore parse failures
        }
        throw new Error(message)
      }

      const checkoutData: CheckoutResponse = await checkoutRes.json()

      const razorpay = new window.Razorpay({
        ...checkoutData.checkout,
        modal: {
          ondismiss: () => {
            setPayingPlanCode("")
          },
        },
        handler: async (response: {
          razorpay_payment_id: string
          razorpay_order_id: string
          razorpay_signature: string
        }) => {
          setStatus("Verifying your payment and unlocking access...")

          const verifyRes = await fetch(`${backendUrl}/billing/verify`, {
            method: "POST",
            headers: buildAuthHeaders(token, { "Content-Type": "application/json" }),
            body: JSON.stringify(response),
          })

          if (!verifyRes.ok) {
            let message = "Payment was received, but verification failed."
            try {
              const data = await verifyRes.json()
              message = data?.detail?.message || data?.detail || data?.error || message
            } catch {
              // ignore parse failures
            }
            throw new Error(message)
          }

          await verifyRes.json()
          await refreshUser()
          setStatus(
            plan.kind === "membership"
              ? "Premium access is now active on your account."
              : "Your extra questions have been added to your account."
          )
          setPayingPlanCode("")
        },
      })

      razorpay.on("payment.failed", (response: any) => {
        const message =
          response?.error?.description ||
          response?.error?.reason ||
          "Payment did not go through."
        setError(message)
        setPayingPlanCode("")
      })

      razorpay.open()
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to complete payment right now.")
      setPayingPlanCode("")
    }
  }

  if (!open) return null

  const premiumUntil = formatDateTime(user?.billing?.premium_until)
  const extraQuestionBalance = user?.billing?.extra_questions_balance ?? 0

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/82 p-3 backdrop-blur-sm">
      <Card className="flex h-[min(92vh,860px)] w-[min(96vw,1080px)] flex-col overflow-hidden border border-cyan-400/20 bg-slate-950/95 text-white shadow-2xl">
        <div className="flex items-start justify-between gap-4 border-b border-white/10 px-5 py-4">
          <div>
            <h2 className="text-xl font-semibold text-white">Upgrade Your Account</h2>
            <p className="mt-1 text-sm text-slate-400">
              Buy extra questions or unlock full Premium access with secure Razorpay checkout.
            </p>
          </div>
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

        <div className="flex-1 overflow-y-auto px-5 py-5">
          <div className="mb-5 grid gap-3 lg:grid-cols-[1.25fr_0.95fr]">
            <div className="rounded-3xl border border-cyan-400/15 bg-[radial-gradient(circle_at_top,_rgba(34,211,238,0.12),_rgba(15,23,42,0.96)_62%)] p-4">
              <div className="flex items-center gap-2 text-white">
                <Sparkles className="h-4 w-4 text-cyan-300" />
                <div className="text-sm font-semibold">Current Access</div>
              </div>
              <div className="mt-2 text-sm leading-6 text-slate-300">
                {user?.plan_access.is_premium
                  ? `Premium is active${premiumUntil ? ` until ${premiumUntil}` : ""}.`
                  : `${user?.plan_access.daily_questions_remaining ?? 0} questions are currently available on your account.`}
              </div>
              {!user?.plan_access.is_premium ? (
                <div className="mt-2 text-xs text-slate-400">
                  Free daily left: {user?.plan_access.free_daily_questions_remaining ?? 0} • Paid booster balance: {extraQuestionBalance}
                </div>
              ) : null}
            </div>

            <div className="rounded-3xl border border-amber-400/20 bg-amber-500/10 p-4">
              <div className="flex items-center gap-2 text-white">
                <Crown className="h-4 w-4 text-amber-200" />
                <div className="text-sm font-semibold">What Premium Unlocks</div>
              </div>
              <div className="mt-2 text-sm leading-6 text-amber-100/90">
                Unlimited chat, full detailed readings, D9 and D10 charts, remedies, matchmaking, ad-free use, and future premium features.
              </div>
            </div>
          </div>

          {!configured ? (
            <div className="rounded-2xl border border-rose-400/20 bg-rose-500/10 px-4 py-3 text-sm text-rose-100">
              Billing is not configured on the server yet. Add the Razorpay keys on the backend and refresh this screen.
            </div>
          ) : null}
          {error ? (
            <div className="mt-3 rounded-2xl border border-rose-400/20 bg-rose-500/10 px-4 py-3 text-sm text-rose-100">
              {error}
            </div>
          ) : null}
          {status ? (
            <div className="mt-3 rounded-2xl border border-emerald-400/20 bg-emerald-500/10 px-4 py-3 text-sm text-emerald-100">
              {status}
            </div>
          ) : null}

          {loading ? (
            <div className="flex min-h-[260px] items-center justify-center text-slate-300">
              <Loader2 className="mr-3 h-5 w-5 animate-spin" />
              Loading plans...
            </div>
          ) : (
            <div className="mt-5 grid gap-4 lg:grid-cols-2">
              {plans.map((plan) => {
                const isPremiumUser = Boolean(user?.plan_access.is_premium)
                const disableForCurrentUser = isPremiumUser && plan.kind === "addon_questions"
                const ctaLabel =
                  plan.kind === "membership"
                    ? isPremiumUser
                      ? "Extend Premium"
                      : "Unlock Premium"
                    : "Buy Booster"

                return (
                  <section
                    key={plan.code}
                    className={`rounded-3xl border p-5 ${
                      plan.kind === "membership"
                        ? "border-amber-400/25 bg-[radial-gradient(circle_at_top,_rgba(251,191,36,0.16),_rgba(15,23,42,0.95)_62%)]"
                        : "border-cyan-400/18 bg-[radial-gradient(circle_at_top,_rgba(34,211,238,0.12),_rgba(15,23,42,0.95)_60%)]"
                    }`}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <h3 className="text-lg font-semibold text-white">{plan.name}</h3>
                        <p className="mt-1 text-sm text-slate-300">{plan.tagline}</p>
                      </div>
                      {plan.badge ? (
                        <span className="rounded-full border border-white/12 bg-white/8 px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-200">
                          {plan.badge}
                        </span>
                      ) : null}
                    </div>

                    <div className="mt-4 text-3xl font-semibold text-white">{plan.display_price}</div>
                    <div className="mt-1 text-xs text-slate-400">
                      {plan.kind === "membership"
                        ? `${plan.duration_days ?? 30} days of premium access`
                        : `${plan.question_credits ?? 0} extra questions added`}
                    </div>

                    <p className="mt-4 text-sm leading-6 text-slate-300">{plan.description}</p>

                    <div className="mt-4 space-y-2 text-sm text-slate-200">
                      {plan.benefits.map((benefit) => (
                        <div key={`${plan.code}-${benefit}`} className="flex items-start gap-2">
                          <span className="mt-[6px] h-1.5 w-1.5 rounded-full bg-cyan-300" />
                          <span>{benefit}</span>
                        </div>
                      ))}
                    </div>

                    {disableForCurrentUser ? (
                      <div className="mt-5 rounded-2xl border border-white/10 bg-white/[0.04] px-3 py-2 text-xs text-slate-400">
                        This add-on is unnecessary while Premium is active because your questions are already unlimited.
                      </div>
                    ) : (
                      <Button
                        type="button"
                        onClick={() => void startCheckout(plan)}
                        disabled={Boolean(payingPlanCode) || !configured}
                        className={`mt-5 h-11 w-full ${
                          plan.kind === "membership"
                            ? "bg-amber-500 text-slate-950 hover:bg-amber-400"
                            : "bg-cyan-600 text-white hover:bg-cyan-500"
                        }`}
                      >
                        {payingPlanCode === plan.code ? (
                          <>
                            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                            Opening checkout...
                          </>
                        ) : (
                          ctaLabel
                        )}
                      </Button>
                    )}
                  </section>
                )
              })}
            </div>
          )}
        </div>
      </Card>
    </div>
  )
}
