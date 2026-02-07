'use client'

import { Lock, ArrowRight, Share2, Star, Crown } from 'lucide-react'
import { Button } from '@/components/ui/button'

interface TeaserScore {
  label: string
  score: number | null
  color: string
}

interface TeaserResultsProps {
  url: string
  scores: {
    overall: number
    performance?: number
    seo?: number
    security?: number
    gdpr?: number
    accessibility?: number
  }
  issuesCount: number
  onSelectPackage: () => void
}

const getScoreColor = (score: number) => {
  if (score >= 80) return 'text-green-500 border-green-500'
  if (score >= 60) return 'text-yellow-500 border-yellow-500'
  if (score >= 40) return 'text-orange-500 border-orange-500'
  return 'text-red-500 border-red-500'
}

const getScoreBg = (score: number) => {
  if (score >= 80) return 'bg-green-50'
  if (score >= 60) return 'bg-yellow-50'
  if (score >= 40) return 'bg-orange-50'
  return 'bg-red-50'
}

function ScoreGauge({ score, label, size = 'normal' }: { score: number | null; label: string; size?: 'large' | 'normal' }) {
  if (score === null) return null

  const sizeClasses = size === 'large'
    ? 'w-28 h-28 text-4xl'
    : 'w-20 h-20 text-2xl'

  return (
    <div className="flex flex-col items-center">
      <div className={`${sizeClasses} rounded-full border-4 ${getScoreColor(score)} ${getScoreBg(score)} flex items-center justify-center font-bold`}>
        {score}
      </div>
      <span className="mt-2 text-sm text-gray-600 font-medium">{label}</span>
    </div>
  )
}

// Fake blurred issues for teaser effect
const FAKE_ISSUES = [
  { severity: 'critical', title: 'Security vulnerability detected in...', category: 'Security' },
  { severity: 'high', title: 'Missing meta description on 5 pages...', category: 'SEO' },
  { severity: 'medium', title: 'Images not optimized, causing slow...', category: 'Performance' },
  { severity: 'high', title: 'Cookie consent banner missing GDPR...', category: 'GDPR' },
  { severity: 'medium', title: 'Insufficient color contrast on buttons...', category: 'Accessibility' },
]

const severityColors = {
  critical: 'bg-red-100 border-red-300',
  high: 'bg-orange-100 border-orange-300',
  medium: 'bg-yellow-100 border-yellow-300',
}

