'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import SignatureCanvas from '@/components/signature/SignatureCanvas'
import {
  createTermsAcceptance,
  createAuditLogEntry,
  generateEnrollmentReference,
  type TermsAcceptance
} from '@/lib/contract-security'
import {
  Mail, User, Globe, FileCheck, Loader2, CheckCircle, AlertCircle
} from 'lucide-react'

// Available languages
const LANGUAGES = [
  { code: 'en', label: 'English', flag: '🇬🇧' },
  { code: 'ro', label: 'Romana', flag: '🇷🇴' },
  { code: 'ar', label: 'العربية', flag: '🇦🇪', rtl: true },
  { code: 'de', label: 'Deutsch', flag: '🇩🇪' },
  { code: 'es', label: 'Espanol', flag: '🇪🇸' },
  { code: 'fr', label: 'Francais', flag: '🇫🇷' },
  { code: 'it', label: 'Italiano', flag: '🇮🇹' },
]

// Terms versions
const TERMS_VERSION = '1.0.0'
const PRIVACY_VERSION = '1.0.0'

interface EnrollmentFormProps {
  auditId: string
  packageId: string
  packageName: string
  onSuccess: (enrollmentData: EnrollmentData) => void
  onCancel?: () => void
}

export interface EnrollmentData {
  enrollmentId: string
  email: string
  name: string
  language: string
  termsAcceptance: TermsAcceptance
  newsletterConsent: boolean
  signatureDataUrl?: string
}

