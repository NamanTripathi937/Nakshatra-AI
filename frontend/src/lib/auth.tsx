"use client"

import React from "react"

import { getBackendUrl } from "./utils"

export type PlanAccess = {
  plan: "free" | "premium"
  is_premium: boolean
  ads_enabled: boolean
  daily_questions_limit: number | null
  daily_questions_used: number
  daily_questions_remaining: number | null
  free_daily_questions_remaining?: number | null
  extra_questions_balance?: number | null
  features: {
    basic_kundli_summary: boolean
    full_detailed_readings: boolean
    divisional_charts: boolean
    remedies: boolean
    compatibility: boolean
    daily_transits: boolean
    pdf_report: boolean
  }
}

export type BillingSnapshot = {
  premium_until?: string | null
  has_active_premium?: boolean
  premium_days_remaining?: number | null
  extra_questions_balance?: number
  active_membership_code?: string | null
  active_membership_name?: string | null
  last_purchase_code?: string | null
  last_purchase_name?: string | null
  last_payment_at?: string | null
}

export type AuthUser = {
  id: string
  name: string
  email: string
  picture?: string | null
  plan_access: PlanAccess
  billing?: BillingSnapshot
}

type AuthContextValue = {
  user: AuthUser | null
  token: string | null
  loading: boolean
  error: string
  signInWithGoogleCredential: (credential: string) => Promise<void>
  refreshUser: () => Promise<void>
  signOut: () => void
}

const AUTH_TOKEN_KEY = "nakshatra_auth_token"
const AUTH_USER_KEY = "nakshatra_auth_user"

const AuthContext = React.createContext<AuthContextValue | null>(null)

function readLocalStorageValue(key: string) {
  if (typeof window === "undefined") return null
  return window.localStorage.getItem(key)
}

function writeLocalStorageValue(key: string, value: string) {
  if (typeof window === "undefined") return
  window.localStorage.setItem(key, value)
}

function removeLocalStorageValue(key: string) {
  if (typeof window === "undefined") return
  window.localStorage.removeItem(key)
}

async function parseApiError(response: Response, fallbackMessage: string) {
  try {
    const data = await response.json()
    if (typeof data?.detail === "string") return data.detail
    if (typeof data?.detail?.message === "string") return data.detail.message
    if (typeof data?.error === "string") return data.error
  } catch {
    // ignore JSON parse failures
  }
  return fallbackMessage
}

export function buildAuthHeaders(token: string | null, headers?: HeadersInit) {
  const base = new Headers(headers || {})
  if (token) {
    base.set("Authorization", `Bearer ${token}`)
  }
  return base
}

export function useAuth() {
  const value = React.useContext(AuthContext)
  if (!value) {
    throw new Error("useAuth must be used inside AuthProvider")
  }
  return value
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const backendUrl = React.useMemo(() => getBackendUrl(), [])
  const [token, setToken] = React.useState<string | null>(null)
  const [user, setUser] = React.useState<AuthUser | null>(null)
  const [loading, setLoading] = React.useState(true)
  const [error, setError] = React.useState("")

  const signOut = React.useCallback(() => {
    setToken(null)
    setUser(null)
    setError("")
    removeLocalStorageValue(AUTH_TOKEN_KEY)
    removeLocalStorageValue(AUTH_USER_KEY)
  }, [])

  const refreshUser = React.useCallback(async () => {
    const activeToken = token || readLocalStorageValue(AUTH_TOKEN_KEY)
    if (!activeToken) {
      setLoading(false)
      return
    }

    setLoading(true)
    try {
      const res = await fetch(`${backendUrl}/auth/me`, {
        headers: buildAuthHeaders(activeToken),
      })
      if (!res.ok) {
        const message = await parseApiError(res, "Failed to restore your account.")
        throw new Error(message)
      }
      const data = await res.json()
      setToken(activeToken)
      setUser(data.user)
      writeLocalStorageValue(AUTH_TOKEN_KEY, activeToken)
      writeLocalStorageValue(AUTH_USER_KEY, JSON.stringify(data.user))
      setError("")
    } catch (err) {
      signOut()
      setError(err instanceof Error ? err.message : "Failed to restore your account.")
    } finally {
      setLoading(false)
    }
  }, [backendUrl, signOut, token])

  const signInWithGoogleCredential = React.useCallback(
    async (credential: string) => {
      setLoading(true)
      setError("")
      try {
        const res = await fetch(`${backendUrl}/auth/google`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ credential }),
        })
        if (!res.ok) {
          const message = await parseApiError(res, "Google sign-in failed.")
          throw new Error(message)
        }
        const data = await res.json()
        setToken(data.token)
        setUser(data.user)
        writeLocalStorageValue(AUTH_TOKEN_KEY, data.token)
        writeLocalStorageValue(AUTH_USER_KEY, JSON.stringify(data.user))
      } catch (err) {
        setError(err instanceof Error ? err.message : "Google sign-in failed.")
        throw err
      } finally {
        setLoading(false)
      }
    },
    [backendUrl]
  )

  React.useEffect(() => {
    const cachedToken = readLocalStorageValue(AUTH_TOKEN_KEY)
    const cachedUser = readLocalStorageValue(AUTH_USER_KEY)
    if (cachedToken) {
      setToken(cachedToken)
    }
    if (cachedUser) {
      try {
        setUser(JSON.parse(cachedUser))
      } catch {
        removeLocalStorageValue(AUTH_USER_KEY)
      }
    }
    void refreshUser()
  }, [refreshUser])

  const value = React.useMemo<AuthContextValue>(
    () => ({
      user,
      token,
      loading,
      error,
      signInWithGoogleCredential,
      refreshUser,
      signOut,
    }),
    [error, loading, refreshUser, signInWithGoogleCredential, signOut, token, user]
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
