'use client'

import { ComparisonData } from '@/lib/api'

interface ComparisonChartProps {
  data: ComparisonData
}

const CATEGORIES = [
  { key: 'overall', label: 'Overall', color: 'bg-primary-500' },
  { key: 'performance', label: 'Performance', color: 'bg-blue-500' },
  { key: 'seo', label: 'SEO', color: 'bg-green-500' },
  { key: 'security', label: 'Security', color: 'bg-red-500' },
  { key: 'gdpr', label: 'GDPR', color: 'bg-purple-500' },
  { key: 'accessibility', label: 'Accessibility', color: 'bg-orange-500' },
]

export default function ComparisonChart({ data }: ComparisonChartProps) {
  // Get my domain from URL
  const getMyDomain = () => {
    try {
      const url = new URL(data.my_url)
      return url.hostname.replace('www.', '')
    } catch {
      return 'Your Website'
    }
  }

  // Build combined data for chart
  const allSites = [
    {
      name: getMyDomain(),
      isMe: true,
      scores: data.my_scores,
    },
    ...data.competitors.map(c => ({
      name: c.name,
      domain: c.domain,
      isMe: false,
      scores: c.scores,
      score_change: c.score_change,
    }))
  ]

  return (
    <div className="space-y-8">
      {/* Overall Score Comparison */}
      <div>
        <h3 className="text-sm font-medium text-gray-700 mb-4">Overall Score Ranking</h3>
        <div className="space-y-3">
          {allSites
            .sort((a, b) => (b.scores.overall || 0) - (a.scores.overall || 0))
            .map((site, index) => (
              <div key={site.name} className="relative">
                <div className="flex items-center gap-4">
                  {/* Rank */}
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${
                    index === 0 ? 'bg-yellow-100 text-yellow-700' :
                    index === 1 ? 'bg-gray-100 text-gray-600' :
                    index === 2 ? 'bg-orange-100 text-orange-700' :
                    'bg-gray-50 text-gray-400'
                  }`}>
                    {index + 1}
                  </div>

                  {/* Name and bar */}
                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-1">
                      <span className={`text-sm font-medium ${site.isMe ? 'text-primary-600' : 'text-gray-700'}`}>
                        {site.name}
                        {site.isMe && (
                          <span className="ml-2 text-xs bg-primary-100 text-primary-700 px-2 py-0.5 rounded-full">
                            You
                          </span>
                        )}
                      </span>
                      <span className={`text-lg font-bold ${
                        (site.scores.overall || 0) >= 80 ? 'text-green-600' :
                        (site.scores.overall || 0) >= 60 ? 'text-yellow-600' : 'text-red-600'
                      }`}>
                        {site.scores.overall || '-'}
                      </span>
                    </div>
                    {/* Progress bar */}
                    <div className="h-3 bg-gray-100 rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full ${site.isMe ? 'bg-primary-500' : 'bg-gray-400'}`}
                        style={{ width: `${site.scores.overall || 0}%` }}
                      />
                    </div>
                  </div>
                </div>
              </div>
            ))}
        </div>
      </div>

      {/* Category Breakdown */}
      <div>
        <h3 className="text-sm font-medium text-gray-700 mb-4">Category Breakdown</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200">
                <th className="text-left py-2 px-2 font-medium text-gray-600">Website</th>
                {CATEGORIES.slice(1).map(cat => (
                  <th key={cat.key} className="text-center py-2 px-2 font-medium text-gray-600">
                    {cat.label}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {allSites.map(site => (
                <tr key={site.name} className={`border-b border-gray-100 ${site.isMe ? 'bg-primary-50' : ''}`}>
                  <td className="py-3 px-2">
                    <span className={site.isMe ? 'font-medium text-primary-600' : ''}>
                      {site.name}
                    </span>
                  </td>
                  {CATEGORIES.slice(1).map(cat => {
                    const score = site.scores[cat.key as keyof typeof site.scores]
                    return (
                      <td key={cat.key} className="text-center py-3 px-2">
                        <span className={`inline-block min-w-[2rem] py-1 px-2 rounded text-sm font-medium ${
                          score === undefined || score === null ? 'text-gray-400' :
                          score >= 80 ? 'bg-green-100 text-green-700' :
                          score >= 60 ? 'bg-yellow-100 text-yellow-700' :
                          'bg-red-100 text-red-700'
                        }`}>
                          {score ?? '-'}
                        </span>
                      </td>
                    )
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Insights */}
      <div className="bg-gray-50 rounded-lg p-4">
        <h3 className="text-sm font-medium text-gray-700 mb-3">Quick Insights</h3>
        <div className="space-y-2 text-sm text-gray-600">
          {/* Find where we rank */}
          {(() => {
            const sortedByOverall = allSites
              .filter(s => s.scores.overall !== undefined)
              .sort((a, b) => (b.scores.overall || 0) - (a.scores.overall || 0))
            const myRank = sortedByOverall.findIndex(s => s.isMe) + 1
            const total = sortedByOverall.length

            if (myRank === 1) {
              return <p>🏆 Your website has the <strong>highest overall score</strong> among all competitors!</p>
            } else if (myRank <= Math.ceil(total / 2)) {
              return <p>📈 Your website ranks <strong>#{myRank} out of {total}</strong>. You're in the top half!</p>
            } else {
              return <p>📊 Your website ranks <strong>#{myRank} out of {total}</strong>. There's room for improvement.</p>
            }
          })()}

          {/* Find weakest category */}
          {(() => {
            const myScores = data.my_scores
            let weakest = { key: '', score: 100 }
            let strongest = { key: '', score: 0 }

            for (const cat of CATEGORIES.slice(1)) {
              const score = myScores[cat.key as keyof typeof myScores]
              if (score !== undefined && score !== null) {
                if (score < weakest.score) {
                  weakest = { key: cat.label, score }
                }
                if (score > strongest.score) {
                  strongest = { key: cat.label, score }
                }
              }
            }

            return (
              <>
                {weakest.key && (
                  <p>⚠️ <strong>{weakest.key}</strong> is your weakest category at {weakest.score} points.</p>
                )}
                {strongest.key && (
                  <p>💪 <strong>{strongest.key}</strong> is your strongest category at {strongest.score} points.</p>
                )}
              </>
            )
          })()}
        </div>
      </div>
    </div>
  )
}
