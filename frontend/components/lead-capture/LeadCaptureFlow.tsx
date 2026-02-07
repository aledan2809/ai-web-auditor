'use client'

import { useState, useEffect, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import {
  Globe, Search, Loader2, ArrowLeft, CheckCircle
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { auditApi, leadsApi, AuditResult } from '@/lib/api'
import TeaserResults from '@/components/teaser/TeaserResults'
import PackageSelection, { Package } from '@/components/packages/PackageSelection'
import EnrollmentForm, { EnrollmentData } from '@/components/enrollment/EnrollmentForm'
import StripeCheckout from '@/components/payment/StripeCheckout'
import SocialShareUnlock from '@/components/social/SocialShareUnlock'

// Package prices (loaded from admin settings in production)
const PACKAGE_PRICES: Record<string, { price: number; currency: string; name: string }> = {
  starter: { price: 0, currency: 'EUR', name: 'Starter' },
  pro: { price: 1.99, currency: 'EUR', name: 'Pro' },
  full: { price: 4.99, currency: 'EUR', name: 'Full' }
}

type FlowStep = 'url-input' | 'auditing' | 'teaser-results' | 'package-selection' | 'enrollment' | 'social-share' | 'payment' | 'complete'

interface LeadData {
  url: string
  auditId: string
  leadId: string
  auditResult: AuditResult | null
  selectedPackage: string
  selectedAudits: string[]
  enrollment: EnrollmentData | null
}

export default function LeadCaptureFlow() {
  const router = useRouter()
  const [step, setStep] = useState<FlowStep>('url-input')
  const [url, setUrl] = useState('')
  const [error, setError] = useState('')

  const [leadData, setLeadData] = useState<LeadData>({
    url: '',
    auditId: '',
    leadId: '',
    auditResult: null,
    selectedPackage: '',
    selectedAudits: [],
    enrollment: null
  })

  // Poll for audit status when auditing
  useEffect(() => {
    if (step !== 'auditing' || !leadData.auditId) return

    let interval: NodeJS.Timeout

    const fetchAudit = async () => {
      try {
        const response = await auditApi.getStatus(leadData.auditId)

        if (response.data.status === 'completed') {
          setLeadData(prev => ({ ...prev, auditResult: response.data }))
          setStep('teaser-results')
          if (interval) clearInterval(interval)
        } else if (response.data.status === 'failed') {
          setError('Audit failed. Please try again.')
          setStep('url-input')
          if (interval) clearInterval(interval)
        }
      } catch (err) {
        console.error('Audit poll error:', err)
      }
    }

    fetchAudit()
    interval = setInterval(fetchAudit, 2000)

    return () => {
      if (interval) clearInterval(interval)
    }
  }, [step, leadData.auditId])

  const handleUrlSubmit = async (e: React.FormEvent) => {
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
      setError('Invalid URL. Please enter a valid website address.')
      return
    }

    setLeadData(prev => ({ ...prev, url: validUrl }))
    setStep('auditing')

    try {
      // Start FREE teaser audit (all types for score preview)
      const response = await auditApi.start({
        url: validUrl,
        audit_types: ['full'],
        include_screenshots: true,
        mobile_test: true
      })

      if (response.data.success) {
        setLeadData(prev => ({ ...prev, auditId: response.data.audit_id }))
      } else {
        setError('Failed to start audit. Please try again.')
        setStep('url-input')
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Server connection error')
      setStep('url-input')
    }
  }

  const handlePackageSelect = (packageId: string, selectedAudits: string[]) => {
    setLeadData(prev => ({
      ...prev,
      selectedPackage: packageId,
      selectedAudits: selectedAudits
    }))
    setStep('enrollment')
  }

  const handleEnrollmentSubmit = async (data: EnrollmentData) => {
    setLeadData(prev => ({ ...prev, enrollment: data }))

    let createdLeadId = ''

    try {
      // Create lead in backend
      const response = await leadsApi.createLead({
        email: data.email,
        name: data.name,
        language: data.language,
        audit_id: leadData.auditId,
        package_id: leadData.selectedPackage,
        selected_audits: leadData.selectedAudits,
        signature_data: data.signatureDataUrl,
        newsletter_consent: data.newsletterConsent,
        fingerprint: data.termsAcceptance?.signatureDataUrl ? 'captured' : undefined,
        terms_hash: data.termsAcceptance?.termsVersion
      })

      if (response.data.lead_id) {
        createdLeadId = response.data.lead_id
        setLeadData(prev => ({ ...prev, leadId: createdLeadId }))
      }
    } catch (err) {
      console.error('Failed to create lead:', err)
      // Continue anyway - we don't want to block the user
    }

    // Check if payment is required
    const selectedPkg = leadData.selectedPackage
    if (selectedPkg === 'starter') {
      // Free package - requires social share
      setStep('social-share')
    } else {
      // Paid package - go to payment
      setStep('payment')
    }
  }

  const handleBack = () => {
    switch (step) {
      case 'package-selection':
        setStep('teaser-results')
        break
      case 'enrollment':
        setStep('package-selection')
        break
      case 'social-share':
        setStep('enrollment')
        break
      case 'payment':
        setStep('enrollment')
        break
      default:
        break
    }
  }

  const goToFullResults = () => {
    router.push(`/audit/${leadData.auditId}`)
  }

  // Render based on current step
  return (
    <div className="max-w-4xl mx-auto">
      {/* Progress Indicator */}
      {step !== 'url-input' && step !== 'auditing' && (
        <div className="mb-8">
          <div className="flex items-center justify-between mb-2">
            <button
              onClick={handleBack}
              className="flex items-center gap-1 text-gray-600 hover:text-gray-900 text-sm"
            >
              <ArrowLeft className="w-4 h-4" />
              Back
            </button>
            <StepIndicator currentStep={step} />
          </div>
        </div>
      )}

      {/* URL Input Step */}
      {step === 'url-input' && (
        <div className="space-y-8">
          <div className="text-center">
            <h1 className="text-4xl font-bold text-gray-900 mb-4">
              Free Website Audit
            </h1>
            <p className="text-xl text-gray-600">
              Get instant scores for Performance, SEO, Security, GDPR & Accessibility
            </p>
          </div>

          <div className="bg-white rounded-xl shadow-lg p-8">
            <form onSubmit={handleUrlSubmit}>
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Website URL
                </label>
                <div className="relative">
                  <Globe className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                  <input
                    type="text"
                    value={url}
                    onChange={(e) => setUrl(e.target.value)}
                    placeholder="example.com or https://example.com"
                    className="w-full pl-12 pr-4 py-4 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 text-lg"
                    required
                  />
                </div>
              </div>

              {error && (
                <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
                  {error}
                </div>
              )}

              <Button
                type="submit"
                size="lg"
                className="w-full py-6 text-lg bg-primary-600 hover:bg-primary-700"
              >
                <Search className="w-5 h-5 mr-2" />
                Start Free Audit
              </Button>
            </form>

            <p className="mt-4 text-center text-sm text-gray-500">
              No credit card required. Get your scores in 30 seconds.
            </p>
          </div>

          {/* Features */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <FeatureCard
              title="Instant Scores"
              description="Get your overall score and category breakdown immediately"
            />
            <FeatureCard
              title="AI-Powered Analysis"
              description="Advanced algorithms detect issues human eyes miss"
            />
            <FeatureCard
              title="Actionable Report"
              description="Clear recommendations to improve your website"
            />
          </div>
        </div>
      )}

      {/* Auditing Step */}
      {step === 'auditing' && (
        <div className="text-center py-16">
          <Loader2 className="w-16 h-16 animate-spin text-primary-600 mx-auto mb-6" />
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Analyzing Your Website</h2>
          <p className="text-gray-600 mb-4">{leadData.url}</p>
          <div className="max-w-md mx-auto">
            <div className="space-y-2">
              <AuditingStep label="Checking performance..." done />
              <AuditingStep label="Analyzing SEO..." done />
              <AuditingStep label="Testing security..." active />
              <AuditingStep label="Verifying GDPR compliance..." />
              <AuditingStep label="Checking accessibility..." />
            </div>
          </div>
        </div>
      )}

      {/* Teaser Results Step */}
      {step === 'teaser-results' && leadData.auditResult && (
        <TeaserResults
          url={leadData.url}
          scores={{
            overall: leadData.auditResult.overall_score,
            performance: leadData.auditResult.performance_score,
            seo: leadData.auditResult.seo_score,
            security: leadData.auditResult.security_score,
            gdpr: leadData.auditResult.gdpr_score,
            accessibility: leadData.auditResult.accessibility_score
          }}
          issuesCount={leadData.auditResult.issues?.length || 0}
          onSelectPackage={() => setStep('package-selection')}
        />
      )}

      {/* Package Selection Step */}
      {step === 'package-selection' && (
        <div className="space-y-6">
          <div className="text-center">
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Choose Your Report Package</h2>
            <p className="text-gray-600">Select the level of detail you need</p>
          </div>
          <PackageSelection
            onSelect={handlePackageSelect}
            showAuditSelection={true}
          />
        </div>
      )}

      {/* Enrollment Step */}
      {step === 'enrollment' && (
        <div className="max-w-2xl mx-auto">
          <div className="text-center mb-6">
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Complete Your Registration</h2>
            <p className="text-gray-600">
              We need a few details to send your report
            </p>
          </div>
          <EnrollmentForm onSubmit={handleEnrollmentSubmit} />
        </div>
      )}

      {/* Social Share Step (for free tier) */}
      {step === 'social-share' && leadData.leadId && (
        <SocialShareUnlock
          leadId={leadData.leadId}
          auditUrl={`${typeof window !== 'undefined' ? window.location.origin : ''}/audit/${leadData.auditId}`}
          websiteUrl={leadData.url}
          score={leadData.auditResult?.overall_score || 0}
          onComplete={() => setStep('complete')}
        />
      )}

      {/* Payment Step */}
      {step === 'payment' && leadData.selectedPackage && (
        <StripeCheckout
          packageId={leadData.selectedPackage}
          packageName={PACKAGE_PRICES[leadData.selectedPackage]?.name || leadData.selectedPackage}
          price={PACKAGE_PRICES[leadData.selectedPackage]?.price || 0}
          currency={PACKAGE_PRICES[leadData.selectedPackage]?.currency || 'EUR'}
          auditId={leadData.auditId}
          onSuccess={() => setStep('complete')}
          onCancel={() => setStep('enrollment')}
        />
      )}

      {/* Complete Step */}
      {step === 'complete' && (
        <div className="text-center py-12">
          <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
            <CheckCircle className="w-12 h-12 text-green-600" />
          </div>
          <h2 className="text-3xl font-bold text-gray-900 mb-4">You're All Set!</h2>
          <p className="text-gray-600 mb-8">
            Your full audit report is ready. We've also sent a copy to your email.
          </p>
          <Button
            onClick={goToFullResults}
            size="lg"
            className="bg-primary-600 hover:bg-primary-700"
          >
            View Full Report
          </Button>
        </div>
      )}
    </div>
  )
}

// Helper Components

function StepIndicator({ currentStep }: { currentStep: FlowStep }) {
  // Dynamically show social-share OR payment based on current step
  const isFreeFlow = currentStep === 'social-share'
  const steps = [
    { id: 'teaser-results', label: 'Results' },
    { id: 'package-selection', label: 'Package' },
    { id: 'enrollment', label: 'Register' },
    ...(isFreeFlow
      ? [{ id: 'social-share', label: 'Share' }]
      : [{ id: 'payment', label: 'Payment' }]),
    { id: 'complete', label: 'Complete' }
  ]

  const currentIndex = steps.findIndex(s => s.id === currentStep)

  return (
    <div className="flex items-center gap-2">
      {steps.map((s, idx) => (
        <div key={s.id} className="flex items-center">
          <div
            className={`w-2 h-2 rounded-full ${
              idx <= currentIndex ? 'bg-primary-600' : 'bg-gray-300'
            }`}
          />
          {idx < steps.length - 1 && (
            <div className={`w-8 h-0.5 ${idx < currentIndex ? 'bg-primary-600' : 'bg-gray-300'}`} />
          )}
        </div>
      ))}
    </div>
  )
}

function FeatureCard({ title, description }: { title: string; description: string }) {
  return (
    <div className="bg-white p-6 rounded-lg shadow text-center">
      <h3 className="font-semibold text-gray-900 mb-2">{title}</h3>
      <p className="text-sm text-gray-600">{description}</p>
    </div>
  )
}

function AuditingStep({ label, done, active }: { label: string; done?: boolean; active?: boolean }) {
  return (
    <div className={`flex items-center gap-3 px-4 py-2 rounded-lg ${
      done ? 'bg-green-50' : active ? 'bg-primary-50' : 'bg-gray-50'
    }`}>
      {done ? (
        <CheckCircle className="w-5 h-5 text-green-600" />
      ) : active ? (
        <Loader2 className="w-5 h-5 text-primary-600 animate-spin" />
      ) : (
        <div className="w-5 h-5 rounded-full border-2 border-gray-300" />
      )}
      <span className={`text-sm ${done ? 'text-green-700' : active ? 'text-primary-700' : 'text-gray-500'}`}>
        {label}
      </span>
    </div>
  )
}
