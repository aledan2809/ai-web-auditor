'use client'

import { useState } from 'react'
import { Loader2, CreditCard, Lock, Shield } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { paymentsApi } from '@/lib/api'

interface StripeCheckoutProps {
  packageId: string
  packageName: string
  price: number
  currency: string
  auditId: string
  leadId?: string
  onSuccess: () => void
  onCancel: () => void
}

export default function StripeCheckout({
  packageId,
  packageName,
  price,
  currency,
  auditId,
  leadId,
  onSuccess,
  onCancel
}: StripeCheckoutProps) {
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')

  const handleCheckout = async () => {
    setIsLoading(true)
    setError('')

    try {
      // Create Stripe checkout session
      const response = await paymentsApi.createCheckout(packageId)

      if (response.data.checkout_url) {
        // Store return data in session storage for after redirect
        sessionStorage.setItem('pending_payment', JSON.stringify({
          auditId,
          leadId,
          packageId,
          sessionId: response.data.session_id
        }))

        // Redirect to Stripe Checkout
        window.location.href = response.data.checkout_url
      } else {
        setError('Failed to create checkout session')
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Payment initialization failed')
    } finally {
      setIsLoading(false)
    }
  }

  const formatPrice = (amount: number, curr: string) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: curr,
      minimumFractionDigits: 2
    }).format(amount)
  }

  return (
    <div className="max-w-md mx-auto">
      {/* Order Summary */}
      <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Order Summary</h2>

        <div className="border-b pb-4 mb-4">
          <div className="flex justify-between items-center">
            <div>
              <p className="font-medium text-gray-900">{packageName} Package</p>
              <p className="text-sm text-gray-500">One-time payment</p>
            </div>
            <p className="text-xl font-bold text-gray-900">
              {formatPrice(price, currency)}
            </p>
          </div>
        </div>

        <div className="flex justify-between items-center text-lg font-semibold">
          <span>Total</span>
          <span className="text-primary-600">{formatPrice(price, currency)}</span>
        </div>
      </div>

      {/* Payment Section */}
      <div className="bg-white rounded-xl shadow-lg p-6">
        <div className="flex items-center gap-2 mb-6">
          <CreditCard className="w-5 h-5 text-gray-600" />
          <h3 className="font-semibold text-gray-900">Secure Payment</h3>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
            {error}
          </div>
        )}

        <Button
          onClick={handleCheckout}
          disabled={isLoading}
          className="w-full py-6 text-lg bg-primary-600 hover:bg-primary-700"
        >
          {isLoading ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin mr-2" />
              Redirecting to payment...
            </>
          ) : (
            <>
              <Lock className="w-5 h-5 mr-2" />
              Pay {formatPrice(price, currency)}
            </>
          )}
        </Button>

        <button
          onClick={onCancel}
          className="w-full mt-3 py-2 text-gray-600 hover:text-gray-900 text-sm"
        >
          Cancel and go back
        </button>

        {/* Trust badges */}
        <div className="mt-6 pt-4 border-t">
          <div className="flex items-center justify-center gap-4 text-xs text-gray-500">
            <div className="flex items-center gap-1">
              <Shield className="w-4 h-4" />
              <span>SSL Secured</span>
            </div>
            <div className="flex items-center gap-1">
              <Lock className="w-4 h-4" />
              <span>256-bit encryption</span>
            </div>
          </div>
          <div className="mt-3 flex justify-center">
            <img
              src="https://cdn.brandfolder.io/KGT2DTA4/at/8vbr8k4mr5xjwk4hxq4t9vs/Stripe_wordmark_-_blurple.svg"
              alt="Powered by Stripe"
              className="h-6 opacity-50"
            />
          </div>
        </div>
      </div>

      {/* Payment methods */}
      <div className="mt-4 text-center text-xs text-gray-500">
        <p>We accept all major credit cards</p>
        <div className="flex justify-center gap-2 mt-2 opacity-60">
          <div className="w-10 h-6 bg-gray-200 rounded flex items-center justify-center text-[8px] font-bold">VISA</div>
          <div className="w-10 h-6 bg-gray-200 rounded flex items-center justify-center text-[8px] font-bold">MC</div>
          <div className="w-10 h-6 bg-gray-200 rounded flex items-center justify-center text-[8px] font-bold">AMEX</div>
        </div>
      </div>
    </div>
  )
}
