'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import {
  ArrowLeft, Save, Loader2, Plus, Trash2,
  DollarSign, Building, CreditCard, Package
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { settingsApi, PricingSettings, PackageConfig } from '@/lib/api'
import { useAuth } from '@/lib/auth'

const DEFAULT_PACKAGES: PackageConfig[] = [
  {
    id: 'starter',
    name: 'Starter',
    price: 0,
    currency: 'EUR',
    audits_included: 2,
    total_audits: 6,
    features: ['Choose 2 audit types', 'Basic score overview', 'Share on social media'],
    requires_share: true,
    pdf_type: 'none',
    is_active: true
  },
  {
    id: 'pro',
    name: 'Pro',
    price: 1.99,
    currency: 'EUR',
    audits_included: 4,
    total_audits: 6,
    features: ['Choose 4 audit types', 'Detailed issue breakdown', 'Basic PDF report', 'Email delivery'],
    popular: true,
    pdf_type: 'basic',
    is_active: true
  },
  {
    id: 'full',
    name: 'Full',
    price: 4.99,
    currency: 'EUR',
    audits_included: 6,
    total_audits: 6,
    features: ['All 6 audit types', 'Full issue details', 'Professional PDF report', 'Priority support', 'AI recommendations'],
    pdf_type: 'professional',
    is_active: true
  }
]

const DEFAULT_SETTINGS: PricingSettings = {
  packages: DEFAULT_PACKAGES,
  hourly_rate: 75,
  currency: 'EUR',
  vat_rate: 0, // Dubai has 5% VAT but service exports are 0%
  company_details: {
    name: 'AI Web Auditor FZ-LLC',
    address: 'Dubai Silicon Oasis, Dubai, UAE',
    vat_number: '',
    bank_name: 'Wio Business',
    bank_account: '',
    swift: ''
  }
}