export default function TeaserResults({
  url,
  scores,
  issuesCount,
  onSelectPackage
}: TeaserResultsProps) {
  const scoreItems: TeaserScore[] = [
    { label: 'Performance', score: scores.performance ?? null, color: 'orange' },
    { label: 'SEO', score: scores.seo ?? null, color: 'blue' },
    { label: 'Security', score: scores.security ?? null, color: 'green' },
    { label: 'GDPR', score: scores.gdpr ?? null, color: 'purple' },
    { label: 'Accessibility', score: scores.accessibility ?? null, color: 'cyan' },
  ].filter(s => s.score !== null)

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="text-center">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Audit Complete!</h2>
        <p className="text-gray-600">
          Results for <span className="font-medium text-primary-600">{url}</span>
        </p>
      </div>

      {/* Overall Score */}
      <div className="flex justify-center">
        <div className="bg-white rounded-2xl shadow-lg p-8 text-center">
          <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wide mb-4">
            Overall Score
          </h3>
          <ScoreGauge score={scores.overall} label="" size="large" />
          <p className={`mt-4 font-semibold ${getScoreColor(scores.overall).split(' ')[0]}`}>
            {scores.overall >= 80 ? 'Excellent!' :
             scores.overall >= 60 ? 'Good, but room for improvement' :
             scores.overall >= 40 ? 'Needs attention' :
             'Critical issues found'}
          </p>
        </div>
      </div>

      {/* Individual Scores */}
      <div className="bg-white rounded-xl shadow-lg p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-6 text-center">
          Category Scores
        </h3>
        <div className="flex justify-center gap-8 flex-wrap">
          {scoreItems.map((item) => (
            <ScoreGauge
              key={item.label}
              score={item.score}
              label={item.label}
            />
          ))}
        </div>
      </div>

      {/* Blurred Issues Preview */}
      <div className="bg-white rounded-xl shadow-lg p-6 relative overflow-hidden">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">
            Issues Found: {issuesCount}
          </h3>
          <span className="text-sm text-gray-500">Preview</span>
        </div>

        <div className="space-y-3 relative">
          {FAKE_ISSUES.slice(0, Math.min(5, issuesCount)).map((issue, idx) => (
            <div
              key={idx}
              className={`p-3 rounded-lg border ${severityColors[issue.severity as keyof typeof severityColors]} blur-[2px]`}
            >
              <div className="flex items-center justify-between">
                <div>
                  <span className="text-xs font-medium uppercase">{issue.severity}</span>
                  <span className="text-xs text-gray-500 ml-2">{issue.category}</span>
                </div>
              </div>
              <p className="text-sm text-gray-700 mt-1">{issue.title}</p>
            </div>
          ))}

          {/* Overlay */}
          <div className="absolute inset-0 bg-gradient-to-b from-transparent via-white/80 to-white flex items-end justify-center pb-4">
            <div className="text-center">
              <Lock className="w-8 h-8 text-gray-400 mx-auto mb-2" />
              <p className="text-gray-600 font-medium">Unlock full report to see all issues</p>
            </div>
          </div>
        </div>
      </div>

      {/* Package Selection CTA */}
      <div className="bg-gradient-to-r from-primary-500 to-primary-600 rounded-xl p-6 text-white">
        <div className="text-center mb-6">
          <h3 className="text-xl font-bold mb-2">Get Your Full Audit Report</h3>
          <p className="text-primary-100">
            Unlock detailed issues, recommendations, and AI-powered insights
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          {/* Starter */}
          <div className="bg-white/10 rounded-lg p-4 backdrop-blur">
            <div className="flex items-center gap-2 mb-2">
              <Share2 className="w-5 h-5" />
              <span className="font-semibold">Starter</span>
            </div>
            <div className="text-2xl font-bold mb-1">FREE</div>
            <p className="text-sm text-primary-100">2 audit types, share to unlock</p>
          </div>

          {/* Pro */}
          <div className="bg-white/20 rounded-lg p-4 backdrop-blur border-2 border-white/40 relative">
            <div className="absolute -top-2 left-1/2 -translate-x-1/2">
              <span className="bg-yellow-400 text-yellow-900 text-xs font-bold px-2 py-0.5 rounded-full flex items-center gap-1">
                <Star className="w-3 h-3" /> POPULAR
              </span>
            </div>
            <div className="flex items-center gap-2 mb-2">
              <Star className="w-5 h-5" />
              <span className="font-semibold">Pro</span>
            </div>
            <div className="text-2xl font-bold mb-1">€1.99</div>
            <p className="text-sm text-primary-100">4 audit types + PDF report</p>
          </div>

          {/* Full */}
          <div className="bg-white/10 rounded-lg p-4 backdrop-blur">
            <div className="flex items-center gap-2 mb-2">
              <Crown className="w-5 h-5" />
              <span className="font-semibold">Full</span>
            </div>
            <div className="text-2xl font-bold mb-1">€4.99</div>
            <p className="text-sm text-primary-100">All 6 types + Pro PDF + AI</p>
          </div>
        </div>

        <Button
          onClick={onSelectPackage}
          size="lg"
          className="w-full bg-white text-primary-600 hover:bg-gray-100 font-semibold"
        >
          Choose Your Package
          <ArrowRight className="w-5 h-5 ml-2" />
        </Button>
      </div>
    </div>
  )
}
