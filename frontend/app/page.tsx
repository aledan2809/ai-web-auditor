'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Search, Loader2, Shield, Zap, Eye, FileText, Lock, Globe } from 'lucide-react'
import { auditApi } from '@/lib/api'

const auditTypes = [
  { id: 'full', label: 'Audit Complet', icon: Globe, description: 'Toate verificarile' },
  { id: 'performance', label: 'Performance', icon: Zap, description: 'Core Web Vitals, timp de incarcare' },
  { id: 'seo', label: 'SEO', icon: Search, description: 'Meta tags, structura, sitemap' },
  { id: 'security', label: 'Security', icon: Shield, description: 'HTTPS, headers, vulnerabilitati' },
  { id: 'gdpr', label: 'GDPR', icon: Lock, description: 'Cookies, privacy, tracking' },
  { id: 'accessibility', label: 'Accessibility', icon: Eye, description: 'WCAG 2.1, screen readers' },
]

export default function HomePage() {
  const router = useRouter()
  const [url, setUrl] = useState('')
  const [selectedTypes, setSelectedTypes] = useState<string[]>(['full'])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    // Validate URL
    let validUrl = url
    if (!url.startsWith('http://') && !url.startsWith('https://')) {
      validUrl = 'https://' + url
    }

    try {
      new URL(validUrl)
    } catch {
      setError('URL invalid. Introduceti un URL valid.')
      return
    }

    setIsLoading(true)

    try {
      const response = await auditApi.start({
        url: validUrl,
        audit_types: selectedTypes,
        include_screenshots: true,
        mobile_test: true
      })

      if (response.data.success) {
        router.push(`/audit/${response.data.audit_id}`)
      } else {
        setError('Eroare la pornirea auditului')
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Eroare la conectarea cu serverul')
    } finally {
      setIsLoading(false)
    }
  }

  const toggleType = (typeId: string) => {
    if (typeId === 'full') {
      // Toggle full audit on/off
      if (selectedTypes.includes('full')) {
        // Deselect full - user wants to pick individual types
        setSelectedTypes([])
      } else {
        // Select full audit
        setSelectedTypes(['full'])
      }
    } else {
      // Individual audit types - only work when 'full' is not selected
      if (selectedTypes.includes('full')) return

      setSelectedTypes(prev => {
        if (prev.includes(typeId)) {
          return prev.filter(t => t !== typeId)
        }
        return [...prev, typeId]
      })
    }
  }

  return (
    <div className="max-w-4xl mx-auto">
      {/* Hero */}
      <div className="text-center mb-12">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          Audit Complet pentru Website-ul Tau
        </h1>
        <p className="text-xl text-gray-600">
          Analizeaza performance, SEO, security, GDPR si accessibility intr-un singur loc
        </p>
      </div>

      {/* Audit Form */}
      <div className="bg-white rounded-xl shadow-lg p-8">
        <form onSubmit={handleSubmit}>
          {/* URL Input */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              URL Website
            </label>
            <div className="relative">
              <Globe className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="text"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder="exemplu.ro sau https://exemplu.ro"
                className="w-full pl-12 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                required
              />
            </div>
          </div>

          {/* Audit Types */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-3">
              Tip Audit
            </label>

            {/* Full Audit Option */}
            <button
              type="button"
              onClick={() => toggleType('full')}
              className={`w-full p-4 rounded-lg border-2 text-left transition-all mb-4 ${
                selectedTypes.includes('full')
                  ? 'border-primary-500 bg-primary-50'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
            >
              <div className="flex items-center gap-2 mb-1">
                <Globe className={`w-5 h-5 ${selectedTypes.includes('full') ? 'text-primary-600' : 'text-gray-400'}`} />
                <span className={`font-medium ${selectedTypes.includes('full') ? 'text-primary-700' : 'text-gray-700'}`}>
                  Audit Complet
                </span>
                <span className="ml-auto text-xs bg-primary-100 text-primary-700 px-2 py-1 rounded">Recomandat</span>
              </div>
              <p className="text-xs text-gray-500">Toate verificarile: Performance, SEO, Security, GDPR, Accessibility</p>
            </button>

            {/* OR Separator */}
            <div className="flex items-center gap-4 mb-4">
              <div className="flex-1 h-px bg-gray-200"></div>
              <span className="text-sm text-gray-400 font-medium">SAU alege individual</span>
              <div className="flex-1 h-px bg-gray-200"></div>
            </div>

            {/* Individual Audit Types */}
            <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
              {auditTypes.filter(t => t.id !== 'full').map((type) => {
                const Icon = type.icon
                const isSelected = selectedTypes.includes(type.id)
                const isDisabled = selectedTypes.includes('full')

                return (
                  <button
                    key={type.id}
                    type="button"
                    onClick={() => toggleType(type.id)}
                    disabled={isDisabled}
                    className={`p-4 rounded-lg border-2 text-left transition-all ${
                      isDisabled
                        ? 'border-gray-100 bg-gray-50 opacity-50 cursor-not-allowed'
                        : isSelected
                          ? 'border-primary-500 bg-primary-50'
                          : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <div className="flex items-center gap-2 mb-1">
                      <Icon className={`w-5 h-5 ${isSelected && !isDisabled ? 'text-primary-600' : 'text-gray-400'}`} />
                      <span className={`font-medium ${isSelected && !isDisabled ? 'text-primary-700' : 'text-gray-700'}`}>
                        {type.label}
                      </span>
                    </div>
                    <p className="text-xs text-gray-500">{type.description}</p>
                  </button>
                )
              })}
            </div>

            {selectedTypes.includes('full') && (
              <p className="mt-3 text-xs text-gray-500 text-center">
                Deselecteaza "Audit Complet" pentru a alege tipuri individuale
              </p>
            )}
          </div>

          {/* Error */}
          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
              {error}
            </div>
          )}

          {/* Submit */}
          <button
            type="submit"
            disabled={isLoading || !url || selectedTypes.length === 0}
            className="w-full py-4 bg-primary-600 text-white rounded-lg font-medium hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                Se porneste auditul...
              </>
            ) : (
              <>
                <Search className="w-5 h-5" />
                Porneste Auditul
              </>
            )}
          </button>
        </form>
      </div>

      {/* Features */}
      <div className="mt-12 grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white p-6 rounded-lg shadow">
          <FileText className="w-8 h-8 text-primary-600 mb-3" />
          <h3 className="font-semibold text-gray-900 mb-2">Rapoarte PDF</h3>
          <p className="text-sm text-gray-600">
            Genereaza rapoarte profesionale pentru clienti
          </p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <Zap className="w-8 h-8 text-primary-600 mb-3" />
          <h3 className="font-semibold text-gray-900 mb-2">Estimari Pret</h3>
          <p className="text-sm text-gray-600">
            Calculeaza automat costul reparatiilor
          </p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <Shield className="w-8 h-8 text-primary-600 mb-3" />
          <h3 className="font-semibold text-gray-900 mb-2">Recomandari AI</h3>
          <p className="text-sm text-gray-600">
            Prioritati si quick wins identificate cu AI
          </p>
        </div>
      </div>
    </div>
  )
}
