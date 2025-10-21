// app/layout.tsx
import type { Metadata } from "next";
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

export const metadata: Metadata = {
  title: "Nakshatra AI",
  description: "Created by Naman Tripathi",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <head>
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
        <meta name="google-site-verification" content="mWLuq6bpiQgQOOg1-GIC5HUqRgzsY-kZTtNskIOeRmA" />
      </head>

      <body className={`${geistSans.variable} ${geistMono.variable} antialiased`}>
        {/* root relative container so absolute mid-layer can be positioned */}
        <div className="relative min-h-screen">
          {/* mid-layer: sits behind content */}
          <div className="mid-layer overflow-visible relative select-none" aria-hidden="true" />

          {/* site content should be above mid-layer */}
          <div className="relative z-10">{children}</div>
        </div>
      </body>
    </html>
  );
}
