'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import {
  Check, Star, Zap, Crown, Share2, FileText, Clock, Shield
} from 'lucide-react'

// Package types
export interface Package {
  id: string
  name: string
  price: number
  currency: string
  auditsIncluded: number
  totalAudits: number
  features: string[]
  popular?: boolean
  requiresShare?: boolean
  pdfType?: 'none' | 'basic' | 'professional'
}

// Default packages (will be loaded from Super Admin settings in production)
const DEFAULT_PACKAGES: Package[] = [
  {
    id: 'starter',
    name: 'Starter',
    price: 0,
    currency: 'EUR',
    auditsIncluded: 2,
    totalAudits: 6,
    features: [
      'Choose 2 audit types',
      'Basic score overview',
      'Share on social media',
    ],
    requiresShare: true,
    pdfType: 'none',
  },
  {
    id: 'pro',
    name: 'Pro',
    price: 1.99,
    currency: 'EUR',
    auditsIncluded: 4,
    totalAudits: 6,
    features: [
      'Choose 4 audit types',
      'Detailed issue breakdown',
      'Basic PDF report',
      'Email delivery',
    ],
    popular: true,
    pdfType: 'basic',
  },
  {
    id: 'full',
    name: 'Full',
    price: 4.99,
    currency: 'EUR',
    auditsIncluded: 6,
    totalAudits: 6,
    features: [
      'All 6 audit types',
      'Full issue details',
      'Professional PDF report',
      'Priority support',
      'AI recommendations',
    ],
    pdfType: 'professional',
  },
]

// Audit types available
const AUDIT_TYPES = [
  { id: 'performance', name: 'Performance', icon: Zap },
  { id: 'seo', name: 'SEO', icon: FileText },
  { id: 'security', name: 'Security', icon: Shield },
  { id: 'gdpr', name: 'GDPR', icon: Shield },
  { id: 'accessibility', name: 'Accessibility', icon: Check },
  { id: 'technical', name: 'Technical', icon: Clock },
]

interface PackageSelectionProps {
  onSelect: (packageId: string, selectedAudits: string[]) => void
  packages?: Package[]
  showAuditSelection?: boolean
}

