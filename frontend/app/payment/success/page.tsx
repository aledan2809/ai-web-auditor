'use client'

import { useEffect } from 'react'
import Link from 'next/link'
import { CheckCircle, ArrowRight } from 'lucide-react'
import { useAuth } from '@/lib/auth'

export default function PaymentSuccessPage() {
  const { checkAuth } = useAuth()

  useEffect(() => {
    // Refresh user data to get updated credits
    checkAuth()
  }, [])

  return (
    <div className="min-h-[60vh] flex items-center justify-center">
      <div className="text-center">
        <div className="inline-flex items-center justify-center w-16 h-16 bg-green-100 rounded-full mb-6">
          <CheckCircle className="w-8 h-8 text-green-600" />
        </div>

        <h1 className="text-2xl font-bold text-gray-900 mb-2">Plata efectuata cu succes!</h1>
        <p className="text-gray-600 mb-8">Creditele au fost adaugate in contul tau.</p>

        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Link
            href="/"
            className="inline-flex items-center justify-center gap-2 px-6 py-3 bg-primary-600 text-white rounded-lg font-medium hover:bg-primary-700"
          >
            Porneste un audit
            <ArrowRight className="w-4 h-4" />
          </Link>
          <Link
            href="/history"
            className="inline-flex items-center justify-center gap-2 px-6 py-3 bg-gray-100 text-gray-900 rounded-lg font-medium hover:bg-gray-200"
          >
            Vezi istoric
          </Link>
        </div>
      </div>
    </div>
  )
}
