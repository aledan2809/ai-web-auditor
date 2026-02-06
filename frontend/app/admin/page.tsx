'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import {
  Users, FileText, CreditCard, TrendingUp,
  Loader2, AlertCircle, BarChart3
} from 'lucide-react'
import { adminApi, DashboardStats } from '@/lib/api'
import { useAuth } from '@/lib/auth'

export default function AdminDashboard() {
  const router = useRouter()
  const { user, isAuthenticated, isLoading: authLoading, checkAuth } = useAuth()
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    checkAuth()
  }, [])

  useEffect(() => {
    if (!authLoading) {
      if (!isAuthenticated) {
        router.push('/login')
      } else if (user?.role !== 'admin') {
        router.push('/')
      } else {
        loadStats()
      }
    }
  }, [authLoading, isAuthenticated, user])

  const loadStats = async () => {
    setIsLoading(true)
    try {
      const response = await adminApi.getStats()
      setStats(response.data)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Eroare la incarcarea statisticilor')
    } finally {
      setIsLoading(false)
    }
  }

  if (authLoading || isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <Loader2 className="w-8 h-8 animate-spin text-primary-600" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center gap-2 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
        <AlertCircle className="w-5 h-5" />
        <span>{error}</span>
      </div>
    )
  }

  if (!stats) return null

  return (
    <div className="max-w-6xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Dashboard Admin</h1>
        <p className="text-gray-600 mt-1">Statistici si management</p>
      </div>

      {/* Quick stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div className="bg-white rounded-xl shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Utilizatori</p>
              <p className="text-3xl font-bold text-gray-900">{stats.users.total}</p>
              <p className="text-sm text-green-600">+{stats.users.new_this_month} luna aceasta</p>
            </div>
            <div className="p-3 bg-blue-100 rounded-full">
              <Users className="w-6 h-6 text-blue-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Audituri</p>
              <p className="text-3xl font-bold text-gray-900">{stats.audits.total}</p>
              <p className="text-sm text-green-600">+{stats.audits.this_month} luna aceasta</p>
            </div>
            <div className="p-3 bg-green-100 rounded-full">
              <FileText className="w-6 h-6 text-green-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Venituri totale</p>
              <p className="text-3xl font-bold text-gray-900">{(stats.revenue.total / 100).toFixed(0)} EUR</p>
              <p className="text-sm text-green-600">+{(stats.revenue.this_month / 100).toFixed(0)} EUR luna aceasta</p>
            </div>
            <div className="p-3 bg-yellow-100 rounded-full">
              <CreditCard className="w-6 h-6 text-yellow-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Scor mediu</p>
              <p className="text-3xl font-bold text-gray-900">{stats.audits.avg_score}</p>
              <p className="text-sm text-gray-500">din 100</p>
            </div>
            <div className="p-3 bg-purple-100 rounded-full">
              <TrendingUp className="w-6 h-6 text-purple-600" />
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Audit status breakdown */}
        <div className="bg-white rounded-xl shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Status Audituri</h2>
          <div className="space-y-4">
            {Object.entries(stats.audits.by_status).map(([status, count]) => {
              const labels: Record<string, string> = {
                completed: 'Finalizate',
                running: 'In curs',
                pending: 'In asteptare',
                failed: 'Esuate'
              }
              const colors: Record<string, string> = {
                completed: 'bg-green-500',
                running: 'bg-blue-500',
                pending: 'bg-yellow-500',
                failed: 'bg-red-500'
              }
              const percentage = stats.audits.total > 0 ? (count / stats.audits.total) * 100 : 0

              return (
                <div key={status}>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-gray-600">{labels[status] || status}</span>
                    <span className="font-medium">{count}</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full ${colors[status] || 'bg-gray-500'}`}
                      style={{ width: `${percentage}%` }}
                    />
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        {/* Top issues */}
        <div className="bg-white rounded-xl shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Probleme frecvente</h2>
          <div className="space-y-3">
            {stats.top_issues.slice(0, 5).map((issue, index) => (
              <div key={index} className="flex items-center justify-between">
                <span className="text-sm text-gray-600 truncate flex-1">{issue.title}</span>
                <span className="ml-4 px-2 py-1 text-xs font-medium bg-gray-100 rounded">
                  {issue.count}
                </span>
              </div>
            ))}
            {stats.top_issues.length === 0 && (
              <p className="text-gray-500 text-sm">Nu exista date</p>
            )}
          </div>
        </div>
      </div>

      {/* Quick links */}
      <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-4">
        <Link
          href="/admin/users"
          className="bg-white rounded-lg shadow p-4 hover:shadow-md transition-shadow flex items-center gap-3"
        >
          <Users className="w-5 h-5 text-primary-600" />
          <span className="font-medium">Gestioneaza utilizatori</span>
        </Link>
        <Link
          href="/admin/audits"
          className="bg-white rounded-lg shadow p-4 hover:shadow-md transition-shadow flex items-center gap-3"
        >
          <FileText className="w-5 h-5 text-primary-600" />
          <span className="font-medium">Toate auditurile</span>
        </Link>
        <Link
          href="/admin/payments"
          className="bg-white rounded-lg shadow p-4 hover:shadow-md transition-shadow flex items-center gap-3"
        >
          <CreditCard className="w-5 h-5 text-primary-600" />
          <span className="font-medium">Istoric plati</span>
        </Link>
      </div>
    </div>
  )
}
