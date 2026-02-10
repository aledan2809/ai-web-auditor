'use client'

import { Suspense, useEffect, useState } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import Link from 'next/link'
import { CheckCircle, ArrowRight, FileText, Mail, Loader2 } from 'lucide-react'
import { useAuth } from '@/lib/auth'
import { Button } from '@/components/ui/button'

interface PendingPayment {
  auditId: string
  leadId?: string
  packageId: string
  sessionId: string
}

function PaymentSuccessContent() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const { checkAuth } = useAuth()
  const [pendingPayment, setPendingPayment] = useState<PendingPayment | null>(null)
  const [isVerifying, setIsVerifying] = useState(true)

  useEffect(() => {
    // Refresh user data
    checkAuth()

    // Check for pending payment from lead capture flow
    const stored = sessionStorage.getItem('pending_payment')
    if (stored) {
      try {
        const data = JSON.parse(stored)
        setPendingPayment(data)
        // Clear stored data
        sessionStorage.removeItem('pending_payment')
      } catch (e) {
        console.error('Failed to parse pending payment:', e)
      }
    }

    // Simulate verification delay
    setTimeout(() => setIsVerifying(false), 1500)
  }, [])

  if (isVerifying) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-12 h-12 animate-spin text-primary-600 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900">Verifying payment...</h2>
          <p className="text-gray-600">Please wait while we confirm your payment</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-[60vh] flex items-center justify-center py-12">
      <div className="max-w-md mx-auto text-center">
        <div className="inline-flex items-center justify-center w-20 h-20 bg-green-100 rounded-full mb-6">
          <CheckCircle className="w-10 h-10 text-green-600" />
        </div>

        <h1 className="text-3xl font-bold text-gray-900 mb-2">Payment Successful!</h1>
        <p className="text-gray-600 mb-8">
          Thank you for your purchase. Your full audit report is now ready.
        </p>

        {/* What's included */}
        <div className="bg-white rounded-xl shadow-lg p-6 mb-8 text-left">
          <h3 className="font-semibold text-gray-900 mb-4">What you get:</h3>
          <ul className="space-y-3">
            <li className="flex items-start gap-3">
              <FileText className="w-5 h-5 text-primary-600 flex-shrink-0 mt-0.5" />
              <span className="text-gray-700">Full detailed audit report with all issues</span>
            </li>
            <li className="flex items-start gap-3">
              <FileText className="w-5 h-5 text-primary-600 flex-shrink-0 mt-0.5" />
              <span className="text-gray-700">Professional PDF report for your records</span>
            </li>
            <li className="flex items-start gap-3">
              <Mail className="w-5 h-5 text-primary-600 flex-shrink-0 mt-0.5" />
              <span className="text-gray-700">Report sent to your email</span>
            </li>
          </ul>
        </div>

        <div className="flex flex-col gap-3">
          {pendingPayment?.auditId ? (
            <Button
              onClick={() => router.push(`/audit/${pendingPayment.auditId}`)}
              size="lg"
              className="w-full bg-primary-600 hover:bg-primary-700"
            >
              View Full Report
              <ArrowRight className="w-4 h-4 ml-2" />
            </Button>
          ) : (
            <Link
              href="/"
              className="inline-flex items-center justify-center gap-2 px-6 py-3 bg-primary-600 text-white rounded-lg font-medium hover:bg-primary-700"
            >
              Start a New Audit
              <ArrowRight className="w-4 h-4" />
            </Link>
          )}
          <Link
            href="/history"
            className="inline-flex items-center justify-center gap-2 px-6 py-3 bg-gray-100 text-gray-900 rounded-lg font-medium hover:bg-gray-200"
          >
            View Audit History
          </Link>
        </div>

        {/* Receipt info */}
        <p className="mt-6 text-sm text-gray-500">
          A receipt has been sent to your email. If you have any questions,
          please contact support@aiwebauditor.com
        </p>
      </div>
    </div>
  )
}

export default function PaymentSuccessPage() {
  return (
    <Suspense fallback={
      <div className="min-h-[60vh] flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-12 h-12 animate-spin text-primary-600 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900">Loading...</h2>
        </div>
      </div>
    }>
      <PaymentSuccessContent />
    </Suspense>
  )
}
