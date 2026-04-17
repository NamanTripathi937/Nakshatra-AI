"use client"

import React from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"

import Header from "./Header"

export default function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname()
  const isChatRoute = pathname?.startsWith("/chatWindow/")
  const footerLinks = [
    { href: "/about", label: "About" },
    { href: "/contact", label: "Contact" },
    { href: "/privacy", label: "Privacy" },
  ]
  const footerContent = (
    <footer className="border-t border-white/8 bg-slate-950/28 px-4 py-3 backdrop-blur-md sm:px-6">
      <div className="mx-auto flex max-w-6xl flex-col gap-2 text-xs text-slate-300 sm:flex-row sm:items-center sm:justify-between">
        <div>Made with ♥️ by Naman Tripathi</div>
        <nav className="flex flex-wrap items-center gap-3">
          {footerLinks.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className="transition-colors hover:text-white"
            >
              {link.label}
            </Link>
          ))}
        </nav>
      </div>
    </footer>
  )

  if (isChatRoute) {
    return (
      <div className="relative flex h-screen flex-col overflow-hidden">
        <div className="mid-layer absolute inset-0 h-screen overflow-hidden select-none" aria-hidden="true" />
        <Header />
        <div className="relative z-10 flex flex-1 flex-col overflow-hidden">
          {children}
        </div>
        {footerContent}
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
        {footerContent}
      </div>
    </div>
  )
}