export default function AdminSettingsPage() {
  const router = useRouter()
  const { user, isAuthenticated, isLoading: authLoading, checkAuth } = useAuth()
  const [settings, setSettings] = useState<PricingSettings>(DEFAULT_SETTINGS)
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState('')
  const [successMessage, setSuccessMessage] = useState('')

  useEffect(() => {
    checkAuth()
  }, [])

  useEffect(() => {
    if (!authLoading) {
      if (!isAuthenticated) {
        router.push('/login')
      } else if (user?.role !== 'admin') {
        router.push('/')
      } else {
        loadSettings()
      }
    }
  }, [authLoading, isAuthenticated, user])

  const loadSettings = async () => {
    setIsLoading(true)
    try {
      const response = await settingsApi.getPricingSettings()
      setSettings(response.data)
    } catch (err) {
      // Use defaults if no settings exist
      setSettings(DEFAULT_SETTINGS)
    } finally {
      setIsLoading(false)
    }
  }

  const handleSave = async () => {
    setIsSaving(true)
    setError('')
    setSuccessMessage('')

    try {
      await settingsApi.updatePricingSettings(settings)
      setSuccessMessage('Settings saved successfully!')
      setTimeout(() => setSuccessMessage(''), 3000)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to save settings')
    } finally {
      setIsSaving(false)
    }
  }

  const updatePackage = (index: number, updates: Partial<PackageConfig>) => {
    setSettings(prev => ({
      ...prev,
      packages: prev.packages.map((pkg, i) =>
        i === index ? { ...pkg, ...updates } : pkg
      )
    }))
  }

  const addFeature = (packageIndex: number) => {
    const newFeature = prompt('Enter new feature:')
    if (newFeature) {
      updatePackage(packageIndex, {
        features: [...settings.packages[packageIndex].features, newFeature]
      })
    }
  }

  const removeFeature = (packageIndex: number, featureIndex: number) => {
    updatePackage(packageIndex, {
      features: settings.packages[packageIndex].features.filter((_, i) => i !== featureIndex)
    })
  }

  if (authLoading || isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <Loader2 className="w-8 h-8 animate-spin text-primary-600" />
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div className="flex items-center gap-4">
          <Link href="/admin" className="p-2 hover:bg-gray-100 rounded-lg">
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Pricing Settings</h1>
            <p className="text-gray-600">Configure packages, pricing, and company details</p>
          </div>
        </div>
        <Button onClick={handleSave} disabled={isSaving}>
          {isSaving ? (
            <Loader2 className="w-4 h-4 animate-spin mr-2" />
          ) : (
            <Save className="w-4 h-4 mr-2" />
          )}
          Save Changes
        </Button>
      </div>

      {/* Messages */}
      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
          {error}
        </div>
      )}
      {successMessage && (
        <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg text-green-700">
          {successMessage}
        </div>
      )}

      <div className="space-y-8">
        {/* General Pricing */}
        <section className="bg-white rounded-xl shadow p-6">
          <div className="flex items-center gap-2 mb-6">
            <DollarSign className="w-5 h-5 text-primary-600" />
            <h2 className="text-lg font-semibold">General Pricing</h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Hourly Rate (for estimates)
              </label>
              <input
                type="number"
                value={settings.hourly_rate}
                onChange={(e) => setSettings(prev => ({ ...prev, hourly_rate: Number(e.target.value) }))}
                className="w-full px-3 py-2 border rounded-lg"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Currency
              </label>
              <select
                value={settings.currency}
                onChange={(e) => setSettings(prev => ({ ...prev, currency: e.target.value }))}
                className="w-full px-3 py-2 border rounded-lg"
              >
                <option value="EUR">EUR (Euro)</option>
                <option value="USD">USD (Dollar)</option>
                <option value="AED">AED (Dirham)</option>
                <option value="GBP">GBP (Pound)</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                VAT Rate (%)
              </label>
              <input
                type="number"
                value={settings.vat_rate}
                onChange={(e) => setSettings(prev => ({ ...prev, vat_rate: Number(e.target.value) }))}
                className="w-full px-3 py-2 border rounded-lg"
                min="0"
                max="100"
              />
            </div>
          </div>
        </section>

        {/* Packages */}
        <section className="bg-white rounded-xl shadow p-6">
          <div className="flex items-center gap-2 mb-6">
            <Package className="w-5 h-5 text-primary-600" />
            <h2 className="text-lg font-semibold">Packages</h2>
          </div>

          <div className="space-y-6">
            {settings.packages.map((pkg, pkgIndex) => (
              <div key={pkg.id} className="border rounded-lg p-4">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <input
                      type="text"
                      value={pkg.name}
                      onChange={(e) => updatePackage(pkgIndex, { name: e.target.value })}
                      className="text-lg font-semibold border-0 bg-transparent focus:ring-0 p-0"
                    />
                    {pkg.popular && (
                      <span className="text-xs bg-yellow-100 text-yellow-800 px-2 py-0.5 rounded">
                        Popular
                      </span>
                    )}
                  </div>
                  <label className="flex items-center gap-2 text-sm">
                    <input
                      type="checkbox"
                      checked={pkg.is_active}
                      onChange={(e) => updatePackage(pkgIndex, { is_active: e.target.checked })}
                      className="rounded"
                    />
                    Active
                  </label>
                </div>

                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                  <div>
                    <label className="block text-xs text-gray-500 mb-1">Price</label>
                    <div className="flex items-center">
                      <input
                        type="number"
                        value={pkg.price}
                        onChange={(e) => updatePackage(pkgIndex, { price: Number(e.target.value) })}
                        className="w-full px-2 py-1 border rounded-l-lg text-sm"
                        step="0.01"
                        min="0"
                      />
                      <span className="px-2 py-1 bg-gray-100 border border-l-0 rounded-r-lg text-sm">
                        {pkg.currency}
                      </span>
                    </div>
                  </div>
                  <div>
                    <label className="block text-xs text-gray-500 mb-1">Audits Included</label>
                    <input
                      type="number"
                      value={pkg.audits_included}
                      onChange={(e) => updatePackage(pkgIndex, { audits_included: Number(e.target.value) })}
                      className="w-full px-2 py-1 border rounded-lg text-sm"
                      min="1"
                      max="6"
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-gray-500 mb-1">PDF Type</label>
                    <select
                      value={pkg.pdf_type}
                      onChange={(e) => updatePackage(pkgIndex, { pdf_type: e.target.value as PackageConfig['pdf_type'] })}
                      className="w-full px-2 py-1 border rounded-lg text-sm"
                    >
                      <option value="none">None</option>
                      <option value="basic">Basic</option>
                      <option value="professional">Professional</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs text-gray-500 mb-1">Options</label>
                    <div className="space-y-1">
                      <label className="flex items-center gap-1 text-xs">
                        <input
                          type="checkbox"
                          checked={pkg.popular || false}
                          onChange={(e) => updatePackage(pkgIndex, { popular: e.target.checked })}
                          className="rounded text-xs"
                        />
                        Popular badge
                      </label>
                      <label className="flex items-center gap-1 text-xs">
                        <input
                          type="checkbox"
                          checked={pkg.requires_share || false}
                          onChange={(e) => updatePackage(pkgIndex, { requires_share: e.target.checked })}
                          className="rounded text-xs"
                        />
                        Requires share
                      </label>
                    </div>
                  </div>
                </div>

                {/* Features */}
                <div>
                  <label className="block text-xs text-gray-500 mb-2">Features</label>
                  <div className="space-y-1">
                    {pkg.features.map((feature, featureIndex) => (
                      <div key={featureIndex} className="flex items-center gap-2">
                        <input
                          type="text"
                          value={feature}
                          onChange={(e) => {
                            const newFeatures = [...pkg.features]
                            newFeatures[featureIndex] = e.target.value
                            updatePackage(pkgIndex, { features: newFeatures })
                          }}
                          className="flex-1 px-2 py-1 border rounded text-sm"
                        />
                        <button
                          onClick={() => removeFeature(pkgIndex, featureIndex)}
                          className="p-1 text-red-500 hover:bg-red-50 rounded"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    ))}
                    <button
                      onClick={() => addFeature(pkgIndex)}
                      className="flex items-center gap-1 text-sm text-primary-600 hover:text-primary-700 mt-2"
                    >
                      <Plus className="w-4 h-4" />
                      Add feature
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Company Details */}
        <section className="bg-white rounded-xl shadow p-6">
          <div className="flex items-center gap-2 mb-6">
            <Building className="w-5 h-5 text-primary-600" />
            <h2 className="text-lg font-semibold">Company Details (for Invoices)</h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Company Name
              </label>
              <input
                type="text"
                value={settings.company_details.name}
                onChange={(e) => setSettings(prev => ({
                  ...prev,
                  company_details: { ...prev.company_details, name: e.target.value }
                }))}
                className="w-full px-3 py-2 border rounded-lg"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                VAT/Trade License Number
              </label>
              <input
                type="text"
                value={settings.company_details.vat_number || ''}
                onChange={(e) => setSettings(prev => ({
                  ...prev,
                  company_details: { ...prev.company_details, vat_number: e.target.value }
                }))}
                className="w-full px-3 py-2 border rounded-lg"
              />
            </div>
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Address
              </label>
              <textarea
                value={settings.company_details.address}
                onChange={(e) => setSettings(prev => ({
                  ...prev,
                  company_details: { ...prev.company_details, address: e.target.value }
                }))}
                className="w-full px-3 py-2 border rounded-lg"
                rows={2}
              />
            </div>
          </div>
        </section>

        {/* Bank Details */}
        <section className="bg-white rounded-xl shadow p-6">
          <div className="flex items-center gap-2 mb-6">
            <CreditCard className="w-5 h-5 text-primary-600" />
            <h2 className="text-lg font-semibold">Bank Details</h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Bank Name
              </label>
              <input
                type="text"
                value={settings.company_details.bank_name || ''}
                onChange={(e) => setSettings(prev => ({
                  ...prev,
                  company_details: { ...prev.company_details, bank_name: e.target.value }
                }))}
                className="w-full px-3 py-2 border rounded-lg"
                placeholder="Wio Business"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Account Number / IBAN
              </label>
              <input
                type="text"
                value={settings.company_details.bank_account || ''}
                onChange={(e) => setSettings(prev => ({
                  ...prev,
                  company_details: { ...prev.company_details, bank_account: e.target.value }
                }))}
                className="w-full px-3 py-2 border rounded-lg"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                SWIFT/BIC
              </label>
              <input
                type="text"
                value={settings.company_details.swift || ''}
                onChange={(e) => setSettings(prev => ({
                  ...prev,
                  company_details: { ...prev.company_details, swift: e.target.value }
                }))}
                className="w-full px-3 py-2 border rounded-lg"
              />
            </div>
          </div>
        </section>
      </div>
    </div>
  )
}
