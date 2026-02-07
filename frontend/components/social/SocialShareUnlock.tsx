'use client'

import { useState } from 'react'
import {
  Share2, Twitter, Facebook, Linkedin, Check, ExternalLink, Loader2
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { leadsApi } from '@/lib/api'

interface SocialShareUnlockProps {
  leadId: string
  auditUrl: string
  websiteUrl: string
  score: number
  onComplete: () => void
}

const SHARE_PLATFORMS = [
  {
    id: 'twitter',
    name: 'Twitter/X',
    icon: Twitter,
    color: 'bg-black hover:bg-gray-800',
    getShareUrl: (url: string, text: string) =>
      `https://twitter.com/intent/tweet?text=${encodeURIComponent(text)}&url=${encodeURIComponent(url)}`
  },
  {
    id: 'linkedin',
    name: 'LinkedIn',
    icon: Linkedin,
    color: 'bg-[#0A66C2] hover:bg-[#004182]',
    getShareUrl: (url: string, text: string) =>
      `https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(url)}`
  },
  {
    id: 'facebook',
    name: 'Facebook',
    icon: Facebook,
    color: 'bg-[#1877F2] hover:bg-[#0C5DC7]',
    getShareUrl: (url: string, text: string) =>
      `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(url)}&quote=${encodeURIComponent(text)}`
  }
]

export default function SocialShareUnlock({
  leadId,
  auditUrl,
  websiteUrl,
  score,
  onComplete
}: SocialShareUnlockProps) {
  const [sharedPlatform, setSharedPlatform] = useState<string | null>(null)
  const [isVerifying, setIsVerifying] = useState(false)
  const [error, setError] = useState('')

  const shareText = `I just audited my website with @AIWebAuditor and got a score of ${score}/100! Check your website's health for free:`

  const handleShare = async (platformId: string) => {
    const platform = SHARE_PLATFORMS.find(p => p.id === platformId)
    if (!platform) return

    // Open share dialog
    const shareUrl = platform.getShareUrl(auditUrl, shareText)
    const popup = window.open(
      shareUrl,
      'share',
      'width=600,height=400,location=0,menubar=0,toolbar=0'
    )

    // Track that the share popup was opened
    setSharedPlatform(platformId)
  }

  const handleVerifyShare = async () => {
    if (!sharedPlatform) return

    setIsVerifying(true)
    setError('')

    try {
      // Call API to mark social share as completed
      const response = await fetch(`/api/leads/${leadId}/social-share`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ platform: sharedPlatform })
      })

      if (response.ok) {
        onComplete()
      } else {
        setError('Failed to verify share. Please try again.')
      }
    } catch (err) {
      setError('Network error. Please try again.')
    } finally {
      setIsVerifying(false)
    }
  }

  return (
    <div className="max-w-md mx-auto">
      <div className="bg-white rounded-xl shadow-lg p-6">
        {/* Header */}
        <div className="text-center mb-6">
          <div className="w-16 h-16 bg-primary-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <Share2 className="w-8 h-8 text-primary-600" />
          </div>
          <h2 className="text-xl font-bold text-gray-900">
            Share to Unlock Your Report
          </h2>
          <p className="text-gray-600 mt-2">
            Share your audit on social media to unlock your free report
          </p>
        </div>

        {/* Share Buttons */}
        <div className="space-y-3 mb-6">
          {SHARE_PLATFORMS.map((platform) => {
            const Icon = platform.icon
            const isSelected = sharedPlatform === platform.id

            return (
              <button
                key={platform.id}
                onClick={() => handleShare(platform.id)}
                className={`w-full flex items-center justify-between p-4 rounded-lg text-white transition-all ${platform.color} ${
                  isSelected ? 'ring-2 ring-offset-2 ring-primary-500' : ''
                }`}
              >
                <div className="flex items-center gap-3">
                  <Icon className="w-5 h-5" />
                  <span className="font-medium">Share on {platform.name}</span>
                </div>
                {isSelected ? (
                  <Check className="w-5 h-5" />
                ) : (
                  <ExternalLink className="w-5 h-5 opacity-70" />
                )}
              </button>
            )
          })}
        </div>

        {/* Verify Button */}
        {sharedPlatform && (
          <div className="space-y-3">
            <p className="text-sm text-gray-600 text-center">
              After sharing, click below to unlock your report
            </p>

            {error && (
              <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
                {error}
              </div>
            )}

            <Button
              onClick={handleVerifyShare}
              disabled={isVerifying}
              className="w-full bg-green-600 hover:bg-green-700"
            >
              {isVerifying ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin mr-2" />
                  Verifying...
                </>
              ) : (
                <>
                  <Check className="w-4 h-4 mr-2" />
                  I've Shared - Unlock Report
                </>
              )}
            </Button>
          </div>
        )}

        {/* Note */}
        <p className="mt-6 text-xs text-gray-500 text-center">
          We use social sharing to keep our free tier available.
          Your share helps others discover website optimization tools.
        </p>
      </div>
    </div>
  )
}
