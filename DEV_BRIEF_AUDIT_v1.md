# DEV BRIEF — /audit Dev (AI Web Auditor surface) (V1)
**Scope:** Build/own the **AI Web Auditor experience** end-to-end inside AVE platform (engine), and ensure `/audit` page behaves as the correct module entry point.  
**You do NOT need to build WordPress pages** (AVE dev will). You must ensure the audit pipeline + APIs are correct.

---

## 1) Role of /audit (product + UX)
/audit is a focused landing for people who want the tool **now**:
- “scan my site”
- “show me issues & priorities”
- “unlock full report”

**Rule:** /audit is audit-centric. No suite-selling above the fold.

---

## 2) System boundaries
- WordPress `/audit` only submits `{websiteUrl,email,consent}` and renders teaser.
- All crawling, scoring, evidence, report generation lives in `app.techbiz.ae`.

---

## 3) Minimum audit pipeline (V1)
### Crawl
- fetch homepage HTML
- discover up to 10 internal links (same host) OR sitemap if present
- fetch basic headers + status codes
- stop early if blocked; set `teaser_limited`

### Checks (V1 minimum)
Produce enough data for:
- Overall score
- 3 component cards preview (ex: Performance, SEO, Trust)
- Hidden issues count (for upsell)

**Suggested check sources**
- Performance/CWV: PageSpeed Insights API OR Lighthouse headless (worker)
- SEO on-page: parse HTML (title/meta/H1/canonical/robots)
- Trust: presence of contact info, privacy/terms links, consistent phone/email, WhatsApp presence
- Security basics: https, mixed content, basic security headers if visible

### Confidence gating
- `confidence < 0.6` → label as estimated
- blocked/partial crawl → `teaser_limited`

---

## 4) Required output contract (teaser)
`GET /api/audit/{auditId}/teaser` must return:
- `status`: teaser_ready | teaser_limited | failed
- `overallScore` (0–100)
- `components` (exactly 3 for preview):
  - `{ id, name, score, topIssues:[{issueId,title,impact,confidence}] }`
- `hiddenCount` (int)
- `pricing` (AED snapshot)
- `message` (if limited)

---

## 5) Report contract (post-unlock)
When unlocked:
- generate full report with 9 components (as per scoring model)
- store evidence pointers
- expose:
  - `GET /api/audit/{auditId}/report`
  - and UI: `GET /report/{auditId}?token=...`

---

## 6) Pricing + unlock behavior (V1)
- v1 can use manual unlock (admin) to ship fast
- keep statuses ready for Stripe later:
  - unlock_pending → unlocked → report_ready

---

## 7) Competitor gap (V1)
- Use SerpAPI/DataForSEO (as decided) OR allow manual competitor override
- If competitor missing, do not block report; mark competitor module as “not available”

---

## 8) Storage (evidence)
- Store screenshots/snippets in S3/R2
- Save pointers in DB

---

## 9) Acceptance criteria
1) Start audit returns auditId immediately
2) Teaser appears or limited state within reasonable time
3) Unlock leads to report_ready + report UI/JSON
4) Confidence gating rules applied
5) Evidence pointers persisted
