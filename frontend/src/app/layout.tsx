// app/layout.tsx
import type { Metadata } from "next";
import AppProviders from "../components/AppProviders";
import AppShell from "../components/AppShell";
import Script from "next/script";
import { Geist, Geist_Mono } from "next/font/google";
import { DEFAULT_OG_IMAGE, SITE_NAME, SITE_URL } from "@/lib/site";
// @ts-ignore - side-effect CSS import has no type declarations
import "./global.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

const ADSENSE_CLIENT_ID = process.env.NEXT_PUBLIC_ADSENSE_CLIENT_ID
const BING_SITE_VERIFICATION = process.env.NEXT_PUBLIC_BING_SITE_VERIFICATION
const GOOGLE_SITE_VERIFICATION =
  process.env.NEXT_PUBLIC_GOOGLE_SITE_VERIFICATION ||
  "mWLuq6bpiQgQOOg1-GIC5HUqRgzsY-kZTtNskIOeRmA"

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: {
    default: SITE_NAME,
    template: "%s | Nakshatra AI",
  },
  description:
    "Free kundli, numerology, AI Vedic astrology readings, Navamsa insights, Vimshottari dasha timing, kundli matching, and chart-based guidance rooted in classical Jyotish logic.",
  keywords: [
    "nakshatra ai",
    "free kundli",
    "numerology calculator",
    "vedic astrology",
    "ai vedic astrologer",
    "kundli matching",
    "navamsa chart",
    "vimshottari dasha",
    "panchang",
    "mangal dosh",
  ],
  authors: [{ name: "Naman Tripathi", url: SITE_URL }],
  creator: "Naman Tripathi",
  publisher: SITE_NAME,
  robots: {
    index: true,
    follow: true,
  },
  verification: {
    google: GOOGLE_SITE_VERIFICATION,
  },
  icons: {
    icon: "/favicon.png",
  },
  openGraph: {
    title: `${SITE_NAME} — Free Kundli & AI Vedic Astrology Reading`,
    description:
      "Generate a free kundli, calculate numerology, ask chart-aware Vedic astrology questions, and explore Navamsa, dasha timing, and compatibility guidance from one saved reading flow.",
    url: SITE_URL,
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
    title: `${SITE_NAME} — Free Kundli & AI Vedic Astrology Reading`,
    description:
      "Generate a free kundli, calculate numerology, ask chart-aware Vedic astrology questions, and explore Navamsa, dasha timing, and compatibility guidance.",
    images: [DEFAULT_OG_IMAGE],
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const structuredData = [
    {
      "@context": "https://schema.org",
      "@type": "WebSite",
      url: SITE_URL,
      name: SITE_NAME,
      description:
        "Free kundli generation, numerology, and chart-aware AI Vedic astrology readings focused on Lagna, Navamsa, dashas, remedies, and compatibility.",
    },
    {
      "@context": "https://schema.org",
      "@type": "Organization",
      name: SITE_NAME,
      url: SITE_URL,
      founder: {
        "@type": "Person",
        name: "Naman Tripathi",
      },
    },
  ];

  return (
    <html lang="en">
      <head suppressHydrationWarning>
        {ADSENSE_CLIENT_ID ? (
          <script
            async
            src={`https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=${ADSENSE_CLIENT_ID}`}
            crossOrigin="anonymous"
          />
        ) : null}
        {BING_SITE_VERIFICATION ? (
          <meta name="msvalidate.01" content={BING_SITE_VERIFICATION} />
        ) : null}
      </head>

      <body className={`${geistSans.variable} ${geistMono.variable} antialiased`}>
        {/* Load gtag.js (GA4) */}
        <Script
          src="https://www.googletagmanager.com/gtag/js?id=G-XTH048GHDB"
          strategy="afterInteractive"
        />
        <Script
          src="https://accounts.google.com/gsi/client"
          strategy="afterInteractive"
        />
        {/* Initialize gtag */}
        <Script id="gtag-init" strategy="afterInteractive">
          {`
            window.dataLayer = window.dataLayer || [];
            function gtag(){dataLayer.push(arguments);}
            gtag('js', new Date());
            gtag('config', 'G-XTH048GHDB');
          `}
        </Script>

        <AppProviders>
          <AppShell>{children}</AppShell>
        </AppProviders>
        <script
          type="application/ld+json"
          // eslint-disable-next-line react/no-danger
          dangerouslySetInnerHTML={{ __html: JSON.stringify(structuredData) }}
        />
      </body>
    </html>
  );
}
