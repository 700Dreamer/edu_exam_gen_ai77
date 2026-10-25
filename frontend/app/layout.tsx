import type { Metadata } from "next";
import { Outfit, Coming_Soon, Geist } from "next/font/google";
import "./globals.css";

const outfit = Outfit({
  subsets: ["latin"],
  variable: "--font-outfit",
});

const comingSoon = Coming_Soon({
  weight: "400",
  subsets: ["latin"],
  variable: "--font-coming-soon",
});

export const metadata: Metadata = {
  title: "Edulytics",
  description: "Enterprise Grade Educational Assessment & Analytics Dashboard",
};

import Script from "next/script";
import { cn } from "@/lib/utils";

const geist = Geist({subsets:['latin'],variable:'--font-sans'});


export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={cn(outfit.variable, comingSoon.variable, "font-sans", geist.variable)}>
      <head>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css" />
      </head>
      <body className="antialiased">
        <Script src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js" strategy="afterInteractive" />
        <Script src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/contrib/auto-render.min.js" strategy="afterInteractive" />
        {children}
      </body>
    </html>
  );
}
