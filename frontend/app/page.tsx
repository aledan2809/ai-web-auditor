'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Search, Loader2, Shield, Zap, Eye, FileText, Lock, Globe } from 'lucide-react'
import { auditApi } from '@/lib/api'

const auditTypes = [
  { id: 'full', label: 'Audit Complet', icon: Globe, description: 'Toate verificările' },
  { id: 'performance', label: 'Performance', icon: Zap, description: 'Core Web Vitals, timp de încărcare' },
  { id: 'seo', label: 'SEO', icon: Search, description: 'Meta tags, structură, sitemap' },
  { id: 'security', label: 'Security', icon: Shield, description: 'HTTPS, headers, vulnerabilități' },
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
      setError('URL invalid. Introduceți un URL valid.')
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
      setSelectedTypes(['full'])
    } else {
      setSelectedTypes(prev => {
        const newTypes = prev.filter(t => t !== 'full')
        if (newTypes.includes(typeId)) {
          return newTypes.filter(t => t !== typeId)
        }
        return [...newTypes, typeId]
      })
    }
  }

  return (
    <div className="max-w-4xl mx-auto">
      {/* Hero */}
      <div className="text-center mb-12">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          Audit Complet pentru Website-ul Tău
        </h1>
        <p className="text-xl text-gray-600">
          Analizează performance, SEO, security, GDPR și accessibility într-un singur loc
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
            <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
              {auditTypes.map((type) => {
                const Icon = type.icon
                const isSelected = selectedTypes.includes(type.id) ||
                  (type.id !== 'full' && selectedTypes.includes('full'))

                return (
                  <button
                    key={type.id}
                    type="button"
                    onClick={() => toggleType(type.id)}
                    className={`p-4 rounded-lg border-2 text-left transition-all ${
                      isSelected
                        ? 'border-primary-500 bg-primary-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <div className="flex items-center gap-2 mb-1">
                      <Icon className={`w-5 h-5 ${isSelected ? 'text-primary-600' : 'text-gray-400'}`} />
                      <span className={`font-medium ${isSelected ? 'text-primary-700' : 'text-gray-700'}`}>
                        {type.label}
                      </span>
                    </div>
                    <p className="text-xs text-gray-500">{type.description}</p>
                  </button>
                )
              })}
            </div>
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
            disabled={isLoading || !url}
            className="w-full py-4 bg-primary-600 text-white rounded-lg font-medium hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                Se pornește auditul...
              </>
            ) : (
              <>
                <Search className="w-5 h-5" />
                Pornește Auditul
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
            Generează rapoarte profesionale pentru clienți
          </p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <Zap className="w-8 h-8 text-primary-600 mb-3" />
          <h3 className="font-semibold text-gray-900 mb-2">Estimări Preț</h3>
          <p className="text-sm text-gray-600">
            Calculează automat costul reparărilor
          </p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <Shield className="w-8 h-8 text-primary-600 mb-3" />
          <h3 className="font-semibold text-gray-900 mb-2">Recomandări AI</h3>
          <p className="text-sm text-gray-600">
            Priorități și quick wins identificate cu AI
          </p>
        </div>
      </div>
    </div>
  )
}
