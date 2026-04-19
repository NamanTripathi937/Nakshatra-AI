"use client"

import React from "react"

import { formatDistanceToNow } from "date-fns"
import { useRouter } from "next/navigation"
import { CalendarDays, Clock3, History, Loader2, MessageSquareText, Sparkles, X } from "lucide-react"

import { buildAuthHeaders, useAuth } from "@/lib/auth"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { ScrollArea } from "@/components/ui/scroll-area"

type AccountHistoryProps = {
  backendUrl: string
  open?: boolean
  onClose?: () => void
  variant?: "modal" | "embedded"
  limit?: number
}

type SessionHistoryItem = {
  session_id: string
  full_name: string
  has_birth_details: boolean
  birth_date?: {
    year?: number
    month?: number
    date?: number
  } | null
  message_count: number
  last_message_preview: string
  last_message_role?: string | null
  created_at?: string | null
  updated_at?: string | null
  plan_snapshot: "free" | "premium"
}

type SessionHistoryResponse = {
  sessions: SessionHistoryItem[]
}

type CachedSessionHistory = {
  fetchedAt: number
  sessions: SessionHistoryItem[]
}

const HISTORY_CACHE_PREFIX = "nakshatra_session_history"
const pendingHistoryRequests = new Map<string, Promise<SessionHistoryItem[]>>()
const memoryHistoryCache = new Map<string, CachedSessionHistory>()

function buildHistoryCacheKey(userId: string, limit?: number) {
  return `${HISTORY_CACHE_PREFIX}:${userId}:${typeof limit === "number" ? limit : "all"}`
}

function readCachedHistory(cacheKey: string) {
  const memoryValue = memoryHistoryCache.get(cacheKey)
  if (memoryValue) return memoryValue
  if (typeof window === "undefined") return null

  try {
    const rawValue = window.localStorage.getItem(cacheKey)
    if (!rawValue) return null
    const parsed = JSON.parse(rawValue) as CachedSessionHistory
    if (!Array.isArray(parsed?.sessions)) return null
    memoryHistoryCache.set(cacheKey, parsed)
    return parsed
  } catch {
    return null
  }
}

function writeCachedHistory(cacheKey: string, sessions: SessionHistoryItem[]) {
  const payload: CachedSessionHistory = {
    fetchedAt: Date.now(),
    sessions,
  }
  memoryHistoryCache.set(cacheKey, payload)
  if (typeof window === "undefined") return
  try {
    window.localStorage.setItem(cacheKey, JSON.stringify(payload))
  } catch {
    // ignore storage failures
  }
}

async function fetchSessionHistory({
  backendUrl,
  token,
  limit,
  cacheKey,
}: {
  backendUrl: string
  token: string
  limit?: number
  cacheKey: string
}) {
  const existingRequest = pendingHistoryRequests.get(cacheKey)
  if (existingRequest) {
    return existingRequest
  }

  const requestPromise = (async () => {
    const historyUrl = new URL(`${backendUrl}/sessions`)
    if (typeof limit === "number" && limit > 0) {
      historyUrl.searchParams.set("limit", String(limit))
    }

    const res = await fetch(historyUrl.toString(), {
      headers: buildAuthHeaders(token),
    })
    if (!res.ok) {
      let message = "Failed to load your reading history."
      try {
        const data = await res.json()
        message = data?.detail?.message || data?.detail || data?.error || message
      } catch {
        // ignore parse failure
      }
      throw new Error(message)
    }

    const data: SessionHistoryResponse = await res.json()
    const sessions = data.sessions || []
    writeCachedHistory(cacheKey, sessions)
    return sessions
  })()

  pendingHistoryRequests.set(cacheKey, requestPromise)
  try {
    return await requestPromise
  } finally {
    pendingHistoryRequests.delete(cacheKey)
  }
}

function formatBirthDate(item: SessionHistoryItem) {
  const birthDate = item.birth_date
  if (!birthDate?.year || !birthDate?.month || !birthDate?.date) {
    return "Birth details saved"
  }
  return `${birthDate.date.toString().padStart(2, "0")}/${birthDate.month.toString().padStart(2, "0")}/${birthDate.year}`
}

