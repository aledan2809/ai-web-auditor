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
        <Providers>
          <Navigation />
          <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            {children}
          </main>
        </Providers>
      </body>
    </html>
  )
}
