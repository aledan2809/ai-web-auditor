/**
 * Invoice/Proforma PDF Generator
 * Generates professional invoices for AI Web Auditor purchases
 */

// Types
export interface InvoiceData {
  invoiceNumber: string
  invoiceDate: string
  dueDate: string
  isProforma: boolean

  // Company details (seller)
  company: {
    name: string
    address: string
    vatNumber?: string
    bankName?: string
    bankAccount?: string
    swift?: string
    email?: string
    website?: string
  }

  // Customer details (buyer)
  customer: {
    name: string
    email: string
    address?: string
    vatNumber?: string
  }

  // Items
  items: {
    description: string
    quantity: number
    unitPrice: number
    total: number
  }[]

  // Totals
  subtotal: number
  vatRate: number
  vatAmount: number
  total: number
  currency: string

  // Payment info
  paymentMethod?: string
  paymentStatus?: 'pending' | 'paid'
  transactionId?: string

  // Notes
  notes?: string
}

export interface InvoiceGeneratorOptions {
  language?: 'en' | 'ro' | 'ar' | 'de' | 'es' | 'fr' | 'it'
}

// Labels in different languages
const LABELS: Record<string, Record<string, string>> = {
  en: {
    invoice: 'INVOICE',
    proforma: 'PROFORMA INVOICE',
    invoiceNumber: 'Invoice No.',
    date: 'Date',
    dueDate: 'Due Date',
    billTo: 'Bill To',
    from: 'From',
    description: 'Description',
    quantity: 'Qty',
    unitPrice: 'Unit Price',
    total: 'Total',
    subtotal: 'Subtotal',
    vat: 'VAT',
    grandTotal: 'Grand Total',
    paymentDetails: 'Payment Details',
    bankName: 'Bank',
    accountNumber: 'Account',
    swift: 'SWIFT/BIC',
    notes: 'Notes',
    thankYou: 'Thank you for your business!',
    paid: 'PAID',
    pending: 'PAYMENT PENDING'
  },
  ro: {
    invoice: 'FACTURA',
    proforma: 'FACTURA PROFORMA',
    invoiceNumber: 'Nr. Factura',
    date: 'Data',
    dueDate: 'Scadenta',
    billTo: 'Catre',
    from: 'De la',
    description: 'Descriere',
    quantity: 'Cant.',
    unitPrice: 'Pret Unitar',
    total: 'Total',
    subtotal: 'Subtotal',
    vat: 'TVA',
    grandTotal: 'Total de Plata',
    paymentDetails: 'Detalii Plata',
    bankName: 'Banca',
    accountNumber: 'Cont',
    swift: 'SWIFT/BIC',
    notes: 'Note',
    thankYou: 'Va multumim pentru incredere!',
    paid: 'ACHITAT',
    pending: 'IN ASTEPTAREA PLATII'
  },
  ar: {
    invoice: 'فاتورة',
    proforma: 'فاتورة أولية',
    invoiceNumber: 'رقم الفاتورة',
    date: 'التاريخ',
    dueDate: 'تاريخ الاستحقاق',
    billTo: 'إلى',
    from: 'من',
    description: 'الوصف',
    quantity: 'الكمية',
    unitPrice: 'سعر الوحدة',
    total: 'المجموع',
    subtotal: 'المجموع الفرعي',
    vat: 'ضريبة القيمة المضافة',
    grandTotal: 'المجموع الكلي',
    paymentDetails: 'تفاصيل الدفع',
    bankName: 'البنك',
    accountNumber: 'رقم الحساب',
    swift: 'سويفت',
    notes: 'ملاحظات',
    thankYou: 'شكراً لتعاملكم معنا!',
    paid: 'مدفوع',
    pending: 'في انتظار الدفع'
  }
}

// Generate invoice number
export function generateInvoiceNumber(prefix = 'AWA'): string {
  const date = new Date()
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const random = Math.floor(Math.random() * 10000).toString().padStart(4, '0')
  return `${prefix}-${year}${month}-${random}`
}

// Format currency
function formatCurrency(amount: number, currency: string): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: currency,
    minimumFractionDigits: 2
  }).format(amount)
}

// Format date
function formatDate(date: string, language: string): string {
  const d = new Date(date)
  const options: Intl.DateTimeFormatOptions = {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  }
  const locale = language === 'ar' ? 'ar-AE' : language === 'ro' ? 'ro-RO' : 'en-US'
  return d.toLocaleDateString(locale, options)
}

/**
 * Generate invoice HTML (can be used for PDF generation or preview)
 */
