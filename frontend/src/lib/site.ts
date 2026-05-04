import type { Metadata } from "next"

export const SITE_NAME = "Nakshatra AI"
export const SITE_DESCRIPTION =
  "Generate a free kundli online, calculate numerology, ask chart-aware AI Vedic astrology questions, and explore Navamsa, Vimshottari dasha, kundli matching, panchang, and relationship timing."
export const SITE_AUTHOR = "Naman Tripathi"
export const SITE_SUPPORT_EMAIL = "namantripathi937@gmail.com"
export const SEO_LAST_MODIFIED = "2026-04-24"

const PREFERRED_SITE_URL = "https://www.nakshatra-ai.tech"

function normalizeSiteUrl(value?: string) {
  const trimmed = (value || PREFERRED_SITE_URL).replace(/\/$/, "")
  const normalized = trimmed.startsWith("http") ? trimmed : `https://${trimmed}`
  return normalized === "https://nakshatra-ai.tech" || normalized === "http://nakshatra-ai.tech"
    ? PREFERRED_SITE_URL
    : normalized.replace("http://www.nakshatra-ai.tech", PREFERRED_SITE_URL)
}

export const SITE_URL = normalizeSiteUrl(process.env.NEXT_PUBLIC_SITE_URL)
export const DEFAULT_OG_IMAGE = "/opengraph-image"

type PageMetadataInput = {
  title: string
  description: string
  path: string
  keywords?: string[]
}

export function buildAbsoluteUrl(path: string) {
  const normalizedPath = path.startsWith("/") ? path : `/${path}`
  return `${SITE_URL}${normalizedPath === "/" ? "" : normalizedPath}`
}

export function buildPageMetadata({
  title,
  description,
  path,
  keywords = [],
}: PageMetadataInput): Metadata {
  const url = buildAbsoluteUrl(path)

  const metadata: Metadata = {
    title,
    description,
    alternates: {
      canonical: url,
      languages: {
        en: url,
      },
    },
    robots: {
      index: true,
      follow: true,
      googleBot: {
        index: true,
        follow: true,
        "max-image-preview": "large",
        "max-snippet": -1,
        "max-video-preview": -1,
      },
    },
    openGraph: {
      title,
      description,
      url,
      siteName: SITE_NAME,
      locale: "en_US",
      type: "website",
      images: [
        {
          url: DEFAULT_OG_IMAGE,
          width: 1200,
          height: 630,
          alt: `${SITE_NAME} open graph image`,
        },
      ],
    },
    twitter: {
      card: "summary_large_image",
      title,
      description,
      images: [DEFAULT_OG_IMAGE],
    },
  }

  if (keywords.length > 0) {
    metadata.keywords = keywords
  }

  return metadata
}
