'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import {
  Plus, Trash2, RefreshCw, TrendingUp, TrendingDown,
  Globe, ArrowRight, BarChart3, Loader2
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useAuth } from '@/lib/auth'
import { competitorsApi, Competitor, ComparisonData } from '@/lib/api'
import CompetitorCard from '@/components/competitors/CompetitorCard'
import AddCompetitorModal from '@/components/competitors/AddCompetitorModal'
import ComparisonChart from '@/components/competitors/ComparisonChart'

export default function CompetitorsPage() {
  const router = useRouter()
  const { user, checkAuth } = useAuth()
  const [competitors, setCompetitors] = useState<Competitor[]>([])
  const [comparison, setComparison] = useState<ComparisonData | null>(null)
  const [loading, setLoading] = useState(true)
  const [showAddModal, setShowAddModal] = useState(false)
  const [refreshing, setRefreshing] = useState<string | null>(null)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    setLoading(true)
    try {
      const [competitorsRes, comparisonRes] = await Promise.all([
        competitorsApi.getCompetitors(),
        competitorsApi.getComparison().catch(() => null)
      ])
      setCompetitors(competitorsRes.data)
      if (comparisonRes) {
        setComparison(comparisonRes.data)
      }
    } catch (error) {
      console.error('Failed to load competitors:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleAddCompetitor = async (name: string, url: string, frequency: string) => {
    try {
      const res = await competitorsApi.addCompetitor(name, url, frequency)
      setCompetitors([res.data, ...competitors])
      setShowAddModal(false)
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Failed to add competitor')
    }
  }

  const handleDeleteCompetitor = async (id: string) => {
    if (!confirm('Are you sure you want to remove this competitor?')) return

    try {
      await competitorsApi.deleteCompetitor(id)
      setCompetitors(competitors.filter(c => c.id !== id))
    } catch (error) {
      console.error('Failed to delete competitor:', error)
    }
  }

  const handleRefreshAudit = async (id: string) => {
    setRefreshing(id)
    try {
      await competitorsApi.triggerAudit(id)
      await checkAuth() // Refresh credits
      // Reload data after a short delay
      setTimeout(loadData, 2000)
    } catch (error: any) {
      if (error.response?.status === 402) {
        alert('Insufficient credits. Please purchase more credits to audit competitors.')
      } else {
        alert(error.response?.data?.detail || 'Failed to start audit')
      }
    } finally {
      setRefreshing(null)
    }
  }

  if (loading) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-primary-600" />
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto py-8 px-4">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Competitor Monitoring</h1>
          <p className="text-gray-600 mt-1">
            Track and compare your website performance against competitors
          </p>
        </div>
        <Button
          onClick={() => setShowAddModal(true)}
          className="bg-primary-600 hover:bg-primary-700"
        >
          <Plus className="w-4 h-4 mr-2" />
          Add Competitor
        </Button>
      </div>

      {/* Comparison Overview */}
      {comparison && comparison.competitors.length > 0 && (
        <div className="bg-white rounded-xl shadow-lg p-6 mb-8">
          <h2 className="text-xl font-bold text-gray-900 mb-6">
            <BarChart3 className="w-5 h-5 inline-block mr-2 text-primary-600" />
            Score Comparison
          </h2>
          <ComparisonChart data={comparison} />
        </div>
      )}

      {/* Competitors List */}
      {competitors.length === 0 ? (
        <div className="bg-white rounded-xl shadow-lg p-12 text-center">
          <Globe className="w-16 h-16 mx-auto text-gray-300 mb-4" />
          <h3 className="text-xl font-semibold text-gray-900 mb-2">No competitors yet</h3>
          <p className="text-gray-600 mb-6">
            Start monitoring your competitors to see how your website compares
          </p>
          <Button
            onClick={() => setShowAddModal(true)}
            className="bg-primary-600 hover:bg-primary-700"
          >
            <Plus className="w-4 h-4 mr-2" />
            Add Your First Competitor
          </Button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {competitors.map(competitor => (
            <CompetitorCard
              key={competitor.id}
              competitor={competitor}
              onRefresh={() => handleRefreshAudit(competitor.id)}
              onDelete={() => handleDeleteCompetitor(competitor.id)}
              isRefreshing={refreshing === competitor.id}
            />
          ))}
        </div>
      )}

      {/* Add Competitor Modal */}
      {showAddModal && (
        <AddCompetitorModal
          onClose={() => setShowAddModal(false)}
          onAdd={handleAddCompetitor}
        />
      )}
    </div>
  )
}
