# AI Web Auditor

Platformă AI pentru audit automat de website-uri cu generare de rapoarte și estimări de preț.

## Funcționalități

### Audituri Disponibile

| Modul | Descriere | Metrici |
|-------|-----------|---------|
| **Performance** | Lighthouse, Core Web Vitals | LCP, FID, CLS, TTFB, Speed Index |
| **SEO** | Meta tags, structură, sitemap | Title, Description, H1-H6, robots.txt |
| **Security** | Headers, SSL, vulnerabilități | HTTPS, CSP, XSS, CORS, cookies |
| **GDPR** | Cookie consent, privacy policy | Tracking scripts, data collection |
| **Accessibility** | WCAG 2.1 compliance | Contrast, aria labels, keyboard nav |
| **UI/UX** | Design patterns, responsive | Mobile-friendly, broken links |
| **API Testing** | Endpoint validation | Response time, status codes, schemas |

### Caracteristici Business

- **Rapoarte PDF** profesionale pentru clienți
- **Estimări de preț** pentru reparații
- **Comparație** cu concurența
- **Monitorizare** programată (daily/weekly)
- **White-label** pentru agenții

## Tech Stack

- **Frontend**: Next.js 14, TailwindCSS, Recharts
- **Backend**: FastAPI, Python 3.11+
- **AI**: Claude API (Anthropic)
- **Database**: SQLite (dev) / PostgreSQL (prod)
- **Tools**: Playwright, Lighthouse, aXe

## Quick Start

```bash
# Backend
cd backend
pip install -r requirements.txt
python main.py

# Frontend
cd frontend
npm install
npm run dev
```

## Structură Proiect

```
AIWebAuditor/
├── backend/
│   ├── main.py              # FastAPI app
│   ├── auditors/            # Audit modules
│   │   ├── performance.py   # Lighthouse integration
│   │   ├── seo.py          # SEO checks
│   │   ├── security.py     # Security scanner
│   │   ├── gdpr.py         # GDPR compliance
│   │   ├── accessibility.py # a11y checks
│   │   └── api_tester.py   # API endpoint testing
│   ├── ai/
│   │   └── analyzer.py     # Claude AI analysis
│   ├── reports/
│   │   └── generator.py    # PDF report generator
│   └── models/
│       └── schemas.py      # Pydantic models
├── frontend/
│   ├── app/                # Next.js pages
│   ├── components/         # React components
│   └── lib/               # API client
└── docs/
    └── pricing.md         # Pricing model documentation
```

## API Endpoints

```
POST /api/audit/start      # Start new audit
GET  /api/audit/{id}       # Get audit status/results
GET  /api/audit/{id}/pdf   # Download PDF report
POST /api/estimate         # Get price estimate for fixes
```

## License

Proprietary - All rights reserved
