/**
 * Email Service for AI Web Auditor
 * Handles sending contracts, invoices, and audit reports via email
 */

import { generateInvoiceHTML, InvoiceData, createInvoiceFromLead } from '../pdf/invoice-generator'

// Email types
export interface EmailRecipient {
  email: string
  name: string
}

export interface EmailAttachment {
  filename: string
  content: string // Base64 encoded
  contentType: string
}

export interface SendEmailRequest {
  to: EmailRecipient
  subject: string
  htmlContent: string
  textContent?: string
  attachments?: EmailAttachment[]
  replyTo?: string
}

export interface EmailTemplate {
  subject: string
  html: string
  text?: string
}

// Email templates in different languages
const EMAIL_TEMPLATES = {
  en: {
    welcome: {
      subject: 'Welcome to AI Web Auditor - Your Report is Ready!',
      greeting: 'Hello',
      intro: 'Thank you for using AI Web Auditor! Your website audit is complete.',
      reportReady: 'Your full audit report is now available.',
      viewReport: 'View Your Report',
      attachedDocs: 'Attached Documents:',
      questions: 'If you have any questions, please reply to this email.',
      regards: 'Best regards,',
      team: 'The AI Web Auditor Team'
    },
    invoice: {
      subject: 'Invoice #{invoiceNumber} - AI Web Auditor',
      greeting: 'Dear',
      intro: 'Please find attached your invoice for the AI Web Auditor service.',
      paymentInfo: 'Payment Details',
      dueDate: 'Due Date',
      amount: 'Amount Due',
      questions: 'For billing inquiries, please contact us.',
      regards: 'Best regards,',
      team: 'AI Web Auditor Billing'
    },
    proforma: {
      subject: 'Proforma Invoice #{invoiceNumber} - AI Web Auditor',
      greeting: 'Dear',
      intro: 'Please find attached your proforma invoice for the AI Web Auditor service.',
      paymentInfo: 'To complete your purchase, please make payment using the details below.',
      questions: 'Once payment is received, you will receive your full audit report.',
      regards: 'Best regards,',
      team: 'AI Web Auditor Team'
    }
  },
  ro: {
    welcome: {
      subject: 'Bun venit la AI Web Auditor - Raportul tau este gata!',
      greeting: 'Buna',
      intro: 'Multumim ca folosesti AI Web Auditor! Auditul website-ului tau este complet.',
      reportReady: 'Raportul complet de audit este acum disponibil.',
      viewReport: 'Vezi Raportul',
      attachedDocs: 'Documente Atasate:',
      questions: 'Daca ai intrebari, te rugam sa raspunzi la acest email.',
      regards: 'Cu respect,',
      team: 'Echipa AI Web Auditor'
    },
    invoice: {
      subject: 'Factura #{invoiceNumber} - AI Web Auditor',
      greeting: 'Stimate/Stimata',
      intro: 'Gasesti atasat factura pentru serviciul AI Web Auditor.',
      paymentInfo: 'Detalii Plata',
      dueDate: 'Scadenta',
      amount: 'Suma de Plata',
      questions: 'Pentru intrebari legate de facturare, te rugam sa ne contactezi.',
      regards: 'Cu respect,',
      team: 'AI Web Auditor Facturare'
    },
    proforma: {
      subject: 'Factura Proforma #{invoiceNumber} - AI Web Auditor',
      greeting: 'Stimate/Stimata',
      intro: 'Gasesti atasat factura proforma pentru serviciul AI Web Auditor.',
      paymentInfo: 'Pentru a finaliza achizitia, te rugam sa efectuezi plata folosind detaliile de mai jos.',
      questions: 'Odata ce plata este primita, vei primi raportul complet de audit.',
      regards: 'Cu respect,',
      team: 'Echipa AI Web Auditor'
    }
  }
}

/**
 * Generate welcome email with audit report
 */
export function generateWelcomeEmail(
  recipient: EmailRecipient,
  auditUrl: string,
  language: 'en' | 'ro' = 'en'
): EmailTemplate {
  const t = EMAIL_TEMPLATES[language]?.welcome || EMAIL_TEMPLATES.en.welcome

  const html = `
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; }
    .container { max-width: 600px; margin: 0 auto; padding: 20px; }
    .header { background: linear-gradient(135deg, #3b82f6, #1d4ed8); color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0; }
    .header h1 { margin: 0; font-size: 24px; }
    .content { background: #f9fafb; padding: 30px; border-radius: 0 0 8px 8px; }
    .button { display: inline-block; background: #3b82f6; color: white; padding: 14px 28px; text-decoration: none; border-radius: 6px; font-weight: 600; margin: 20px 0; }
    .button:hover { background: #2563eb; }
    .footer { text-align: center; margin-top: 20px; font-size: 12px; color: #666; }
    .highlight { background: #dbeafe; padding: 15px; border-radius: 6px; margin: 15px 0; }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>AI Web Auditor</h1>
    </div>
    <div class="content">
      <p>${t.greeting} ${recipient.name},</p>
      <p>${t.intro}</p>

      <div class="highlight">
        <strong>${t.reportReady}</strong>
      </div>

      <p style="text-align: center;">
        <a href="${auditUrl}" class="button">${t.viewReport}</a>
      </p>

      <p>${t.questions}</p>

      <p>
        ${t.regards}<br>
        <strong>${t.team}</strong>
      </p>
    </div>
    <div class="footer">
      <p>&copy; ${new Date().getFullYear()} AI Web Auditor. All rights reserved.</p>
    </div>
  </div>
</body>
</html>
  `

  return {
    subject: t.subject,
    html,
    text: `${t.greeting} ${recipient.name},\n\n${t.intro}\n\n${t.reportReady}\n\nView your report: ${auditUrl}\n\n${t.questions}\n\n${t.regards}\n${t.team}`
  }
}

