'use client';
import { useState } from "react";
import { Crown, History, Home, LogOut, Sparkles } from "lucide-react";

import AccountHistory from "@/components/AccountHistory";
import BillingPlansModal from "@/components/BillingPlansModal";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/lib/auth";
import { getBackendUrl } from "@/lib/utils";

export default function Header() {
  const [historyOpen, setHistoryOpen] = useState(false)
  const [billingOpen, setBillingOpen] = useState(false)
  const { user, signOut } = useAuth()
  const plan = user?.plan_access.plan ?? "free"
  const remaining = user?.plan_access.daily_questions_remaining
  const extraQuestions = user?.plan_access.extra_questions_balance ?? 0
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
            <div className="grid grid-cols-[minmax(0,1fr)_auto_minmax(0,1fr)] items-center gap-3 px-4 py-3 sm:px-6 sm:py-4">
              <div className="flex items-center justify-start">
                <Home
                  className="h-5 w-5 shrink-0 cursor-pointer text-white hover:text-blue-400 sm:h-6 sm:w-6"
                  onClick={() => (window.location.href = '/')}
                />
              </div>

              <h1 className="text-center text-lg font-bold bg-gradient-to-r from-white to-blue-300 bg-clip-text text-transparent sm:text-2xl">
                ✦ N A K S H A T R A ✦
              </h1>

              <div className="flex items-center justify-end gap-2">
                {user ? (
                  <>
                    <div className="hidden text-right sm:block">
                      <div className="text-sm font-medium text-white">{user.name.split(" ")[0]}</div>
                      <div className="text-[11px] text-slate-400">
                        {plan === "premium"
                          ? "Premium account"
                          : extraQuestions > 0
                            ? `${remaining ?? 0} questions available (${extraQuestions} paid)`
                            : `${remaining ?? 0} free questions left today`}
                      </div>
                    </div>
                    <div
                      className={`hidden rounded-full px-2 py-1 text-[10px] font-semibold uppercase tracking-[0.16em] sm:inline-flex ${
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
                      className={`h-8 px-2 hover:text-white ${
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
                      className="h-8 px-2 text-slate-300 hover:bg-white/10 hover:text-white"
                    >
                      <History className="h-4 w-4" />
                    </Button>
                    <Button
                      type="button"
                      variant="ghost"
                      onClick={signOut}
                      className="h-8 px-2 text-slate-300 hover:bg-white/10 hover:text-white"
                    >
                      <LogOut className="h-4 w-4" />
                    </Button>
                  </>
                ) : (
                  <button
                    type="button"
                    onClick={() => {
                      document.getElementById("auth-panel")?.scrollIntoView({ behavior: "smooth", block: "center" })
                    }}
                    className="hidden items-center gap-1 rounded-full border border-blue-400/20 bg-blue-500/10 px-3 py-1.5 text-xs font-medium text-blue-100 transition-colors hover:bg-blue-500/20 sm:inline-flex"
                  >
                    <Sparkles className="h-3.5 w-3.5 text-blue-300" />
                    <span>Sign In / Sign Up</span>
                  </button>
                )}
              </div>
            </div>
          </header>
          </>
  )
}
