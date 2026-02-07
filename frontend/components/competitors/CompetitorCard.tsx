'use client'

import { useState } from 'react'
import {
  Globe, RefreshCw, Trash2, TrendingUp, TrendingDown,
  ChevronDown, ChevronUp, MoreVertical, History, Pause, Play
} from 'lucide-react'
import { Competitor, competitorsApi, CompetitorAudit } from '@/lib/api'

interface CompetitorCardProps {
  competitor: Competitor
  onRefresh: () => void
  onDelete: () => void
  isRefreshing: boolean
}

function ScoreBadge({ score, label }: { score?: number; label: string }) {
  if (score === undefined || score === null) {
    return (
      <div className="text-center">
        <div className="text-sm text-gray-400">-</div>
        <div className="text-xs text-gray-400">{label}</div>
      </div>
    )
  }

  const color = score >= 80 ? 'text-green-600' : score >= 60 ? 'text-yellow-600' : 'text-red-600'

  return (
    <div className="text-center">
      <div className={`text-lg font-bold ${color}`}>{score}</div>
      <div className="text-xs text-gray-500">{label}</div>
    </div>
  )
}

export default function CompetitorCard({
  competitor,
  onRefresh,
  onDelete,
  isRefreshing
}: CompetitorCardProps) {
  const [showHistory, setShowHistory] = useState(false)
  const [history, setHistory] = useState<CompetitorAudit[]>([])
  const [loadingHistory, setLoadingHistory] = useState(false)
  const [showMenu, setShowMenu] = useState(false)

  const loadHistory = async () => {
    if (history.length > 0) {
      setShowHistory(!showHistory)
      return
    }

    setLoadingHistory(true)
    try {
      const res = await competitorsApi.getCompetitorHistory(competitor.id)
      setHistory(res.data)
      setShowHistory(true)
    } catch (error) {
      console.error('Failed to load history:', error)
    } finally {
      setLoadingHistory(false)
    }
  }

  const toggleActive = async () => {
    try {
      await competitorsApi.updateCompetitor(competitor.id, {
        is_active: !competitor.is_active
      })
      window.location.reload()
    } catch (error) {
      console.error('Failed to update competitor:', error)
    }
  }

  const hasScores = competitor.latest_overall_score !== null && competitor.latest_overall_score !== undefined

  return (
    <div className={`bg-white rounded-xl shadow-lg overflow-hidden ${!competitor.is_active ? 'opacity-60' : ''}`}>
      {/* Header */}
      <div className="p-4 border-b border-gray-100">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <h3 className="font-semibold text-gray-900 truncate">{competitor.name}</h3>
            <div className="flex items-center gap-1 text-sm text-gray-500 mt-1">
              <Globe className="w-3 h-3" />
              <span className="truncate">{competitor.domain}</span>
            </div>
          </div>

          {/* Menu */}
          <div className="relative">
            <button
              onClick={() => setShowMenu(!showMenu)}
              className="p-1 hover:bg-gray-100 rounded-lg"
            >
              <MoreVertical className="w-4 h-4 text-gray-400" />
            </button>

            {showMenu && (
              <div className="absolute right-0 mt-1 w-48 bg-white rounded-lg shadow-lg border z-10">
                <button
                  onClick={() => {
                    setShowMenu(false)
                    toggleActive()
                  }}
                  className="w-full flex items-center gap-2 px-4 py-2 text-left text-sm hover:bg-gray-50"
                >
                  {competitor.is_active ? (
                    <>
                      <Pause className="w-4 h-4" />
                      Pause Monitoring
                    </>
                  ) : (
                    <>
                      <Play className="w-4 h-4" />
                      Resume Monitoring
                    </>
                  )}
                </button>
                <button
                  onClick={() => {
                    setShowMenu(false)
                    loadHistory()
                  }}
                  className="w-full flex items-center gap-2 px-4 py-2 text-left text-sm hover:bg-gray-50"
                >
                  <History className="w-4 h-4" />
                  View History
                </button>
                <button
                  onClick={() => {
                    setShowMenu(false)
                    onDelete()
                  }}
                  className="w-full flex items-center gap-2 px-4 py-2 text-left text-sm text-red-600 hover:bg-red-50"
                >
                  <Trash2 className="w-4 h-4" />
                  Remove
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Score change indicator */}
        {competitor.score_change !== 0 && (
          <div className={`flex items-center gap-1 text-sm mt-2 ${
            competitor.score_change > 0 ? 'text-green-600' : 'text-red-600'
          }`}>
            {competitor.score_change > 0 ? (
              <TrendingUp className="w-4 h-4" />
            ) : (
              <TrendingDown className="w-4 h-4" />
            )}
            <span>
              {competitor.score_change > 0 ? '+' : ''}{competitor.score_change} since last audit
            </span>
          </div>
        )}
      </div>

      {/* Scores */}
      <div className="p-4">
        {hasScores ? (
          <>
            {/* Overall Score */}
            <div className="text-center mb-4">
              <div className={`text-4xl font-bold ${
                (competitor.latest_overall_score || 0) >= 80 ? 'text-green-600' :
                (competitor.latest_overall_score || 0) >= 60 ? 'text-yellow-600' : 'text-red-600'
              }`}>
                {competitor.latest_overall_score}
              </div>
              <div className="text-sm text-gray-500">Overall Score</div>
            </div>

            {/* Category Scores */}
            <div className="grid grid-cols-5 gap-2">
              <ScoreBadge score={competitor.latest_performance_score} label="Perf" />
              <ScoreBadge score={competitor.latest_seo_score} label="SEO" />
              <ScoreBadge score={competitor.latest_security_score} label="Sec" />
              <ScoreBadge score={competitor.latest_gdpr_score} label="GDPR" />
              <ScoreBadge score={competitor.latest_accessibility_score} label="A11y" />
            </div>
          </>
        ) : (
          <div className="text-center py-4 text-gray-500">
            <p>No audit data yet</p>
            <p className="text-sm">Click refresh to start an audit</p>
          </div>
        )}
      </div>

      {/* Actions */}
      <div className="px-4 pb-4">
        <div className="flex items-center gap-2">
          <button
            onClick={onRefresh}
            disabled={isRefreshing}
            className={`flex-1 flex items-center justify-center gap-2 px-4 py-2 rounded-lg text-sm font-medium ${
              isRefreshing
                ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                : 'bg-primary-600 text-white hover:bg-primary-700'
            }`}
          >
            <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`} />
            {isRefreshing ? 'Auditing...' : 'Refresh Audit'}
          </button>
        </div>

        {competitor.last_audit_at && (
          <p className="text-xs text-gray-400 text-center mt-2">
            Last audit: {new Date(competitor.last_audit_at).toLocaleDateString()}
          </p>
        )}
      </div>

      {/* History Panel */}
      {showHistory && (
        <div className="border-t border-gray-100 p-4 bg-gray-50">
          <div className="flex items-center justify-between mb-3">
            <h4 className="font-medium text-gray-900">Audit History</h4>
            <button onClick={() => setShowHistory(false)}>
              <ChevronUp className="w-4 h-4 text-gray-400" />
            </button>
          </div>

          {history.length === 0 ? (
            <p className="text-sm text-gray-500">No history available</p>
          ) : (
            <div className="space-y-2 max-h-40 overflow-y-auto">
              {history.map(audit => (
                <div
                  key={audit.id}
                  className="flex items-center justify-between text-sm p-2 bg-white rounded-lg"
                >
                  <span className="text-gray-600">
                    {new Date(audit.created_at).toLocaleDateString()}
                  </span>
                  <div className="flex items-center gap-2">
                    <span className={`font-medium ${
                      audit.overall_score >= 80 ? 'text-green-600' :
                      audit.overall_score >= 60 ? 'text-yellow-600' : 'text-red-600'
                    }`}>
                      {audit.overall_score}
                    </span>
                    {audit.score_change !== 0 && (
                      <span className={audit.score_change > 0 ? 'text-green-600' : 'text-red-600'}>
                        ({audit.score_change > 0 ? '+' : ''}{audit.score_change})
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