function formatUpdatedAt(value?: string | null) {
  if (!value) return "Updated recently"
  try {
    const date = new Date(value)
    return `${formatDistanceToNow(date, { addSuffix: true })} • ${date.toLocaleString([], {
      day: "2-digit",
      month: "short",
      hour: "numeric",
      minute: "2-digit",
    })}`
  } catch {
    return "Updated recently"
  }
}

function EmptyState({ onStartNew }: { onStartNew?: () => void }) {
  return (
    <div className="rounded-3xl border border-white/10 bg-slate-950/55 p-6 text-center text-slate-300">
      <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-blue-500/10 text-blue-200">
        <History className="h-5 w-5" />
      </div>
      <div className="text-lg font-semibold text-white">No saved readings yet</div>
      <p className="mt-2 text-sm leading-6 text-slate-400">
        Once you generate your first kundli, it will appear here so you can reopen it anytime.
      </p>
      {onStartNew ? (
        <Button
          type="button"
          onClick={onStartNew}
          className="mt-4 rounded-xl bg-blue-700 text-white hover:bg-blue-600"
        >
          Start your first reading
        </Button>
      ) : null}
    </div>
  )
}

function HistoryList({
  items,
  limit,
  onOpenSession,
  openingSessionId,
}: {
  items: SessionHistoryItem[]
  limit?: number
  onOpenSession: (sessionId: string) => void
  openingSessionId?: string | null
}) {
  const visibleItems = typeof limit === "number" ? items.slice(0, limit) : items

  return (
    <div className="grid gap-3">
      {visibleItems.map((item) => (
        <button
          key={item.session_id}
          type="button"
          onClick={() => onOpenSession(item.session_id)}
          disabled={openingSessionId === item.session_id}
          className={`rounded-3xl border bg-slate-950/60 p-4 text-left transition-colors ${
            openingSessionId === item.session_id
              ? "border-cyan-400/35 bg-slate-900/90 opacity-95"
              : "border-white/10 hover:border-cyan-400/25 hover:bg-slate-900/80"
          }`}
        >
          <div className="flex items-start justify-between gap-3">
            <div>
              <div className="text-base font-semibold text-white">{item.full_name}</div>
              <div className="mt-1 flex flex-wrap items-center gap-3 text-xs text-slate-400">
                <span className="inline-flex items-center gap-1">
                  <CalendarDays className="h-3.5 w-3.5" />
                  {formatBirthDate(item)}
                </span>
                <span className="inline-flex items-center gap-1">
                  <MessageSquareText className="h-3.5 w-3.5" />
                  {item.message_count} messages
                </span>
              </div>
            </div>
            <span
              className={`rounded-full px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.16em] ${
                item.plan_snapshot === "premium"
                  ? "bg-amber-500/15 text-amber-200"
                  : "bg-slate-700/80 text-slate-200"
              }`}
            >
              {item.plan_snapshot}
            </span>
          </div>
          {openingSessionId === item.session_id ? (
            <div className="mt-3 inline-flex items-center gap-2 rounded-full border border-cyan-400/20 bg-cyan-500/10 px-3 py-1 text-xs font-medium text-cyan-100">
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
              Opening reading...
            </div>
          ) : null}
          <p className="mt-3 text-sm leading-6 text-slate-300">
            {item.last_message_preview || "Open this reading to continue the conversation."}
          </p>
          <div className="mt-3 inline-flex items-center gap-1 text-xs text-slate-500">
            <Clock3 className="h-3.5 w-3.5" />
            {formatUpdatedAt(item.updated_at)}
          </div>
        </button>
      ))}
    </div>
  )
}

