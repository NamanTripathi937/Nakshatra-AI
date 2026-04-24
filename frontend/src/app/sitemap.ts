// app/sitemap.ts
import { MetadataRoute } from "next";
import { allSeoPaths } from "@/lib/seo-content";
import { SEO_LAST_MODIFIED, buildAbsoluteUrl } from "@/lib/site";

function getChangeFrequency(path: string): MetadataRoute.Sitemap[number]["changeFrequency"] {
  if (path.startsWith("/guides/")) return "monthly";
  if (path === "/privacy" || path === "/contact" || path === "/about") return "yearly";
  return "weekly";
}

function getPriority(path: string) {
  if (path === "/") return 1;
  if (path === "/free-kundli" || path === "/ai-vedic-astrologer" || path === "/numerology") {
    return 0.9;
  }
  if (path.startsWith("/guides/")) return 0.7;
  if (path === "/guides") return 0.75;
  if (path === "/privacy" || path === "/contact" || path === "/about") return 0.5;
  return 0.85;
}

export default function sitemap(): MetadataRoute.Sitemap {
  const lastModified = new Date(`${SEO_LAST_MODIFIED}T00:00:00.000Z`);

  return allSeoPaths.map((path) => ({
    url: buildAbsoluteUrl(path),
    lastModified,
    changeFrequency: getChangeFrequency(path),
    priority: getPriority(path),
  }));
}
