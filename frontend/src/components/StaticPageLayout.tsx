import Link from "next/link"
import type { ReactNode } from "react"

type StaticPageLayoutProps = {
  eyebrow: string
  title: string
  intro: string
  children: ReactNode
}

export default function StaticPageLayout({
  eyebrow,
  title,
  intro,
  children,
}: StaticPageLayoutProps) {
  return (
    <main className="flex h-full flex-1 overflow-y-auto px-4 py-6 sm:px-6 lg:px-8 lg:py-8">
      <div className="mx-auto flex w-full max-w-5xl flex-col gap-6">
        <section className="overflow-hidden rounded-[2rem] border border-cyan-400/18 bg-[radial-gradient(circle_at_top_left,_rgba(34,211,238,0.16),_rgba(8,15,30,0.94)_40%,_rgba(5,10,20,0.98)_100%)] p-6 text-white shadow-[0_24px_90px_rgba(6,11,24,0.45)] sm:p-8">
          <div className="inline-flex items-center justify-center rounded-full border border-cyan-300/18 bg-cyan-400/8 px-3 py-1 leading-none text-[11px] font-semibold uppercase tracking-[0.22em] text-cyan-100">
            {eyebrow}
          </div>
          <div className="mt-5 max-w-3xl">
            <h1 className="text-3xl font-semibold leading-tight text-white sm:text-4xl">
              {title}
            </h1>
            <p className="mt-4 max-w-2xl text-sm leading-7 text-slate-200 sm:text-base">
              {intro}
            </p>
          </div>
          <div className="mt-6 flex flex-wrap gap-3 text-sm">
            <Link
              href="/"
              className="rounded-full border border-white/12 bg-white/8 px-4 py-2 text-slate-100 transition-colors hover:bg-white/14"
            >
              Back to home
            </Link>
            <Link
              href="/contact"
              className="rounded-full border border-cyan-300/16 bg-cyan-400/10 px-4 py-2 text-cyan-100 transition-colors hover:bg-cyan-400/18"
            >
              Contact
            </Link>
          </div>
        </section>

        <section className="grid gap-4 sm:gap-5">
          {children}
        </section>
      </div>
    </main>
  )
}
