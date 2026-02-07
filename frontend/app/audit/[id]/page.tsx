'use client'

import { useState, useEffect } from 'react'
import { useParams } from 'next/navigation'
import {
  Loader2, CheckCircle, XCircle, AlertTriangle,
  Download, DollarSign, RefreshCw, ExternalLink, Wrench
} from 'lucide-react'
import { auditApi, estimateApi, websiteGuruApi, AuditResult, PriceEstimate } from '@/lib/api'

const severityColors = {
  critical: 'bg-red-100 text-red-800 border-red-200',
  high: 'bg-orange-100 text-orange-800 border-orange-200',
  medium: 'bg-yellow-100 text-yellow-800 border-yellow-200',
  low: 'bg-green-100 text-green-800 border-green-200',
  info: 'bg-blue-100 text-blue-800 border-blue-200',
}

const categoryLabels: Record<string, string> = {
  performance: 'Performance',
  seo: 'SEO',
  security: 'Security',
  gdpr: 'GDPR',
  accessibility: 'Accessibility',
}

function ScoreCircle({ score, label }: { score: number | null | undefined; label: string }) {
  const getColor = (s: number) => {
    if (s >= 80) return 'text-green-500'
    if (s >= 60) return 'text-yellow-500'
    if (s >= 40) return 'text-orange-500'
    return 'text-red-500'
  }

  return (
    <div className="text-center">
      <div className={`text-3xl font-bold ${score !== null && score !== undefined ? getColor(score) : 'text-gray-400'}`}>
        {score !== null && score !== undefined ? score : '-'}
      </div>
      <div className="text-sm text-gray-600">{label}</div>
    </div>
  )
}

