import { notFound } from "next/navigation"

import SeoGuidePage from "@/components/SeoGuidePage"
import { getGuidePageBySlug, guidePages } from "@/lib/seo-content"
import { buildPageMetadata } from "@/lib/site"

type GuidePageProps = {
  params: Promise<{ slug: string }>
}

export async function generateStaticParams() {
  return guidePages.map((page) => ({ slug: page.slug }))
}

export async function generateMetadata({ params }: GuidePageProps) {
  const { slug } = await params
  const page = getGuidePageBySlug(slug)

  if (!page) {
    return {}
  }

  return buildPageMetadata({
    title: page.title,
    description: page.description,
    path: page.path,
    keywords: ["vedic astrology guide", page.title.toLowerCase()],
  })
}

export default async function GuidePage({ params }: GuidePageProps) {
  const { slug } = await params
  const page = getGuidePageBySlug(slug)

  if (!page) {
    notFound()
  }

  return <SeoGuidePage page={page} />
}