export function generateInvoiceHTML(
  data: InvoiceData,
  options: InvoiceGeneratorOptions = {}
): string {
  const lang = options.language || 'en'
  const labels = LABELS[lang] || LABELS.en
  const isRTL = lang === 'ar'

  const html = `
<!DOCTYPE html>
<html dir="${isRTL ? 'rtl' : 'ltr'}" lang="${lang}">
<head>
  <meta charset="UTF-8">
  <title>${data.isProforma ? labels.proforma : labels.invoice} ${data.invoiceNumber}</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: 'Segoe UI', Tahoma, sans-serif;
      font-size: 12px;
      line-height: 1.5;
      color: #333;
      padding: 40px;
      direction: ${isRTL ? 'rtl' : 'ltr'};
    }
    .invoice-header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      margin-bottom: 40px;
      padding-bottom: 20px;
      border-bottom: 3px solid #3b82f6;
    }
    .company-info h1 {
      font-size: 24px;
      color: #1e40af;
      margin-bottom: 8px;
    }
    .company-info p {
      color: #666;
      font-size: 11px;
    }
    .invoice-title {
      text-align: ${isRTL ? 'left' : 'right'};
    }
    .invoice-title h2 {
      font-size: 28px;
      color: #3b82f6;
      margin-bottom: 10px;
    }
    .invoice-meta {
      font-size: 11px;
      color: #666;
    }
    .invoice-meta strong {
      color: #333;
    }
    .addresses {
      display: flex;
      justify-content: space-between;
      margin-bottom: 30px;
    }
    .address-block {
      width: 45%;
    }
    .address-block h3 {
      font-size: 11px;
      text-transform: uppercase;
      color: #666;
      margin-bottom: 8px;
      padding-bottom: 4px;
      border-bottom: 1px solid #e5e5e5;
    }
    .address-block p {
      margin-bottom: 4px;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      margin-bottom: 30px;
    }
    th {
      background: #f8fafc;
      padding: 12px;
      text-align: ${isRTL ? 'right' : 'left'};
      font-weight: 600;
      border-bottom: 2px solid #e2e8f0;
      font-size: 11px;
      text-transform: uppercase;
      color: #64748b;
    }
    td {
      padding: 12px;
      border-bottom: 1px solid #f1f5f9;
    }
    .text-right { text-align: ${isRTL ? 'left' : 'right'}; }
    .totals {
      width: 300px;
      margin-${isRTL ? 'right' : 'left'}: auto;
    }
    .totals tr td {
      padding: 8px 12px;
    }
    .totals .grand-total {
      font-size: 16px;
      font-weight: bold;
      background: #3b82f6;
      color: white;
    }
    .payment-details {
      background: #f8fafc;
      padding: 20px;
      border-radius: 8px;
      margin-bottom: 20px;
    }
    .payment-details h3 {
      font-size: 14px;
      margin-bottom: 12px;
      color: #1e40af;
    }
    .payment-grid {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 16px;
    }
    .payment-item label {
      font-size: 10px;
      text-transform: uppercase;
      color: #64748b;
    }
    .payment-item p {
      font-weight: 500;
    }
    .notes {
      padding: 16px;
      background: #fffbeb;
      border-radius: 8px;
      margin-bottom: 20px;
    }
    .notes h3 {
      font-size: 12px;
      margin-bottom: 8px;
      color: #92400e;
    }
    .footer {
      text-align: center;
      padding-top: 20px;
      border-top: 1px solid #e5e5e5;
      color: #666;
      font-size: 11px;
    }
    .status-badge {
      display: inline-block;
      padding: 4px 12px;
      border-radius: 4px;
      font-weight: 600;
      font-size: 11px;
    }
    .status-paid {
      background: #dcfce7;
      color: #166534;
    }
    .status-pending {
      background: #fef3c7;
      color: #92400e;
    }
  </style>
</head>
<body>
  <div class="invoice-header">
    <div class="company-info">
      <h1>${data.company.name}</h1>
      <p>${data.company.address}</p>
      ${data.company.vatNumber ? `<p>VAT: ${data.company.vatNumber}</p>` : ''}
      ${data.company.email ? `<p>${data.company.email}</p>` : ''}
      ${data.company.website ? `<p>${data.company.website}</p>` : ''}
    </div>
    <div class="invoice-title">
      <h2>${data.isProforma ? labels.proforma : labels.invoice}</h2>
      <div class="invoice-meta">
        <p><strong>${labels.invoiceNumber}:</strong> ${data.invoiceNumber}</p>
        <p><strong>${labels.date}:</strong> ${formatDate(data.invoiceDate, lang)}</p>
        <p><strong>${labels.dueDate}:</strong> ${formatDate(data.dueDate, lang)}</p>
        <p style="margin-top: 8px;">
          <span class="status-badge ${data.paymentStatus === 'paid' ? 'status-paid' : 'status-pending'}">
            ${data.paymentStatus === 'paid' ? labels.paid : labels.pending}
          </span>
        </p>
      </div>
    </div>
  </div>

  <div class="addresses">
    <div class="address-block">
      <h3>${labels.billTo}</h3>
      <p><strong>${data.customer.name}</strong></p>
      <p>${data.customer.email}</p>
      ${data.customer.address ? `<p>${data.customer.address}</p>` : ''}
      ${data.customer.vatNumber ? `<p>VAT: ${data.customer.vatNumber}</p>` : ''}
    </div>
  </div>

  <table>
    <thead>
      <tr>
        <th>${labels.description}</th>
        <th class="text-right">${labels.quantity}</th>
        <th class="text-right">${labels.unitPrice}</th>
        <th class="text-right">${labels.total}</th>
      </tr>
    </thead>
    <tbody>
      ${data.items.map(item => `
        <tr>
          <td>${item.description}</td>
          <td class="text-right">${item.quantity}</td>
          <td class="text-right">${formatCurrency(item.unitPrice, data.currency)}</td>
          <td class="text-right">${formatCurrency(item.total, data.currency)}</td>
        </tr>
      `).join('')}
    </tbody>
  </table>

  <table class="totals">
    <tr>
      <td>${labels.subtotal}</td>
      <td class="text-right">${formatCurrency(data.subtotal, data.currency)}</td>
    </tr>
    ${data.vatRate > 0 ? `
      <tr>
        <td>${labels.vat} (${data.vatRate}%)</td>
        <td class="text-right">${formatCurrency(data.vatAmount, data.currency)}</td>
      </tr>
    ` : ''}
    <tr class="grand-total">
      <td>${labels.grandTotal}</td>
      <td class="text-right">${formatCurrency(data.total, data.currency)}</td>
    </tr>
  </table>

  ${data.company.bankAccount ? `
    <div class="payment-details">
      <h3>${labels.paymentDetails}</h3>
      <div class="payment-grid">
        <div class="payment-item">
          <label>${labels.bankName}</label>
          <p>${data.company.bankName}</p>
        </div>
        <div class="payment-item">
          <label>${labels.accountNumber}</label>
          <p>${data.company.bankAccount}</p>
        </div>
        ${data.company.swift ? `
          <div class="payment-item">
            <label>${labels.swift}</label>
            <p>${data.company.swift}</p>
          </div>
        ` : ''}
      </div>
    </div>
  ` : ''}

  ${data.notes ? `
    <div class="notes">
      <h3>${labels.notes}</h3>
      <p>${data.notes}</p>
    </div>
  ` : ''}

  <div class="footer">
    <p>${labels.thankYou}</p>
    ${data.transactionId ? `<p style="margin-top: 4px; font-size: 10px;">Transaction ID: ${data.transactionId}</p>` : ''}
  </div>
</body>
</html>
  `

  return html
}

