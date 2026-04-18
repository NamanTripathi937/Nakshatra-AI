// app/sitemap.ts
import { MetadataRoute } from "next";
import { allSeoPaths } from "@/lib/seo-content";
import { buildAbsoluteUrl } from "@/lib/site";

export default function sitemap(): MetadataRoute.Sitemap {
  return allSeoPaths.map((path) => ({
    url: buildAbsoluteUrl(path),
    lastModified: new Date(),
    changeFrequency: path.startsWith("/guides/") ? ("monthly" as const) : ("weekly" as const),
    priority: path === "/" ? 1 : path.startsWith("/guides/") ? 0.7 : 0.85,
  }));
}
