import type { GuideContent, LandingPageContent } from "@/lib/seo-content"
import {
  DEFAULT_OG_IMAGE,
  SEO_LAST_MODIFIED,
  SITE_AUTHOR,
  SITE_DESCRIPTION,
  SITE_NAME,
  SITE_SUPPORT_EMAIL,
  SITE_URL,
  buildAbsoluteUrl,
} from "@/lib/site"

type BreadcrumbItem = {
  name: string
  path: string
}

type StaticPageInput = {
  title: string
  description: string
  path: string
  breadcrumbs?: BreadcrumbItem[]
}

const organizationId = `${SITE_URL}/#organization`
const websiteId = `${SITE_URL}/#website`
const webAppId = `${SITE_URL}/#web-application`

function buildImageUrl() {
  return buildAbsoluteUrl(DEFAULT_OG_IMAGE)
}

export function buildRootJsonLd() {
  return [
    {
      "@context": "https://schema.org",
      "@type": "Organization",
      "@id": organizationId,
      name: SITE_NAME,
      url: SITE_URL,
      logo: buildAbsoluteUrl("/main-logo.png"),
      email: SITE_SUPPORT_EMAIL,
      founder: {
        "@type": "Person",
        name: SITE_AUTHOR,
      },
    },
    {
      "@context": "https://schema.org",
      "@type": "WebSite",
      "@id": websiteId,
      url: SITE_URL,
      name: SITE_NAME,
      alternateName: ["Nakshatra AI Astrology", "NakshatraAI"],
      description: SITE_DESCRIPTION,
      inLanguage: "en",
      publisher: {
        "@id": organizationId,
      },
    },
    {
      "@context": "https://schema.org",
      "@type": "WebApplication",
      "@id": webAppId,
      name: SITE_NAME,
      url: SITE_URL,
      applicationCategory: "LifestyleApplication",
      operatingSystem: "Web",
      description: SITE_DESCRIPTION,
      image: buildImageUrl(),
      publisher: {
        "@id": organizationId,
      },
      offers: {
        "@type": "Offer",
        price: "0",
        priceCurrency: "INR",
        category: "Free kundli and astrology reading access",
      },
    },
  ]
}

export function buildBreadcrumbJsonLd(items: BreadcrumbItem[]) {
  return {
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    itemListElement: items.map((item, index) => ({
      "@type": "ListItem",
      position: index + 1,
      name: item.name,
      item: buildAbsoluteUrl(item.path),
    })),
  }
}

export function buildStaticPageJsonLd({
  title,
  description,
  path,
  breadcrumbs = [
    { name: "Home", path: "/" },
    { name: title, path },
  ],
}: StaticPageInput) {
  const url = buildAbsoluteUrl(path)

  return [
    buildBreadcrumbJsonLd(breadcrumbs),
    {
      "@context": "https://schema.org",
      "@type": "WebPage",
      "@id": `${url}#webpage`,
      url,
      name: title,
      description,
      inLanguage: "en",
      isPartOf: {
        "@id": websiteId,
      },
      publisher: {
        "@id": organizationId,
      },
    },
  ]
}

export function buildLandingPageJsonLd(page: LandingPageContent) {
  return buildStaticPageJsonLd({
    title: page.title,
    description: page.description,
    path: page.path,
  })
}

export function buildGuideArticleJsonLd(page: GuideContent) {
  const url = buildAbsoluteUrl(page.path)

  return [
    buildBreadcrumbJsonLd([
      { name: "Home", path: "/" },
      { name: "Guides", path: "/guides" },
      { name: page.title, path: page.path },
    ]),
    {
      "@context": "https://schema.org",
      "@type": "Article",
      "@id": `${url}#article`,
      headline: page.title,
      description: page.description,
      image: buildImageUrl(),
      url,
      mainEntityOfPage: url,
      inLanguage: "en",
      articleSection: page.eyebrow,
      keywords: page.keyTakeaways,
      datePublished: SEO_LAST_MODIFIED,
      dateModified: SEO_LAST_MODIFIED,
      author: {
        "@type": "Person",
        name: SITE_AUTHOR,
      },
      publisher: {
        "@id": organizationId,
      },
    },
  ]
}

export function buildGuidesIndexJsonLd(guides: GuideContent[]) {
  const url = buildAbsoluteUrl("/guides")

  return [
    buildBreadcrumbJsonLd([
      { name: "Home", path: "/" },
      { name: "Guides", path: "/guides" },
    ]),
    {
      "@context": "https://schema.org",
      "@type": "CollectionPage",
      "@id": `${url}#collection`,
      url,
      name: "Vedic Astrology Guides",
      description:
        "A collection of Vedic astrology and numerology guides from Nakshatra AI.",
      inLanguage: "en",
      isPartOf: {
        "@id": websiteId,
      },
      mainEntity: {
        "@type": "ItemList",
        itemListElement: guides.map((guide, index) => ({
          "@type": "ListItem",
          position: index + 1,
          name: guide.title,
          url: buildAbsoluteUrl(guide.path),
        })),
      },
    },
  ]
}
