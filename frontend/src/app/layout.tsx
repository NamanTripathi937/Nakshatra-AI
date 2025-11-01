// app/layout.tsx


import type { Metadata } from "next";
import Header from "../components/Header";
import Script from "next/script";
import { Geist, Geist_Mono } from "next/font/google";
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

const BASE_URL = "https://nakshatra-ai.vercel.app";

export const metadata: Metadata = {
  metadataBase: new URL(BASE_URL),
  title: {
    default: "Nakshatra AI",
    template: "%s | Nakshatra AI",
  },
  description: "Nakshatra AI — An AI project by Naman Tripathi. Explore AI tools and demos built with Next.js on Vercel.",
  keywords: [
    "nakshatra ai",
    "nakshtra-ai",
    "nakshatra by naman",
    "nakshatra-ai.vercel.app",
    "Naman Tripathi",
    "nakshatra",
    "naman astrology"
  ],
  authors: [{ name: "Naman Tripathi", url: BASE_URL }],
  creator: "Naman Tripathi",
  robots: {
    index: true,
    follow: true,
  },
  verification: {
    google: "mWLuq6bpiQgQOOg1-GIC5HUqRgzsY-kZTtNskIOeRmA",
  },
  alternates: {
    canonical: "/",
  },
  icons: {
    icon: "/favicon.png",
    apple: "/apple-touch-icon.png",
  },
  openGraph: {
    title: "Nakshatra AI — Naman",
    description:
      "Nakshatra AI — An AI project by Naman Tripathi. Explore AI tools and demos built with Next.js on Vercel.",
    url: BASE_URL,
    siteName: "Nakshatra AI",
    locale: "en_US",
    type: "website",
    // intentionally omitting images (no og.png)
  },
  twitter: {
    card: "summary",
    title: "Nakshatra AI — Naman",
    description:
      "Nakshatra AI — An AI project by Naman Tripathi. Explore AI tools and demos built with Next.js on Vercel.",
    // intentionally omitting images
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const structuredData = {
    "@context": "https://schema.org",
    "@type": "WebSite",
    url: BASE_URL,
    name: "Nakshatra AI",
    author: {
      "@type": "Person",
      name: "Naman Tripathi",
      url: BASE_URL,
    },
    potentialAction: {
      "@type": "SearchAction",
      target: `${BASE_URL}/?s={search_term_string}`,
      "query-input": "required name=search_term_string",
    },
  };

  return (
    <html lang="en">
      <head>
        <link rel="canonical" href={BASE_URL} />
        <script
          type="application/ld+json"
          // eslint-disable-next-line react/no-danger
          dangerouslySetInnerHTML={{ __html: JSON.stringify(structuredData) }}
        />
      </head>

      <body className={`${geistSans.variable} ${geistMono.variable} antialiased`}>
        {/* Load gtag.js (GA4) */}
        <Script
          src="https://www.googletagmanager.com/gtag/js?id=G-XTH048GHDB"
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

        {/* google site verification meta */}
        <meta name="google-site-verification" content="mWLuq6bpiQgQOOg1-GIC5HUqRgzsY-kZTtNskIOeRmA" />

        <div className="relative min-h-screen">
          <div className="mid-layer overflow-visible relative select-none" aria-hidden="true" />
            <Header />
          <div className="relative z-10">{children}</div>
        </div>
      </body>
    </html>
  );
}
