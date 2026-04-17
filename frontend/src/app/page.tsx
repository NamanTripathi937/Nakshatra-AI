import type { Metadata } from "next"

import KundaliPage from "../components/KundaliPage"

export const metadata: Metadata = {
  title: "Vedic Astrology Readings",
  description:
    "Explore a content-rich Vedic astrology homepage covering kundli basics, Lagna, Navamsha, dashas, and chart-aware AI readings before you sign in.",
  alternates: {
    canonical: "/",
  },
}

export default function HomePage() {
  return <KundaliPage />
}