const EnrollmentForm = ({
  auditId,
  packageId,
  packageName,
  onSuccess,
  onCancel
}: EnrollmentFormProps) => {
  // Form state
  const [email, setEmail] = useState('')
  const [name, setName] = useState('')
  const [language, setLanguage] = useState('en')
  const [termsAccepted, setTermsAccepted] = useState(false)
  const [privacyAccepted, setPrivacyAccepted] = useState(false)
  const [newsletterConsent, setNewsletterConsent] = useState(false)
  const [signatureDataUrl, setSignatureDataUrl] = useState<string | null>(null)

  // UI state
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showTerms, setShowTerms] = useState(false)
  const [showPrivacy, setShowPrivacy] = useState(false)

  // Validation
  const isEmailValid = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)
  const isFormValid = isEmailValid && name.trim().length >= 2 && termsAccepted && privacyAccepted

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!isFormValid) return

    setIsSubmitting(true)
    setError(null)

    try {
      // Create terms acceptance record
      const termsAcceptance = await createTermsAcceptance(
        `terms:${TERMS_VERSION},privacy:${PRIVACY_VERSION}`,
        signatureDataUrl || undefined
      )

      // Create audit log entry
      const auditEntry = createAuditLogEntry('enroll', {
        email,
        additionalMetadata: {
          auditId,
          packageId,
          name,
          language,
          newsletterConsent,
          hasSignature: !!signatureDataUrl,
        }
      })

      // Generate enrollment reference
      const enrollmentId = generateEnrollmentReference()

      // Prepare enrollment data
      const enrollmentData: EnrollmentData = {
        enrollmentId,
        email,
        name,
        language,
        termsAcceptance,
        newsletterConsent,
        signatureDataUrl: signatureDataUrl || undefined,
      }

      // TODO: Send to backend API
      // await api.post('/api/leads/enroll', {
      //   ...enrollmentData,
      //   auditId,
      //   packageId,
      //   auditLog: auditEntry
      // })

      console.log('Enrollment data:', enrollmentData)
      console.log('Audit entry:', auditEntry)

      // Success callback
      onSuccess(enrollmentData)

    } catch (err) {
      console.error('Enrollment error:', err)
      setError('An error occurred. Please try again.')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="bg-white rounded-xl shadow-lg p-6 max-w-lg mx-auto">
      <div className="text-center mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Get Your Full Report</h2>
        <p className="text-gray-600 mt-2">
          Complete the form below to receive your <span className="font-semibold">{packageName}</span> report
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-5">
        {/* Email */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Email Address *
          </label>
          <div className="relative">
            <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
            <Input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="your@email.com"
              className="pl-10"
              required
            />
          </div>
          {email && !isEmailValid && (
            <p className="text-sm text-red-500 mt-1">Please enter a valid email address</p>
          )}
        </div>

        {/* Name */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Full Name *
          </label>
          <div className="relative">
            <User className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
            <Input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="John Doe"
              className="pl-10"
              required
              minLength={2}
            />
          </div>
        </div>

        {/* Language Selection */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            <Globe className="inline w-4 h-4 mr-1" />
            Report Language
          </label>
          <div className="grid grid-cols-4 gap-2">
            {LANGUAGES.map((lang) => (
              <button
                key={lang.code}
                type="button"
                onClick={() => setLanguage(lang.code)}
                className={`p-2 rounded-lg border text-center transition-all ${
                  language === lang.code
                    ? 'border-primary-500 bg-primary-50 text-primary-700'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <span className="text-lg">{lang.flag}</span>
                <span className="block text-xs mt-1">{lang.code.toUpperCase()}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Terms & Privacy Checkboxes */}
        <div className="space-y-3 pt-2">
          <label className="flex items-start gap-3 cursor-pointer">
            <input
              type="checkbox"
              checked={termsAccepted}
              onChange={(e) => setTermsAccepted(e.target.checked)}
              className="mt-1 w-4 h-4 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
            />
            <span className="text-sm text-gray-600">
              I accept the{' '}
              <button
                type="button"
                onClick={() => setShowTerms(!showTerms)}
                className="text-primary-600 hover:underline"
              >
                Terms & Conditions
              </button>
              {' '}*
            </span>
          </label>

          <label className="flex items-start gap-3 cursor-pointer">
            <input
              type="checkbox"
              checked={privacyAccepted}
              onChange={(e) => setPrivacyAccepted(e.target.checked)}
              className="mt-1 w-4 h-4 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
            />
            <span className="text-sm text-gray-600">
              I accept the{' '}
              <button
                type="button"
                onClick={() => setShowPrivacy(!showPrivacy)}
                className="text-primary-600 hover:underline"
              >
                Privacy Policy & GDPR
              </button>
              {' '}*
            </span>
          </label>

          <label className="flex items-start gap-3 cursor-pointer">
            <input
              type="checkbox"
              checked={newsletterConsent}
              onChange={(e) => setNewsletterConsent(e.target.checked)}
              className="mt-1 w-4 h-4 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
            />
            <span className="text-sm text-gray-600">
              I want to receive tips, offers, and updates via email (optional)
            </span>
          </label>
        </div>

        {/* Signature Canvas */}
        <div className="pt-2">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            <FileCheck className="inline w-4 h-4 mr-1" />
            Digital Signature (optional but recommended)
          </label>
          <SignatureCanvas
            onSignatureChange={setSignatureDataUrl}
            label="Sign below to confirm your agreement"
            clearLabel="Clear"
            hintLabel="Use mouse or finger to draw your signature"
          />
        </div>

        {/* Error Message */}
        {error && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2 text-red-700">
            <AlertCircle className="w-5 h-5 flex-shrink-0" />
            <span className="text-sm">{error}</span>
          </div>
        )}

        {/* Submit Buttons */}
        <div className="flex gap-3 pt-2">
          {onCancel && (
            <Button
              type="button"
              variant="outline"
              onClick={onCancel}
              disabled={isSubmitting}
              className="flex-1"
            >
              Cancel
            </Button>
          )}
          <Button
            type="submit"
            disabled={!isFormValid || isSubmitting}
            className="flex-1 bg-primary-600 hover:bg-primary-700"
          >
            {isSubmitting ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin mr-2" />
                Processing...
              </>
            ) : (
              <>
                <CheckCircle className="w-5 h-5 mr-2" />
                Get My Report
              </>
            )}
          </Button>
        </div>

        <p className="text-xs text-center text-gray-500 pt-2">
          Your data is secure and will never be shared without your consent.
        </p>
      </form>

      {/* Terms Modal - simplified inline version */}
      {showTerms && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl max-w-2xl w-full max-h-[80vh] overflow-y-auto p-6">
            <h3 className="text-xl font-bold mb-4">Terms & Conditions</h3>
            <div className="prose prose-sm">
              <p>Version: {TERMS_VERSION}</p>
              <p>Last updated: February 2026</p>
              <h4>1. Service Description</h4>
              <p>AI Web Auditor provides website analysis services including performance, SEO, security, GDPR compliance, and accessibility audits.</p>
              <h4>2. Use of Service</h4>
              <p>By using our service, you agree to provide accurate information and use the reports for legitimate purposes only.</p>
              <h4>3. Payment Terms</h4>
              <p>Paid packages are processed securely via our payment provider. Refunds are available within 14 days of purchase.</p>
              {/* Add more terms as needed */}
            </div>
            <Button onClick={() => setShowTerms(false)} className="mt-4 w-full">
              Close
            </Button>
          </div>
        </div>
      )}

      {/* Privacy Modal - simplified inline version */}
      {showPrivacy && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl max-w-2xl w-full max-h-[80vh] overflow-y-auto p-6">
            <h3 className="text-xl font-bold mb-4">Privacy Policy & GDPR</h3>
            <div className="prose prose-sm">
              <p>Version: {PRIVACY_VERSION}</p>
              <p>Last updated: February 2026</p>
              <h4>1. Data Collection</h4>
              <p>We collect: email address, name, website URL for auditing, and usage analytics.</p>
              <h4>2. Data Usage</h4>
              <p>Your data is used to provide audit services, send reports, and if consented, marketing communications.</p>
              <h4>3. Your Rights (GDPR)</h4>
              <p>You have the right to access, rectify, delete, and port your data. Contact us at privacy@aiwebauditor.com.</p>
              <h4>4. Data Retention</h4>
              <p>We retain your data for 2 years or until you request deletion.</p>
            </div>
            <Button onClick={() => setShowPrivacy(false)} className="mt-4 w-full">
              Close
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}

export default EnrollmentForm
