import type { Metadata } from "next"

export const SITE_NAME = "Nakshatra AI"
export const SITE_URL =
  (process.env.NEXT_PUBLIC_SITE_URL || "https://nakshatra-ai.vercel.app").replace(/\/$/, "")
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

  return {
    title,
    description,
    keywords,
    alternates: {
      canonical: path,
    },
    openGraph: {
      title,
      description,
      url,
      siteName: SITE_NAME,
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
}
