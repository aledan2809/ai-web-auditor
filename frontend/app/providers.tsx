'use client'

import { I18nProvider } from '@/lib/i18n'
import { ReactNode, useEffect } from 'react'

interface ProvidersProps {
  children: ReactNode
}

export function Providers({ children }: ProvidersProps) {
  // Handle initial direction setup
  useEffect(() => {
    const stored = localStorage.getItem('preferred-language')
    if (stored === 'ar') {
      document.documentElement.dir = 'rtl'
      document.documentElement.lang = 'ar'
    }
  }, [])

  return (
    <I18nProvider>
      {children}
    </I18nProvider>
  )
}
