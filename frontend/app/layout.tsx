import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'CreativePulse AI - Turn Creative Performance into Creative DNA',
  description: 'AI-powered creative intelligence platform. Connect your creative library with campaign performance to discover measurable visual patterns.',
  keywords: 'creative analytics, marketing AI, creative DNA, performance optimization, visual intelligence',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className="dark">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
      </head>
      <body className="antialiased">{children}</body>
    </html>
  )
}

