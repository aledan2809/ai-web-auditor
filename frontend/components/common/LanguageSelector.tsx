'use client'

import { useTranslation, LANGUAGES, LanguageCode } from '@/lib/i18n'
import { ChevronDown } from 'lucide-react'
import { useState, useRef, useEffect } from 'react'

interface LanguageSelectorProps {
  variant?: 'dropdown' | 'inline'
  showLabel?: boolean
}

export default function LanguageSelector({
  variant = 'dropdown',
  showLabel = false
}: LanguageSelectorProps) {
  const { locale, setLocale, t } = useTranslation()
  const [isOpen, setIsOpen] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const currentLang = LANGUAGES[locale]
  const languages = Object.entries(LANGUAGES) as [LanguageCode, typeof LANGUAGES[LanguageCode]][]

  if (variant === 'inline') {
    return (
      <div className="flex flex-wrap gap-2">
        {languages.map(([code, { name, flag }]) => (
          <button
            key={code}
            onClick={() => setLocale(code)}
            className={`flex items-center gap-1 px-3 py-1.5 rounded-lg text-sm transition-all ${
              locale === code
                ? 'bg-primary-100 text-primary-700 font-medium'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            <span className="text-lg">{flag}</span>
            {showLabel && <span>{name}</span>}
          </button>
        ))}
      </div>
    )
  }

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-3 py-2 rounded-lg border border-gray-200 bg-white hover:bg-gray-50 transition-colors"
      >
        <span className="text-lg">{currentLang.flag}</span>
        {showLabel && <span className="text-sm text-gray-700">{currentLang.name}</span>}
        <ChevronDown className={`w-4 h-4 text-gray-400 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {isOpen && (
        <div className="absolute top-full mt-1 right-0 bg-white rounded-lg shadow-lg border border-gray-200 py-1 min-w-[160px] z-50">
          {languages.map(([code, { name, flag }]) => (
            <button
              key={code}
              onClick={() => {
                setLocale(code)
                setIsOpen(false)
              }}
              className={`w-full flex items-center gap-3 px-4 py-2 text-left hover:bg-gray-50 ${
                locale === code ? 'bg-primary-50 text-primary-700' : 'text-gray-700'
              }`}
            >
              <span className="text-lg">{flag}</span>
              <span className="text-sm">{name}</span>
              {locale === code && (
                <span className="ml-auto text-primary-600">✓</span>
              )}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