export default function AccountHistory({
  backendUrl,
  open = true,
  onClose,
  variant = "embedded",
  limit,
}: AccountHistoryProps) {
  const { token, user } = useAuth()
  const router = useRouter()
  const [items, setItems] = React.useState<SessionHistoryItem[]>([])
  const [loading, setLoading] = React.useState(false)
  const [error, setError] = React.useState("")
  const [openingSessionId, setOpeningSessionId] = React.useState<string | null>(null)

  React.useEffect(() => {
    if (!open || !token || !user) return

    let cancelled = false
    const activeToken = token
    const cacheKey = buildHistoryCacheKey(user.id, limit)
    const cachedHistory = readCachedHistory(cacheKey)

    if (cachedHistory?.sessions?.length) {
      setItems(cachedHistory.sessions)
      setLoading(false)
    }

    async function loadHistory() {
      if (!cachedHistory?.sessions?.length) {
        setLoading(true)
      }
      setError("")
      try {
        const sessions = await fetchSessionHistory({
          backendUrl,
          token: activeToken,
          limit,
          cacheKey,
        })
        if (!cancelled) {
          setItems(sessions)
          for (const session of sessions.slice(0, Math.min(limit ?? sessions.length, 3))) {
            void router.prefetch(`/chatWindow/${session.session_id}`)
          }
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Failed to load your reading history.")
        }
      } finally {
        if (!cancelled) {
          setLoading(false)
        }
      }
    }

    void loadHistory()
    return () => {
      cancelled = true
    }
  }, [backendUrl, limit, open, token, user])

  const handleOpenSession = React.useCallback(
    (sessionId: string) => {
      setOpeningSessionId(sessionId)
      onClose?.()
      router.push(`/chatWindow/${sessionId}`)
    },
    [onClose, router]
  )

  const handleStartNew = React.useCallback(() => {
    onClose?.()
    router.push("/")
  }, [onClose, router])

  if (!user) return null
  if (variant === "modal" && !open) return null

  const content = (
    <>
      {loading ? (
        <div className="flex min-h-[180px] items-center justify-center text-slate-300">
          <Loader2 className="mr-3 h-5 w-5 animate-spin" />
          Loading your saved readings...
        </div>
      ) : error ? (
        <div className="rounded-3xl border border-rose-400/20 bg-rose-500/10 p-4 text-sm text-rose-100">
          {error}
        </div>
      ) : items.length === 0 ? (
        <EmptyState onStartNew={variant === "modal" ? handleStartNew : undefined} />
      ) : (
        <HistoryList
          items={items}
          limit={limit}
          onOpenSession={handleOpenSession}
          openingSessionId={openingSessionId}
        />
      )}
    </>
  )

  if (variant === "embedded") {
    return (
      <section className="rounded-3xl border border-white/10 bg-slate-950/65 p-5 text-white lg:h-[440px] lg:min-h-0">
        <div className="mb-4 flex items-start justify-between gap-3">
          <div>
            <div className="inline-flex items-center gap-2 text-sm font-semibold text-white">
              <History className="h-4 w-4 text-cyan-300" />
              Recent Readings
            </div>
          </div>
          <Button
            type="button"
            variant="outline"
            onClick={handleStartNew}
            className="border-white/12 bg-slate-900/70 text-slate-200 hover:bg-slate-800 hover:text-white"
          >
            <Sparkles className="mr-2 h-4 w-4" />
            New Reading
          </Button>
        </div>
        <ScrollArea className="lg:h-[calc(100%-4.75rem)]">
          <div className="pr-1">
            {content}
          </div>
        </ScrollArea>
      </section>
    )
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/82 p-2 backdrop-blur-sm">
      <Card className="flex h-[min(92vh,880px)] w-[min(96vw,920px)] flex-col overflow-hidden border border-white/10 bg-slate-950/95 text-white shadow-2xl">
        <div className="flex items-start justify-between gap-3 border-b border-white/10 px-5 py-4">
          <div>
            <h2 className="text-xl font-semibold text-white">Account History</h2>
            <p className="text-sm text-slate-400">
              Resume your past readings from any signed-in session.
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
        <div className="flex-1 overflow-y-auto px-4 py-4 sm:px-5">
          {content}
        </div>
      </Card>
    </div>
  )
}
