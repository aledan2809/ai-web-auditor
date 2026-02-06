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
