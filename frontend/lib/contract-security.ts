/**
 * Contract Security Utilities
 * Provides cryptographic signing, hashing, and audit logging for contracts
 */

/**
 * Signature metadata for legal compliance
 */
export interface SignatureMetadata {
  signedAt: string // ISO timestamp
  clientIP: string | null
  userAgent: string
  fingerprint: string // Browser fingerprint hash
  termsHash: string // SHA-256 hash of terms content
  signatureHash: string // SHA-256 hash of signature image
}

/**
 * Audit log entry for contract actions
 */
export interface AuditLogEntry {
  action: 'view' | 'accept' | 'sign' | 'download' | 'verify' | 'enroll'
  timestamp: string
  userId?: string
  leadId?: string
  email?: string
  metadata?: Record<string, unknown>
}

/**
 * Terms acceptance record
 */
export interface TermsAcceptance {
  termsVersion: string
  acceptedAt: string
  ipAddress: string | null
  userAgent: string
  signatureDataUrl?: string
}

/**
 * Generate SHA-256 hash of a string
 */
export async function sha256(message: string): Promise<string> {
  const msgBuffer = new TextEncoder().encode(message)
  const hashBuffer = await crypto.subtle.digest('SHA-256', msgBuffer)
  const hashArray = Array.from(new Uint8Array(hashBuffer))
  return hashArray.map((b) => b.toString(16).padStart(2, '0')).join('')
}

/**
 * Generate hash of terms content for integrity verification
 */
export async function generateTermsHash(termsContent: string): Promise<string> {
  const dataToHash = JSON.stringify({
    terms: termsContent,
    version: '1.0',
  })
  return sha256(dataToHash)
}

/**
 * Generate hash of signature image (base64)
 */
export async function generateSignatureHash(signatureBase64: string): Promise<string> {
  return sha256(signatureBase64)
}

/**
 * Generate a simple browser fingerprint
 */
export async function generateBrowserFingerprint(): Promise<string> {
  const components = [
    navigator.userAgent,
    navigator.language,
    screen.width,
    screen.height,
    screen.colorDepth,
    new Date().getTimezoneOffset(),
    navigator.hardwareConcurrency || 0,
    navigator.platform,
  ]

  return sha256(components.join('|'))
}

/**
 * Get client IP
 */
export async function getClientIP(): Promise<string | null> {
  try {
    const response = await fetch('https://api.ipify.org?format=json')
    const data = await response.json()
    return data.ip
  } catch {
    return null
  }
}

/**
 * Create complete signature metadata
 */
export async function createSignatureMetadata(
  termsContent: string,
  signatureBase64: string
): Promise<SignatureMetadata> {
  const [termsHash, signatureHash, fingerprint, clientIP] = await Promise.all([
    generateTermsHash(termsContent),
    generateSignatureHash(signatureBase64),
    generateBrowserFingerprint(),
    getClientIP(),
  ])

  return {
    signedAt: new Date().toISOString(),
    clientIP,
    userAgent: navigator.userAgent,
    fingerprint,
    termsHash,
    signatureHash,
  }
}

/**
 * Create terms acceptance record
 */
export async function createTermsAcceptance(
  termsVersion: string,
  signatureDataUrl?: string
): Promise<TermsAcceptance> {
  const clientIP = await getClientIP()

  return {
    termsVersion,
    acceptedAt: new Date().toISOString(),
    ipAddress: clientIP,
    userAgent: navigator.userAgent,
    signatureDataUrl,
  }
}

/**
 * Create audit log entry
 */
export function createAuditLogEntry(
  action: AuditLogEntry['action'],
  options?: {
    userId?: string
    leadId?: string
    email?: string
    additionalMetadata?: Record<string, unknown>
  }
): AuditLogEntry {
  return {
    action,
    timestamp: new Date().toISOString(),
    userId: options?.userId,
    leadId: options?.leadId,
    email: options?.email,
    metadata: {
      userAgent: typeof navigator !== 'undefined' ? navigator.userAgent : 'server',
      url: typeof window !== 'undefined' ? window.location.href : 'server',
      timezone: typeof Intl !== 'undefined' ? Intl.DateTimeFormat().resolvedOptions().timeZone : 'UTC',
      ...options?.additionalMetadata,
    },
  }
}

/**
 * Generate a lead/enrollment reference code
 * Format: AWA-YYYYMMDD-XXXX (e.g., AWA-20260207-A7B3)
 */
export function generateEnrollmentReference(): string {
  const date = new Date()
  const dateStr = date.toISOString().split('T')[0].replace(/-/g, '')
  const randomPart = Math.random().toString(36).substring(2, 6).toUpperCase()
  return `AWA-${dateStr}-${randomPart}`
}

/**
 * Format metadata for database storage
 */
export function formatMetadataForStorage(metadata: SignatureMetadata | TermsAcceptance | AuditLogEntry): string {
  return JSON.stringify(metadata)
}

/**
 * Parse metadata from database
 */
export function parseMetadataFromStorage<T>(stored: string): T | null {
  try {
    return JSON.parse(stored) as T
  } catch {
    return null
  }
}