export default function AuditPage() {
  const params = useParams()
  const auditId = params.id as string

  const [audit, setAudit] = useState<AuditResult | null>(null)
  const [estimate, setEstimate] = useState<PriceEstimate | null>(null)
  const [loading, setLoading] = useState(true)
  const [estimateLoading, setEstimateLoading] = useState(false)
  const [guruLoading, setGuruLoading] = useState(false)
  const [error, setError] = useState('')

  // Poll for audit status
  useEffect(() => {
    let interval: NodeJS.Timeout

    const fetchAudit = async () => {
      try {
        const response = await auditApi.getStatus(auditId)
        setAudit(response.data)

        if (response.data.status === 'completed' || response.data.status === 'failed') {
          setLoading(false)
          if (interval) clearInterval(interval)
        }
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Eroare la încărcarea auditului')
        setLoading(false)
        if (interval) clearInterval(interval)
      }
    }

    fetchAudit()
    interval = setInterval(fetchAudit, 2000)

    return () => {
      if (interval) clearInterval(interval)
    }
  }, [auditId])

  const handleGetEstimate = async () => {
    setEstimateLoading(true)
    try {
      const response = await estimateApi.getEstimate(auditId)
      setEstimate(response.data)
    } catch (err: any) {
      console.error('Estimate error:', err)
    } finally {
      setEstimateLoading(false)
    }
  }

  const handleDownloadPdf = async () => {
    try {
      const response = await auditApi.downloadPdf(auditId)
      const blob = new Blob([response.data], { type: 'application/pdf' })
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `audit_${auditId.slice(0, 8)}.pdf`
      a.click()
      window.URL.revokeObjectURL(url)
    } catch (err) {
      console.error('Download error:', err)
    }
  }

  const handleSendToWebsiteGuru = async () => {
    if (!audit) return
    setGuruLoading(true)
    try {
      const result = await websiteGuruApi.sendAudit(audit)
      if (result.success && result.redirect_url) {
        // Open Website Guru in new tab
        const guruUrl = process.env.NEXT_PUBLIC_WEBSITE_GURU_URL || 'http://localhost:3000'
        window.open(`${guruUrl}${result.redirect_url}`, '_blank')
      } else {
        console.error('Website Guru error:', result.error)
        alert('Eroare la trimiterea catre Website Guru')
      }
    } catch (err) {
      console.error('Website Guru error:', err)
      alert('Eroare la conectarea cu Website Guru')
    } finally {
      setGuruLoading(false)
    }
  }

  if (error) {
    return (
      <div className="max-w-4xl mx-auto">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
          <XCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-red-800">{error}</h2>
        </div>
      </div>
    )
  }

  if (!audit) {
    return (
      <div className="flex justify-center items-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-primary-600" />
      </div>
    )
  }

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div className="bg-white rounded-xl shadow-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Rezultate Audit</h1>
            <a
              href={audit.url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-primary-600 hover:underline flex items-center gap-1"
            >
              {audit.url}
              <ExternalLink className="w-4 h-4" />
            </a>
          </div>
          <div className="flex items-center gap-2">
            {audit.status === 'running' && (
              <span className="flex items-center gap-2 px-3 py-1 bg-blue-100 text-blue-800 rounded-full">
                <Loader2 className="w-4 h-4 animate-spin" />
                În progres...
              </span>
            )}
            {audit.status === 'completed' && (
              <span className="flex items-center gap-2 px-3 py-1 bg-green-100 text-green-800 rounded-full">
                <CheckCircle className="w-4 h-4" />
                Completat
              </span>
            )}
            {audit.status === 'failed' && (
              <span className="flex items-center gap-2 px-3 py-1 bg-red-100 text-red-800 rounded-full">
                <XCircle className="w-4 h-4" />
                Eșuat
              </span>
            )}
          </div>
        </div>

        {/* Scores Grid */}
        {audit.status === 'completed' && (
          <div className="grid grid-cols-6 gap-4 pt-4 border-t">
            <ScoreCircle score={audit.overall_score} label="Overall" />
            <ScoreCircle score={audit.performance_score} label="Performance" />
            <ScoreCircle score={audit.seo_score} label="SEO" />
            <ScoreCircle score={audit.security_score} label="Security" />
            <ScoreCircle score={audit.gdpr_score} label="GDPR" />
            <ScoreCircle score={audit.accessibility_score} label="A11y" />
          </div>
        )}
      </div>

      {/* Actions */}
      {audit.status === 'completed' && (
        <div className="flex gap-4 flex-wrap">
          <button
            onClick={handleDownloadPdf}
            className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
          >
            <Download className="w-5 h-5" />
            Descarca PDF
          </button>
          <button
            onClick={handleGetEstimate}
            disabled={estimateLoading}
            className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
          >
            {estimateLoading ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <DollarSign className="w-5 h-5" />
            )}
            Calculeaza Pret
          </button>
          <button
            onClick={handleSendToWebsiteGuru}
            disabled={guruLoading}
            className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50"
          >
            {guruLoading ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <Wrench className="w-5 h-5" />
            )}
            Repara cu Website Guru
          </button>
        </div>
      )}

      {/* Price Estimate */}
      {estimate && (
        <div className="bg-white rounded-xl shadow-lg p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Estimare Preț</h2>

          <div className="grid grid-cols-3 gap-6 mb-6">
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="text-sm text-gray-600">Total Ore</div>
              <div className="text-2xl font-bold">{estimate.total_hours}h</div>
            </div>
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="text-sm text-gray-600">Discount</div>
              <div className="text-2xl font-bold">{estimate.discount_percent}%</div>
            </div>
            <div className="bg-green-50 rounded-lg p-4">
              <div className="text-sm text-gray-600">Preț Total</div>
              <div className="text-2xl font-bold text-green-600">
                {estimate.total_price} {estimate.currency}
              </div>
            </div>
          </div>

          {estimate.ai_summary && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
              <h3 className="font-semibold text-blue-900 mb-2">Recomandare AI</h3>
              <p className="text-blue-800">{estimate.ai_summary}</p>
            </div>
          )}

          {estimate.quick_wins.length > 0 && (
            <div className="mb-6">
              <h3 className="font-semibold text-gray-900 mb-2">Quick Wins</h3>
              <ul className="list-disc list-inside text-gray-700">
                {estimate.quick_wins.map((win, i) => (
                  <li key={i}>{win}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Issues List */}
      {audit.status === 'completed' && audit.issues.length > 0 && (
        <div className="bg-white rounded-xl shadow-lg p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4">
            Probleme Găsite ({audit.issues.length})
          </h2>

          <div className="space-y-4">
            {audit.issues.map((issue) => (
              <div
                key={issue.id}
                className={`border rounded-lg p-4 ${severityColors[issue.severity]}`}
              >
                <div className="flex items-start justify-between">
                  <div>
                    <span className="inline-block px-2 py-1 text-xs font-medium rounded uppercase mb-2">
                      {issue.severity}
                    </span>
                    <span className="ml-2 text-xs text-gray-600">
                      {categoryLabels[issue.category] || issue.category}
                    </span>
                    <h3 className="font-semibold text-gray-900">{issue.title}</h3>
                    <p className="text-sm text-gray-700 mt-1">{issue.description}</p>
                    <p className="text-sm text-gray-600 mt-2">
                      <strong>Recomandare:</strong> {issue.recommendation}
                    </p>
                  </div>
                  <div className="text-right text-sm text-gray-500">
                    <div>{issue.estimated_hours}h</div>
                    <div>{issue.complexity}</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
