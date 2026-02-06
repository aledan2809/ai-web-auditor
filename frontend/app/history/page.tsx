'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import {
  Search, Filter, Eye, Trash2, RefreshCw, Download,
  ChevronLeft, ChevronRight, Loader2, AlertCircle
} from 'lucide-react'
import { auditApi, AuditListItem } from '@/lib/api'
import { useAuth } from '@/lib/auth'

export default function HistoryPage() {
  const router = useRouter()
  const { isAuthenticated, isLoading: authLoading, checkAuth } = useAuth()

  const [audits, setAudits] = useState<AuditListItem[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pages, setPages] = useState(1)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')

  // Filters
  const [urlSearch, setUrlSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [minScore, setMinScore] = useState<number | undefined>()

  useEffect(() => {
    checkAuth()
  }, [])

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/login')
    }
  }, [authLoading, isAuthenticated])

  useEffect(() => {
    if (isAuthenticated) {
      loadAudits()
    }
  }, [isAuthenticated, page, statusFilter])

  const loadAudits = async () => {
    setIsLoading(true)
    try {
      const response = await auditApi.getList(page, 20, {
        status: statusFilter || undefined,
        url_search: urlSearch || undefined,
        min_score: minScore
      })
      setAudits(response.data.audits)
      setTotal(response.data.total)
      setPages(response.data.pages)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Eroare la incarcarea auditurilor')
    } finally {
      setIsLoading(false)
    }
  }

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    setPage(1)
    loadAudits()
  }

  const handleDelete = async (auditId: string) => {
    if (!confirm('Sigur doriti sa stergeti acest audit?')) return

    try {
      await auditApi.delete(auditId)
      loadAudits()
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Eroare la stergere')
    }
  }

  const handleRerun = async (auditId: string) => {
    try {
      const response = await auditApi.rerun(auditId)
      router.push(`/audit/${response.data.audit_id}`)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Eroare la repornirea auditului')
    }
  }

  const handleDownload = async (auditId: string) => {
    try {
      const response = await auditApi.downloadPdf(auditId)
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.download = `audit_report_${auditId.slice(0, 8)}.pdf`
      link.click()
    } catch (err) {
      setError('Eroare la descarcarea PDF')
    }
  }

  const getStatusBadge = (status: string) => {
    const styles: Record<string, string> = {
      pending: 'bg-yellow-100 text-yellow-800',
      running: 'bg-blue-100 text-blue-800',
      completed: 'bg-green-100 text-green-800',
      failed: 'bg-red-100 text-red-800'
    }
    const labels: Record<string, string> = {
      pending: 'In asteptare',
      running: 'In curs',
      completed: 'Finalizat',
      failed: 'Esuat'
    }
    return (
      <span className={`px-2 py-1 text-xs font-medium rounded-full ${styles[status]}`}>
        {labels[status]}
      </span>
    )
  }

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-600'
    if (score >= 60) return 'text-yellow-600'
    if (score >= 40) return 'text-orange-600'
    return 'text-red-600'
  }

  if (authLoading) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <Loader2 className="w-8 h-8 animate-spin text-primary-600" />
      </div>
    )
  }

  return (
    <div className="max-w-6xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Istoric Audituri</h1>
        <p className="text-gray-600 mt-1">Vizualizeaza si gestioneaza auditurile anterioare</p>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow p-4 mb-6">
        <form onSubmit={handleSearch} className="flex flex-wrap gap-4 items-end">
          <div className="flex-1 min-w-[200px]">
            <label className="block text-sm font-medium text-gray-700 mb-1">Cauta URL</label>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                value={urlSearch}
                onChange={(e) => setUrlSearch(e.target.value)}
                placeholder="exemplu.ro"
                className="w-full pl-9 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
              />
            </div>
          </div>

          <div className="w-40">
            <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="w-full py-2 px-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
            >
              <option value="">Toate</option>
              <option value="completed">Finalizate</option>
              <option value="running">In curs</option>
              <option value="pending">In asteptare</option>
              <option value="failed">Esuate</option>
            </select>
          </div>

          <div className="w-32">
            <label className="block text-sm font-medium text-gray-700 mb-1">Scor minim</label>
            <input
              type="number"
              min="0"
              max="100"
              value={minScore || ''}
              onChange={(e) => setMinScore(e.target.value ? parseInt(e.target.value) : undefined)}
              placeholder="0-100"
              className="w-full py-2 px-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
            />
          </div>

          <button
            type="submit"
            className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 flex items-center gap-2"
          >
            <Filter className="w-4 h-4" />
            Filtreaza
          </button>
        </form>
      </div>

      {error && (
        <div className="flex items-center gap-2 p-4 mb-6 bg-red-50 border border-red-200 rounded-lg text-red-700">
          <AlertCircle className="w-5 h-5" />
          <span>{error}</span>
        </div>
      )}

      {/* Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="w-8 h-8 animate-spin text-primary-600" />
          </div>
        ) : audits.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-500">Nu exista audituri.</p>
            <Link href="/" className="text-primary-600 hover:text-primary-700 mt-2 inline-block">
              Porneste primul audit
            </Link>
          </div>
        ) : (
          <>
            <table className="w-full">
              <thead className="bg-gray-50 border-b">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">URL</th>
                  <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase">Scor</th>
                  <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase">Probleme</th>
                  <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase">Status</th>
                  <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase">Data</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Actiuni</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {audits.map((audit) => (
                  <tr key={audit.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4">
                      <div className="text-sm font-medium text-gray-900 truncate max-w-[250px]">
                        {audit.url}
                      </div>
                    </td>
                    <td className="px-6 py-4 text-center">
                      <span className={`text-lg font-bold ${getScoreColor(audit.overall_score)}`}>
                        {audit.overall_score}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-center text-sm text-gray-600">
                      {audit.issues_count}
                    </td>
                    <td className="px-6 py-4 text-center">
                      {getStatusBadge(audit.status)}
                    </td>
                    <td className="px-6 py-4 text-center text-sm text-gray-600">
                      {new Date(audit.created_at).toLocaleDateString('ro-RO')}
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center justify-end gap-2">
                        <Link
                          href={`/audit/${audit.id}`}
                          className="p-2 text-gray-600 hover:text-primary-600 hover:bg-gray-100 rounded"
                          title="Vizualizeaza"
                        >
                          <Eye className="w-4 h-4" />
                        </Link>
                        {audit.status === 'completed' && (
                          <button
                            onClick={() => handleDownload(audit.id)}
                            className="p-2 text-gray-600 hover:text-primary-600 hover:bg-gray-100 rounded"
                            title="Descarca PDF"
                          >
                            <Download className="w-4 h-4" />
                          </button>
                        )}
                        <button
                          onClick={() => handleRerun(audit.id)}
                          className="p-2 text-gray-600 hover:text-primary-600 hover:bg-gray-100 rounded"
                          title="Ruleaza din nou"
                        >
                          <RefreshCw className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => handleDelete(audit.id)}
                          className="p-2 text-gray-600 hover:text-red-600 hover:bg-gray-100 rounded"
                          title="Sterge"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            {/* Pagination */}
            {pages > 1 && (
              <div className="flex items-center justify-between px-6 py-3 border-t bg-gray-50">
                <p className="text-sm text-gray-600">
                  Total: {total} audituri
                </p>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setPage(p => Math.max(1, p - 1))}
                    disabled={page === 1}
                    className="p-2 rounded hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <ChevronLeft className="w-5 h-5" />
                  </button>
                  <span className="text-sm text-gray-600">
                    Pagina {page} din {pages}
                  </span>
                  <button
                    onClick={() => setPage(p => Math.min(pages, p + 1))}
                    disabled={page === pages}
                    className="p-2 rounded hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <ChevronRight className="w-5 h-5" />
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}
