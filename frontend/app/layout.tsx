import type { Metadata } from 'next'
import './globals.css'
import { Navigation } from './navigation'

export const metadata: Metadata = {
  title: 'AI Web Auditor',
  description: 'Platforma completa de audit pentru website-uri',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="ro">
      <body className="min-h-screen bg-gray-50">
        <Navigation />
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {children}
        </main>
      </body>
    </html>
  )
}
