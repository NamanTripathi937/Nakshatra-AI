'use client';
import { useState } from "react";
import Link from "next/link";
import { Crown, History, Home, LogOut, Menu, Sparkles } from "lucide-react";

import AccountHistory from "@/components/AccountHistory";
import BillingPlansModal from "@/components/BillingPlansModal";
import { Button } from "@/components/ui/button";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { useAuth } from "@/lib/auth";
import { getBackendUrl } from "@/lib/utils";

function formatPremiumDaysRemaining(daysRemaining?: number | null) {
  if (!daysRemaining || daysRemaining <= 0) return "Premium account"
  return `${daysRemaining} day${daysRemaining === 1 ? "" : "s"} left`
}

export default function Header() {
  const [historyOpen, setHistoryOpen] = useState(false)
  const [billingOpen, setBillingOpen] = useState(false)
  const { user, signOut } = useAuth()
  const plan = user?.plan_access.plan ?? "free"
  const remaining = user?.plan_access.daily_questions_remaining
  const extraQuestions = user?.plan_access.extra_questions_balance ?? 0
  const premiumDaysRemaining = user?.billing?.premium_days_remaining
  const backendUrl = getBackendUrl()

  return (  
          <>
          <AccountHistory
            backendUrl={backendUrl}
            open={historyOpen}
            onClose={() => setHistoryOpen(false)}
            variant="modal"
          />
          <BillingPlansModal
            backendUrl={backendUrl}
            open={billingOpen}
            onClose={() => setBillingOpen(false)}
          />
          <header className="backdrop-blur-md border-b border-gray-700 shadow-sm mb-4 bg-black/20">
            <div className="grid grid-cols-[auto_minmax(0,1fr)_auto] items-center gap-1.5 px-3 py-3 lg:grid-cols-[minmax(0,1fr)_auto_minmax(0,1fr)] lg:gap-3 lg:px-6 lg:py-4">
              <div className="flex items-center justify-start">
                <Link
                  href="/"
                  aria-label="Nakshatra AI home"
                  className="inline-flex text-white transition-colors hover:text-blue-400"
                >
                  <Home className="h-5 w-5 shrink-0 lg:h-6 lg:w-6" aria-hidden="true" />
                </Link>
              </div>

              <Link
                href="/"
                aria-label="Nakshatra AI home"
                className="truncate px-1 text-center text-sm font-bold tracking-[0.18em] bg-gradient-to-r from-white to-blue-300 bg-clip-text text-transparent lg:px-2 lg:text-2xl lg:tracking-normal"
              >
                <span className="lg:hidden">NAKSHATRA</span>
                <span className="hidden lg:inline">✦ N A K S H A T R A ✦</span>
              </Link>

              <div className="flex items-center justify-end gap-1 lg:gap-2">
                {user ? (
                  <>
                    <Popover>
                      <PopoverTrigger asChild>
                        <Button
                          type="button"
                          variant="ghost"
                          className="h-8 px-1.5 text-slate-200 hover:bg-white/10 hover:text-white lg:hidden"
                        >
                          <Menu className="h-4 w-4" />
                        </Button>
                      </PopoverTrigger>
                      <PopoverContent
                        align="end"
                        className="w-56 rounded-2xl border border-white/10 bg-slate-950/96 p-2 text-white shadow-2xl lg:hidden"
                      >
                        <div className="px-2 py-2">
                          <div className="text-sm font-medium text-white">{user.name.split(" ")[0]}</div>
                          <div className="mt-1 text-[11px] text-slate-400">
                            {plan === "premium"
                              ? formatPremiumDaysRemaining(premiumDaysRemaining)
                              : extraQuestions > 0
                                ? `${remaining ?? 0} questions available (${extraQuestions} paid)`
                                : `${remaining ?? 0} free questions left today`}
                          </div>
                        </div>
                        <div className="my-1 h-px bg-white/8" />
                        <Button
                          type="button"
                          variant="ghost"
                          onClick={() => setBillingOpen(true)}
                          className={`flex h-9 w-full items-center justify-start gap-2 rounded-xl px-3 ${
                            plan === "premium"
                              ? "text-amber-200 hover:bg-amber-500/10 hover:text-amber-100"
                              : "text-cyan-200 hover:bg-cyan-500/10 hover:text-cyan-100"
                          }`}
                        >
                          <Crown className="h-4 w-4" />
                          <span>{plan === "premium" ? "Premium" : "Upgrade"}</span>
                        </Button>
                        <Button
                          type="button"
                          variant="ghost"
                          onClick={() => setHistoryOpen(true)}
                          className="flex h-9 w-full items-center justify-start gap-2 rounded-xl px-3 text-slate-200 hover:bg-white/10 hover:text-white"
                        >
                          <History className="h-4 w-4" />
                          <span>History</span>
                        </Button>
                        <Button
                          type="button"
                          variant="ghost"
                          onClick={signOut}
                          className="flex h-9 w-full items-center justify-start gap-2 rounded-xl px-3 text-slate-200 hover:bg-white/10 hover:text-white"
                        >
                          <LogOut className="h-4 w-4" />
                          <span>Sign out</span>
                        </Button>
                      </PopoverContent>
                    </Popover>
                    <div className="hidden text-right lg:block">
                      <div className="text-sm font-medium text-white">{user.name.split(" ")[0]}</div>
                      <div className="text-[11px] text-slate-400">
                        {plan === "premium"
                          ? formatPremiumDaysRemaining(premiumDaysRemaining)
                          : extraQuestions > 0
                            ? `${remaining ?? 0} questions available (${extraQuestions} paid)`
                            : `${remaining ?? 0} free questions left today`}
                      </div>
                    </div>
                    <div
                      className={`hidden rounded-full px-2 py-1 text-[10px] font-semibold uppercase tracking-[0.16em] lg:inline-flex ${
                        plan === "premium"
                          ? "bg-amber-500/15 text-amber-200"
                          : "bg-slate-700/70 text-slate-200"
                      }`}
                    >
                      {plan}
                    </div>
                    <Button
                      type="button"
                      variant="ghost"
                      onClick={() => setBillingOpen(true)}
                      className={`hidden h-8 px-1.5 lg:inline-flex lg:px-2 hover:text-white ${
                        plan === "premium"
                          ? "text-amber-200 hover:bg-amber-500/10"
                          : "text-cyan-200 hover:bg-cyan-500/10"
                      }`}
                    >
                      <Crown className="h-4 w-4" />
                    </Button>
                    <Button
                      type="button"
                      variant="ghost"
                      onClick={() => setHistoryOpen(true)}
                      className="hidden h-8 px-1.5 text-slate-300 hover:bg-white/10 hover:text-white lg:inline-flex lg:px-2"
                    >
                      <History className="h-4 w-4" />
                    </Button>
                    <Button
                      type="button"
                      variant="ghost"
                      onClick={signOut}
                      className="hidden h-8 px-1.5 text-slate-300 hover:bg-white/10 hover:text-white lg:inline-flex lg:px-2"
                    >
                      <LogOut className="h-4 w-4" />
                    </Button>
                  </>
                ) : (
                  <>
                    <Popover>
                      <PopoverTrigger asChild>
                        <Button
                          type="button"
                          variant="ghost"
                          className="h-8 px-1.5 text-slate-200 hover:bg-white/10 hover:text-white lg:hidden"
                        >
                          <Menu className="h-4 w-4" />
                        </Button>
                      </PopoverTrigger>
                      <PopoverContent
                        align="end"
                        className="w-56 rounded-2xl border border-white/10 bg-slate-950/96 p-2 text-white shadow-2xl lg:hidden"
                      >
                        <Button
                          type="button"
                          variant="ghost"
                          onClick={() => {
                            document.getElementById("auth-panel")?.scrollIntoView({ behavior: "smooth", block: "center" })
                          }}
                          className="flex h-9 w-full items-center justify-start gap-2 rounded-xl px-3 text-blue-100 hover:bg-blue-500/10 hover:text-blue-50"
                        >
                          <Sparkles className="h-4 w-4 text-blue-300" />
                          <span>Sign In / Sign Up</span>
                        </Button>
                      </PopoverContent>
                    </Popover>
                    <button
                      type="button"
                      onClick={() => {
                        document.getElementById("auth-panel")?.scrollIntoView({ behavior: "smooth", block: "center" })
                      }}
                      className="hidden items-center gap-1 rounded-full border border-blue-400/20 bg-blue-500/10 px-3 py-1.5 text-xs font-medium text-blue-100 transition-colors hover:bg-blue-500/20 lg:inline-flex"
                    >
                      <Sparkles className="h-3.5 w-3.5 text-blue-300" />
                      <span>Sign In / Sign Up</span>
                    </button>
                  </>
                )}
              </div>
            </div>
          </header>
          </>
  )
}