/**
 * Generate invoice email
 */
export function generateInvoiceEmail(
  recipient: EmailRecipient,
  invoiceData: InvoiceData,
  language: 'en' | 'ro' = 'en'
): EmailTemplate {
  const templateKey = invoiceData.isProforma ? 'proforma' : 'invoice'
  const t = EMAIL_TEMPLATES[language]?.[templateKey] || EMAIL_TEMPLATES.en[templateKey]

  const subject = t.subject.replace('{invoiceNumber}', invoiceData.invoiceNumber)

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: invoiceData.currency,
      minimumFractionDigits: 2
    }).format(amount)
  }

  const html = `
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; }
    .container { max-width: 600px; margin: 0 auto; padding: 20px; }
    .header { background: #1e3a5f; color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0; }
    .header h1 { margin: 0; font-size: 24px; }
    .content { background: #f9fafb; padding: 30px; border-radius: 0 0 8px 8px; }
    .info-box { background: white; padding: 20px; border-radius: 6px; margin: 20px 0; border: 1px solid #e5e7eb; }
    .info-row { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #f3f4f6; }
    .info-row:last-child { border-bottom: none; }
    .total-row { font-size: 18px; font-weight: bold; color: #1e3a5f; }
    .footer { text-align: center; margin-top: 20px; font-size: 12px; color: #666; }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>${invoiceData.isProforma ? 'Proforma Invoice' : 'Invoice'}</h1>
      <p style="margin: 5px 0 0; opacity: 0.8;">#${invoiceData.invoiceNumber}</p>
    </div>
    <div class="content">
      <p>${t.greeting} ${recipient.name},</p>
      <p>${t.intro}</p>

      <div class="info-box">
        <div class="info-row">
          <span>${t.dueDate || 'Due Date'}:</span>
          <span>${new Date(invoiceData.dueDate).toLocaleDateString()}</span>
        </div>
        <div class="info-row total-row">
          <span>${t.amount || 'Amount Due'}:</span>
          <span>${formatCurrency(invoiceData.total)}</span>
        </div>
      </div>

      <p>${t.paymentInfo}</p>

      ${invoiceData.company.bankAccount ? `
        <div class="info-box">
          <p><strong>Bank:</strong> ${invoiceData.company.bankName}</p>
          <p><strong>Account:</strong> ${invoiceData.company.bankAccount}</p>
          ${invoiceData.company.swift ? `<p><strong>SWIFT:</strong> ${invoiceData.company.swift}</p>` : ''}
        </div>
      ` : ''}

      <p>${t.questions}</p>

      <p>
        ${t.regards}<br>
        <strong>${t.team}</strong>
      </p>
    </div>
    <div class="footer">
      <p>&copy; ${new Date().getFullYear()} AI Web Auditor. All rights reserved.</p>
    </div>
  </div>
</body>
</html>
  `

  return {
    subject,
    html,
    text: `${t.greeting} ${recipient.name},\n\n${t.intro}\n\nInvoice: ${invoiceData.invoiceNumber}\nAmount: ${formatCurrency(invoiceData.total)}\nDue Date: ${new Date(invoiceData.dueDate).toLocaleDateString()}\n\n${t.questions}\n\n${t.regards}\n${t.team}`
  }
}

/**
 * API call to send email (backend integration)
 */
export async function sendEmail(request: SendEmailRequest): Promise<{ success: boolean; messageId?: string; error?: string }> {
  try {
    const response = await fetch('/api/email/send', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(request)
    })

    if (!response.ok) {
      const error = await response.json()
      return { success: false, error: error.message || 'Failed to send email' }
    }

    const result = await response.json()
    return { success: true, messageId: result.messageId }
  } catch (error) {
    console.error('Email send error:', error)
    return { success: false, error: 'Network error' }
  }
}

/**
 * Send welcome email with audit report
 */
export async function sendWelcomeEmail(
  recipient: EmailRecipient,
  auditUrl: string,
  language: 'en' | 'ro' = 'en'
): Promise<{ success: boolean; error?: string }> {
  const template = generateWelcomeEmail(recipient, auditUrl, language)

  return sendEmail({
    to: recipient,
    subject: template.subject,
    htmlContent: template.html,
    textContent: template.text
  })
}

/**
 * Send invoice email with PDF attachment
 */
export async function sendInvoiceEmail(
  recipient: EmailRecipient,
  invoiceData: InvoiceData,
  language: 'en' | 'ro' = 'en'
): Promise<{ success: boolean; error?: string }> {
  const template = generateInvoiceEmail(recipient, invoiceData, language)

  // Generate invoice HTML for PDF
  const invoiceHTML = generateInvoiceHTML(invoiceData, { language })

  // Convert HTML to base64 for attachment
  const htmlBase64 = btoa(unescape(encodeURIComponent(invoiceHTML)))

  return sendEmail({
    to: recipient,
    subject: template.subject,
    htmlContent: template.html,
    textContent: template.text,
    attachments: [
      {
        filename: `${invoiceData.isProforma ? 'Proforma' : 'Invoice'}-${invoiceData.invoiceNumber}.html`,
        content: htmlBase64,
        contentType: 'text/html'
      }
    ]
  })
}
