import axios from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'

export const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // Important for cookies
})

// ============== TYPES ==============

export interface User {
  id: string
  email: string
  name?: string
  role: string
  credits: number
  created_at: string
}

export interface AuditRequest {
  url: string
  audit_types?: string[]
  include_screenshots?: boolean
  mobile_test?: boolean
}

export interface AuditIssue {
  id: string
  category: string
  severity: 'critical' | 'high' | 'medium' | 'low' | 'info'
  title: string
  description: string
  recommendation: string
  estimated_hours: number
  complexity: string
}

export interface AuditResult {
  id: string
  url: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  created_at: string
  completed_at?: string
  overall_score: number
  performance_score?: number
  seo_score?: number
  security_score?: number
  gdpr_score?: number
  accessibility_score?: number
  issues: AuditIssue[]
  desktop_screenshot?: string
  mobile_screenshot?: string
}

export interface AuditListItem {
  id: string
  url: string
  status: string
  overall_score: number
  performance_score?: number
  seo_score?: number
  security_score?: number
  gdpr_score?: number
  accessibility_score?: number
  issues_count: number
  created_at: string
  completed_at?: string
}

export interface PriceEstimate {
  audit_id: string
  total_issues: number
  issues_by_severity: Record<string, number>
  total_hours: number
  hours_by_category: Record<string, number>
  currency: string
  hourly_rate: number
  subtotal: number
  discount_percent: number
  total_price: number
  items: any[]
  priority_order: string[]
  quick_wins: string[]
  ai_summary: string
}

export interface Product {
  id: string
  name: string
  price: number
  credits?: number
  credits_per_month?: number
  description: string
  mode: string
}

export interface Payment {
  id: string
  amount: number
  currency: string
  status: string
  product_type?: string
  credits_added: number
  created_at: string
}

export interface DashboardStats {
  users: { total: number; new_this_month: number; active: number }
  audits: { total: number; this_month: number; avg_score: number; by_status: Record<string, number> }
  revenue: { total: number; this_month: number; mrr: number }
  top_issues: { title: string; count: number }[]
}

// ============== AUTH API ==============

export const authApi = {
  register: (email: string, password: string, name?: string) =>
    api.post<User>('/api/auth/register', { email, password, name }),

  login: (email: string, password: string) =>
    api.post<User>('/api/auth/login', { email, password }),

  logout: () =>
    api.post('/api/auth/logout'),

  me: () =>
    api.get<User>('/api/auth/me'),

  refresh: () =>
    api.post('/api/auth/refresh'),
}

// ============== AUDIT API ==============

export const auditApi = {
  start: (data: AuditRequest) =>
    api.post<{ success: boolean; audit_id: string; message: string; status: string }>(
      '/api/audit/start',
      data
    ),

  getStatus: (auditId: string) =>
    api.get<AuditResult>(`/api/audit/${auditId}`),

  getList: (page = 1, limit = 20, filters?: { status?: string; url_search?: string; min_score?: number }) =>
    api.get<{ total: number; page: number; limit: number; pages: number; audits: AuditListItem[] }>('/api/audits', {
      params: { page, limit, ...filters }
    }),

  delete: (auditId: string) =>
    api.delete(`/api/audit/${auditId}`),

  rerun: (auditId: string) =>
    api.post<{ success: boolean; audit_id: string }>(`/api/audit/${auditId}/rerun`),

  downloadPdf: (auditId: string) =>
    api.get(`/api/audit/${auditId}/pdf`, { responseType: 'blob' }),
}

// ============== ESTIMATE API ==============

export const estimateApi = {
  getEstimate: (auditId: string, hourlyRate = 75, currency = 'EUR') =>
    api.post<PriceEstimate>('/api/estimate', {
      audit_id: auditId,
      hourly_rate: hourlyRate,
      currency: currency
    }),
}

// ============== PAYMENTS API ==============

export const paymentsApi = {
  getProducts: () =>
    api.get<Product[]>('/api/payments/products'),

  createCheckout: (productType: string) =>
    api.post<{ checkout_url: string; session_id: string }>('/api/payments/create-checkout', {
      product_type: productType
    }),

  getHistory: () =>
    api.get<Payment[]>('/api/payments/history'),

  cancelSubscription: () =>
    api.post('/api/payments/cancel-subscription'),
}

// ============== WEBSITE GURU INTEGRATION ==============

const WEBSITE_GURU_URL = process.env.NEXT_PUBLIC_WEBSITE_GURU_URL || 'http://localhost:3000'

export const websiteGuruApi = {
  sendAudit: async (audit: AuditResult) => {
    const response = await fetch(`${WEBSITE_GURU_URL}/api/import-audit`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        url: audit.url,
        overall_score: audit.overall_score,
        performance_score: audit.performance_score,
        seo_score: audit.seo_score,
        security_score: audit.security_score,
        gdpr_score: audit.gdpr_score,
        accessibility_score: audit.accessibility_score,
        issues: audit.issues.map(issue => ({
          category: issue.category,
          severity: issue.severity,
          title: issue.title,
          description: issue.description,
          recommendation: issue.recommendation,
          estimated_hours: issue.estimated_hours,
          complexity: issue.complexity
        })),
        source: 'ai-web-auditor',
        source_audit_id: audit.id
      })
    })
    return response.json()
  }
}

// ============== ADMIN API ==============

