'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Check, Zap, Crown, Loader2, AlertCircle } from 'lucide-react'
import { paymentsApi, Product } from '@/lib/api'
import { useAuth } from '@/lib/auth'

const plans = [
  {
    id: 'single',
    name: 'Audit Unic',
    price: 5,
    credits: 1,
    features: ['1 audit complet', 'Raport PDF', 'Estimare pret reparari'],
    popular: false,
  },
  {
    id: 'pack_5',
    name: 'Pachet 5',
    price: 20,
    credits: 5,
    discount: '20%',
    features: ['5 audituri complete', 'Rapoarte PDF', 'Estimari AI', 'Economie 5 EUR'],
    popular: false,
  },
  {
    id: 'pack_10',
    name: 'Pachet 10',
    price: 35,
    credits: 10,
    discount: '30%',
    features: ['10 audituri complete', 'Rapoarte PDF', 'Estimari AI', 'Economie 15 EUR'],
    popular: true,
  },
  {
    id: 'pack_20',
    name: 'Pachet 20',
    price: 60,
    credits: 20,
    discount: '40%',
    features: ['20 audituri complete', 'Rapoarte PDF', 'Estimari AI', 'Economie 40 EUR'],
    popular: false,
  },
]

const subscriptions = [
  {
    id: 'monthly',
    name: 'Lunar',
    price: 29,
    period: '/luna',
    credits: 20,
    features: ['20 audituri/luna', 'Rapoarte nelimitate', 'Suport prioritar', 'Anuleaza oricand'],
  },
  {
    id: 'yearly',
    name: 'Anual',
    price: 290,
    period: '/an',
    credits: 240,
    discount: '2 luni gratuite',
    features: ['20 audituri/luna', 'Rapoarte nelimitate', 'Suport prioritar', 'Economie 58 EUR'],
  },
]

export default function PricingPage() {
  const router = useRouter()
  const { user, isAuthenticated, checkAuth } = useAuth()
  const [isLoading, setIsLoading] = useState<string | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    checkAuth()
  }, [])

  const handlePurchase = async (productId: string) => {
    if (!isAuthenticated) {
      router.push('/login')
      return
    }

    setIsLoading(productId)
    setError('')

    try {
      const response = await paymentsApi.createCheckout(productId)
      window.location.href = response.data.checkout_url
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Eroare la procesarea platii')
      setIsLoading(null)
    }
  }

  return (
    <div className="max-w-6xl mx-auto">
      <div className="text-center mb-12">
        <h1 className="text-3xl font-bold text-gray-900">Preturi</h1>
        <p className="text-gray-600 mt-2">Alege planul potrivit pentru nevoile tale</p>
        {user && (
          <p className="text-primary-600 mt-4 font-medium">
            Credite disponibile: {user.credits}
          </p>
        )}
      </div>

      {error && (
        <div className="flex items-center gap-2 p-4 mb-8 bg-red-50 border border-red-200 rounded-lg text-red-700 max-w-md mx-auto">
          <AlertCircle className="w-5 h-5" />
          <span>{error}</span>
        </div>
      )}

      {/* One-time purchases */}
      <div className="mb-12">
        <h2 className="text-xl font-semibold text-gray-900 mb-6 text-center">Pachete unice</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {plans.map((plan) => (
            <div
              key={plan.id}
              className={`bg-white rounded-xl shadow-lg p-6 relative ${
                plan.popular ? 'ring-2 ring-primary-500' : ''
              }`}
            >
              {plan.popular && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                  <span className="bg-primary-600 text-white text-xs font-medium px-3 py-1 rounded-full">
                    Popular
                  </span>
                </div>
              )}

              {plan.discount && (
                <div className="absolute -top-3 right-4">
                  <span className="bg-green-500 text-white text-xs font-medium px-2 py-1 rounded-full">
                    -{plan.discount}
                  </span>
                </div>
              )}

              <div className="text-center mb-6">
                <h3 className="text-lg font-semibold text-gray-900">{plan.name}</h3>
                <div className="mt-4">
                  <span className="text-4xl font-bold text-gray-900">{plan.price}</span>
                  <span className="text-gray-600"> EUR</span>
                </div>
                <p className="text-sm text-gray-500 mt-1">{plan.credits} credite</p>
              </div>

              <ul className="space-y-3 mb-6">
                {plan.features.map((feature, i) => (
                  <li key={i} className="flex items-center gap-2 text-sm text-gray-600">
                    <Check className="w-4 h-4 text-green-500" />
                    {feature}
                  </li>
                ))}
              </ul>

              <button
                onClick={() => handlePurchase(plan.id)}
                disabled={isLoading === plan.id}
                className={`w-full py-3 rounded-lg font-medium flex items-center justify-center gap-2 ${
                  plan.popular
                    ? 'bg-primary-600 text-white hover:bg-primary-700'
                    : 'bg-gray-100 text-gray-900 hover:bg-gray-200'
                } disabled:opacity-50`}
              >
                {isLoading === plan.id ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  <>
                    <Zap className="w-4 h-4" />
                    Cumpara
                  </>
                )}
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Subscriptions */}
      <div>
        <h2 className="text-xl font-semibold text-gray-900 mb-6 text-center">Abonamente</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-2xl mx-auto">
          {subscriptions.map((plan) => (
            <div
              key={plan.id}
              className="bg-white rounded-xl shadow-lg p-6 relative"
            >
              {plan.discount && (
                <div className="absolute -top-3 right-4">
                  <span className="bg-green-500 text-white text-xs font-medium px-2 py-1 rounded-full">
                    {plan.discount}
                  </span>
                </div>
              )}

              <div className="flex items-center gap-2 mb-4">
                <Crown className="w-5 h-5 text-primary-600" />
                <h3 className="text-lg font-semibold text-gray-900">{plan.name}</h3>
              </div>

              <div className="mb-6">
                <span className="text-4xl font-bold text-gray-900">{plan.price}</span>
                <span className="text-gray-600"> EUR{plan.period}</span>
              </div>

              <ul className="space-y-3 mb-6">
                {plan.features.map((feature, i) => (
                  <li key={i} className="flex items-center gap-2 text-sm text-gray-600">
                    <Check className="w-4 h-4 text-green-500" />
                    {feature}
                  </li>
                ))}
              </ul>

              <button
                onClick={() => handlePurchase(plan.id)}
                disabled={isLoading === plan.id}
                className="w-full py-3 bg-primary-600 text-white rounded-lg font-medium hover:bg-primary-700 disabled:opacity-50 flex items-center justify-center gap-2"
              >
                {isLoading === plan.id ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  <>
                    <Crown className="w-4 h-4" />
                    Aboneaza-te
                  </>
                )}
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* FAQ or info section */}
      <div className="mt-12 text-center text-gray-600">
        <p>Toate platile sunt procesate securizat prin Stripe.</p>
        <p className="mt-1">Poti anula abonamentul oricand.</p>
      </div>
    </div>
  )
}
