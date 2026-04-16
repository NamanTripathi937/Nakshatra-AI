"use client"

import React from "react"
import { usePathname } from "next/navigation"

import Header from "./Header"

export default function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname()
  const isChatRoute = pathname?.startsWith("/chatWindow/")

  if (isChatRoute) {
    return (
      <div className="relative flex h-screen flex-col overflow-hidden">
        <div className="mid-layer absolute inset-0 h-screen overflow-hidden select-none" aria-hidden="true" />
        <Header />
        <div className="relative z-10 flex flex-1 flex-col overflow-hidden">
          {children}
        </div>
      </div>
    )
  }

  return (
    <div className="relative min-h-screen">
      <div className="mid-layer pointer-events-none fixed inset-0 select-none" aria-hidden="true" />
      <div className="relative z-10 flex min-h-screen flex-col">
        <Header />
        <div className="flex-1">
          {children}
        </div>
      </div>
    </div>
  )
}