export const adminApi = {
  getStats: () =>
    api.get<DashboardStats>('/api/admin/stats'),

  getUsers: (page = 1, limit = 20, search?: string, role?: string) =>
    api.get('/api/admin/users', { params: { page, limit, search, role } }),

  getUser: (userId: string) =>
    api.get(`/api/admin/users/${userId}`),

  updateUser: (userId: string, data: { role?: string; credits?: number; is_active?: boolean }) =>
    api.patch(`/api/admin/users/${userId}`, data),

  deleteUser: (userId: string) =>
    api.delete(`/api/admin/users/${userId}`),

  getAllAudits: (page = 1, limit = 20, status?: string) =>
    api.get('/api/admin/audits', { params: { page, limit, status } }),

  getAllPayments: (page = 1, limit = 20, status?: string) =>
    api.get('/api/admin/payments', { params: { page, limit, status } }),
}

// ============== LEAD CAPTURE API ==============

export interface Lead {
  id: string
  email: string
  name: string
  language: string
  url: string
  audit_id: string
  package_id: string
  selected_audits: string[]
  signature_data?: string
  terms_accepted_at: string
  newsletter_consent: boolean
  status: 'pending' | 'verified' | 'converted' | 'churned'
  created_at: string
  converted_at?: string
}

export interface EnrollmentRequest {
  email: string
  name: string
  language: string
  audit_id: string
  package_id: string
  selected_audits: string[]
  signature_data?: string
  newsletter_consent: boolean
  fingerprint?: string
  ip_address?: string
  user_agent?: string
  terms_hash?: string
}

export interface PackageConfig {
  id: string
  name: string
  price: number
  currency: string
  audits_included: number
  total_audits: number
  features: string[]
  popular?: boolean
  requires_share?: boolean
  pdf_type: 'none' | 'basic' | 'professional'
  is_active: boolean
}

export const leadsApi = {
  // Create a new lead (enrollment)
  createLead: (data: EnrollmentRequest) =>
    api.post<{ success: boolean; lead_id: string; reference: string }>('/api/leads/enroll', data),

  // Get lead status
  getLeadStatus: (leadId: string) =>
    api.get<Lead>(`/api/leads/${leadId}`),

  // Verify email
  verifyEmail: (token: string) =>
    api.post<{ success: boolean }>('/api/leads/verify-email', { token }),

  // Get available packages (public)
  getPackages: () =>
    api.get<PackageConfig[]>('/api/packages'),
}

// ============== SUPER ADMIN SETTINGS API ==============

export interface PricingSettings {
  packages: PackageConfig[]
  hourly_rate: number
  currency: string
  vat_rate: number
  company_details: {
    name: string
    address: string
    vat_number?: string
    bank_name?: string
    bank_account?: string
    swift?: string
  }
}

export const settingsApi = {
  // Get pricing settings
  getPricingSettings: () =>
    api.get<PricingSettings>('/api/admin/settings/pricing'),

  // Update pricing settings
  updatePricingSettings: (data: Partial<PricingSettings>) =>
    api.patch<PricingSettings>('/api/admin/settings/pricing', data),

  // Update single package
  updatePackage: (packageId: string, data: Partial<PackageConfig>) =>
    api.patch<PackageConfig>(`/api/admin/settings/packages/${packageId}`, data),
}

// ============== COMPETITOR MONITORING API ==============

export interface Competitor {
  id: string
  name: string
  url: string
  domain: string
  is_active: boolean
  monitor_frequency: 'daily' | 'weekly' | 'monthly'
  latest_overall_score?: number
  latest_performance_score?: number
  latest_seo_score?: number
  latest_security_score?: number
  latest_gdpr_score?: number
  latest_accessibility_score?: number
  score_change: number
  last_audit_at?: string
  created_at: string
}

export interface CompetitorAudit {
  id: string
  overall_score: number
  performance_score?: number
  seo_score?: number
  security_score?: number
  gdpr_score?: number
  accessibility_score?: number
  score_change: number
  created_at: string
}

export interface ComparisonData {
  my_url: string
  my_scores: {
    overall: number
    performance?: number
    seo?: number
    security?: number
    gdpr?: number
    accessibility?: number
  }
  competitors: {
    id: string
    name: string
    url: string
    domain: string
    scores: {
      overall: number
      performance?: number
      seo?: number
      security?: number
      gdpr?: number
      accessibility?: number
    }
    score_change: number
    last_audit_at?: string
  }[]
}

export const competitorsApi = {
  // Get all competitors
  getCompetitors: () =>
    api.get<Competitor[]>('/api/competitors'),

  // Add a new competitor
  addCompetitor: (name: string, url: string, monitor_frequency: string = 'weekly') =>
    api.post<Competitor>('/api/competitors', { name, url, monitor_frequency }),

  // Get a specific competitor
  getCompetitor: (competitorId: string) =>
    api.get<Competitor>(`/api/competitors/${competitorId}`),

  // Update a competitor
  updateCompetitor: (competitorId: string, data: { name?: string; is_active?: boolean; monitor_frequency?: string }) =>
    api.patch<Competitor>(`/api/competitors/${competitorId}`, data),

  // Delete a competitor
  deleteCompetitor: (competitorId: string) =>
    api.delete(`/api/competitors/${competitorId}`),

  // Get competitor audit history
  getCompetitorHistory: (competitorId: string, limit: number = 30) =>
    api.get<CompetitorAudit[]>(`/api/competitors/${competitorId}/history`, { params: { limit } }),

  // Trigger a new audit for a competitor
  triggerAudit: (competitorId: string) =>
    api.post<{ success: boolean; audit_id: string }>(`/api/competitors/${competitorId}/audit`),

  // Compare with all competitors
  getComparison: (myAuditId?: string) =>
    api.get<ComparisonData>('/api/competitors/compare/all', { params: { my_audit_id: myAuditId } }),
}