const PackageSelection = ({
  onSelect,
  packages = DEFAULT_PACKAGES,
  showAuditSelection = true
}: PackageSelectionProps) => {
  const [selectedPackage, setSelectedPackage] = useState<string | null>(null)
  const [selectedAudits, setSelectedAudits] = useState<string[]>([])

  const currentPackage = packages.find(p => p.id === selectedPackage)
  const maxAudits = currentPackage?.auditsIncluded || 0

  const toggleAudit = (auditId: string) => {
    if (selectedAudits.includes(auditId)) {
      setSelectedAudits(prev => prev.filter(id => id !== auditId))
    } else if (selectedAudits.length < maxAudits) {
      setSelectedAudits(prev => [...prev, auditId])
    }
  }

  const handleContinue = () => {
    if (!selectedPackage) return

    // For full package, select all audits automatically
    if (selectedPackage === 'full') {
      onSelect(selectedPackage, AUDIT_TYPES.map(a => a.id))
    } else {
      onSelect(selectedPackage, selectedAudits)
    }
  }

  const formatPrice = (price: number, currency: string) => {
    if (price === 0) return 'FREE'
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency,
      minimumFractionDigits: 2
    }).format(price)
  }

  return (
    <div className="space-y-8">
      {/* Package Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {packages.map((pkg) => (
          <div
            key={pkg.id}
            onClick={() => {
              setSelectedPackage(pkg.id)
              if (pkg.id === 'full') {
                setSelectedAudits(AUDIT_TYPES.map(a => a.id))
              } else {
                setSelectedAudits([])
              }
            }}
            className={`relative rounded-xl border-2 p-6 cursor-pointer transition-all ${
              selectedPackage === pkg.id
                ? 'border-primary-500 bg-primary-50 shadow-lg'
                : 'border-gray-200 hover:border-gray-300 hover:shadow'
            }`}
          >
            {/* Popular Badge */}
            {pkg.popular && (
              <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                <span className="bg-primary-500 text-white text-xs font-semibold px-3 py-1 rounded-full flex items-center gap-1">
                  <Star className="w-3 h-3" />
                  POPULAR
                </span>
              </div>
            )}

            {/* Package Icon */}
            <div className={`w-12 h-12 rounded-full flex items-center justify-center mb-4 ${
              pkg.id === 'starter' ? 'bg-gray-100' :
              pkg.id === 'pro' ? 'bg-primary-100' :
              'bg-yellow-100'
            }`}>
              {pkg.id === 'starter' && <Zap className="w-6 h-6 text-gray-600" />}
              {pkg.id === 'pro' && <Star className="w-6 h-6 text-primary-600" />}
              {pkg.id === 'full' && <Crown className="w-6 h-6 text-yellow-600" />}
            </div>

            {/* Package Name & Price */}
            <h3 className="text-xl font-bold text-gray-900">{pkg.name}</h3>
            <div className="mt-2">
              <span className="text-3xl font-bold text-gray-900">
                {formatPrice(pkg.price, pkg.currency)}
              </span>
              {pkg.price > 0 && (
                <span className="text-gray-500 text-sm ml-1">one-time</span>
              )}
            </div>

            {/* Audits Included */}
            <div className="mt-4 text-sm text-gray-600">
              <span className="font-semibold">{pkg.auditsIncluded}</span> of {pkg.totalAudits} audit types
            </div>

            {/* Features */}
            <ul className="mt-4 space-y-2">
              {pkg.features.map((feature, idx) => (
                <li key={idx} className="flex items-start gap-2 text-sm text-gray-600">
                  <Check className="w-4 h-4 text-green-500 flex-shrink-0 mt-0.5" />
                  <span>{feature}</span>
                </li>
              ))}
            </ul>

            {/* Requires Share Badge */}
            {pkg.requiresShare && (
              <div className="mt-4 flex items-center gap-2 text-xs text-gray-500 bg-gray-100 rounded-lg p-2">
                <Share2 className="w-4 h-4" />
                <span>Requires sharing on social media</span>
              </div>
            )}

            {/* Selection Indicator */}
            {selectedPackage === pkg.id && (
              <div className="absolute top-4 right-4">
                <div className="w-6 h-6 bg-primary-500 rounded-full flex items-center justify-center">
                  <Check className="w-4 h-4 text-white" />
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Audit Type Selection (for Starter and Pro) */}
      {showAuditSelection && selectedPackage && selectedPackage !== 'full' && (
        <div className="bg-gray-50 rounded-xl p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Select your audit types ({selectedAudits.length}/{maxAudits})
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            {AUDIT_TYPES.map((audit) => {
              const Icon = audit.icon
              const isSelected = selectedAudits.includes(audit.id)
              const isDisabled = !isSelected && selectedAudits.length >= maxAudits

              return (
                <button
                  key={audit.id}
                  onClick={() => toggleAudit(audit.id)}
                  disabled={isDisabled}
                  className={`p-4 rounded-lg border-2 text-left transition-all ${
                    isSelected
                      ? 'border-primary-500 bg-primary-50'
                      : isDisabled
                        ? 'border-gray-100 bg-gray-50 opacity-50 cursor-not-allowed'
                        : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <Icon className={`w-5 h-5 ${isSelected ? 'text-primary-600' : 'text-gray-400'}`} />
                    <span className={`font-medium ${isSelected ? 'text-primary-700' : 'text-gray-700'}`}>
                      {audit.name}
                    </span>
                    {isSelected && (
                      <Check className="w-4 h-4 text-primary-600 ml-auto" />
                    )}
                  </div>
                </button>
              )
            })}
          </div>
        </div>
      )}

      {/* Continue Button */}
      <div className="flex justify-center">
        <Button
          size="lg"
          onClick={handleContinue}
          disabled={!selectedPackage || (selectedPackage !== 'full' && selectedAudits.length === 0)}
          className="px-8 bg-primary-600 hover:bg-primary-700"
        >
          Continue to Registration
        </Button>
      </div>

      {/* Sample Report Links */}
      <div className="flex justify-center gap-4 text-sm">
        <button className="text-primary-600 hover:underline">
          View sample SEO report
        </button>
        <button className="text-primary-600 hover:underline">
          View sample Security report
        </button>
      </div>
    </div>
  )
}

export default PackageSelection
