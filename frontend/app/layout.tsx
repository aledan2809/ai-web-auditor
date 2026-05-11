import type { Metadata } from 'next'
import './globals.css'
import { Navigation } from './navigation'
import { Providers } from './providers'

export const metadata: Metadata = {
  title: 'AI Web Auditor',
  description: 'Complete website audit platform',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="min-h-screen bg-gray-50">
        <a
          href="#main-content"
          className="sr-only focus:not-sr-only focus:absolute focus:top-2 focus:left-2 focus:z-50 focus:px-4 focus:py-2 focus:bg-white focus:text-primary-600 focus:rounded focus:shadow"
        >
          Skip to main content
        </a>
        <Providers>
          <Navigation />
          <main id="main-content" className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            {children}
          </main>
        </Providers>
      </body>
    </html>
  )
}
