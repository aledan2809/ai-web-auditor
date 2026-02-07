'use client'

import { createContext, useContext, useState, useCallback, ReactNode } from 'react'

// Import translations
import en from './translations/en.json'
import ro from './translations/ro.json'
import ar from './translations/ar.json'
import de from './translations/de.json'
import es from './translations/es.json'
import fr from './translations/fr.json'
import it from './translations/it.json'

// Supported languages
export const LANGUAGES = {
  en: { name: 'English', flag: '🇬🇧', dir: 'ltr' as const },
  ro: { name: 'Romana', flag: '🇷🇴', dir: 'ltr' as const },
  ar: { name: 'العربية', flag: '🇦🇪', dir: 'rtl' as const },
  de: { name: 'Deutsch', flag: '🇩🇪', dir: 'ltr' as const },
  es: { name: 'Espanol', flag: '🇪🇸', dir: 'ltr' as const },
  fr: { name: 'Francais', flag: '🇫🇷', dir: 'ltr' as const },
  it: { name: 'Italiano', flag: '🇮🇹', dir: 'ltr' as const },
} as const

export type LanguageCode = keyof typeof LANGUAGES

// All translations
const translations: Record<LanguageCode, typeof en> = {
  en,
  ro,
  ar,
  de,
  es,
  fr,
  it,
}

// Get nested value from object using dot notation
function getNestedValue(obj: any, path: string): string {
  return path.split('.').reduce((current, key) => current?.[key], obj) ?? path
}

// Replace placeholders in string
function interpolate(str: string, params?: Record<string, string | number>): string {
  if (!params) return str
  return Object.entries(params).reduce(
    (result, [key, value]) => result.replace(new RegExp(`{${key}}`, 'g'), String(value)),
    str
  )
}

// Context type
interface I18nContextType {
  locale: LanguageCode
  setLocale: (locale: LanguageCode) => void
  t: (key: string, params?: Record<string, string | number>) => string
  dir: 'ltr' | 'rtl'
  isRTL: boolean
}

// Create context
const I18nContext = createContext<I18nContextType | null>(null)

// Provider component
interface I18nProviderProps {
  children: ReactNode
  defaultLocale?: LanguageCode
}

export function I18nProvider({ children, defaultLocale = 'en' }: I18nProviderProps) {
  const [locale, setLocaleState] = useState<LanguageCode>(() => {
    // Check for stored preference
    if (typeof window !== 'undefined') {
      const stored = localStorage.getItem('preferred-language')
      if (stored && stored in LANGUAGES) {
        return stored as LanguageCode
      }
      // Check browser language
      const browserLang = navigator.language.split('-')[0]
      if (browserLang in LANGUAGES) {
        return browserLang as LanguageCode
      }
    }
    return defaultLocale
  })

  const setLocale = useCallback((newLocale: LanguageCode) => {
    setLocaleState(newLocale)
    if (typeof window !== 'undefined') {
      localStorage.setItem('preferred-language', newLocale)
      // Update document direction for RTL support
      document.documentElement.dir = LANGUAGES[newLocale].dir
      document.documentElement.lang = newLocale
    }
  }, [])

  const t = useCallback((key: string, params?: Record<string, string | number>): string => {
    const translation = getNestedValue(translations[locale], key)
    return interpolate(translation, params)
  }, [locale])

  const value: I18nContextType = {
    locale,
    setLocale,
    t,
    dir: LANGUAGES[locale].dir,
    isRTL: LANGUAGES[locale].dir === 'rtl',
  }

  return (
    <I18nContext.Provider value={value}>
      {children}
    </I18nContext.Provider>
  )
}

// Hook
export function useTranslation() {
  const context = useContext(I18nContext)
  if (!context) {
    throw new Error('useTranslation must be used within an I18nProvider')
  }
  return context
}

// Language selector component helper
export function getLanguageOptions() {
  return Object.entries(LANGUAGES).map(([code, { name, flag }]) => ({
    value: code,
    label: `${flag} ${name}`,
  }))
}

// Export translations type for TypeScript
export type TranslationKeys = typeof en