/**
 * Create invoice data from a lead/payment
 */
export function createInvoiceFromLead(
  leadData: {
    email: string
    name: string
    packageName: string
    packagePrice: number
    currency: string
  },
  companySettings: InvoiceData['company'],
  options?: {
    isProforma?: boolean
    vatRate?: number
    transactionId?: string
  }
): InvoiceData {
  const subtotal = leadData.packagePrice
  const vatRate = options?.vatRate || 0
  const vatAmount = subtotal * (vatRate / 100)
  const total = subtotal + vatAmount

  const today = new Date()
  const dueDate = new Date(today)
  dueDate.setDate(dueDate.getDate() + 30)

  return {
    invoiceNumber: generateInvoiceNumber(),
    invoiceDate: today.toISOString(),
    dueDate: dueDate.toISOString(),
    isProforma: options?.isProforma ?? true,

    company: companySettings,

    customer: {
      name: leadData.name,
      email: leadData.email
    },

    items: [
      {
        description: `AI Web Auditor - ${leadData.packageName} Package`,
        quantity: 1,
        unitPrice: leadData.packagePrice,
        total: leadData.packagePrice
      }
    ],

    subtotal,
    vatRate,
    vatAmount,
    total,
    currency: leadData.currency,

    paymentStatus: options?.isProforma ? 'pending' : 'paid',
    transactionId: options?.transactionId
  }
}
