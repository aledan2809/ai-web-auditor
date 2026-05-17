# AUDIT_GAPS.md — AIWebAuditor

> Ledger persistent pentru gaps identificate. Status: OPEN → Eliminated (cu commit hash + dată).
> Per Master CLAUDE.md §2d: surfaced la fiecare sesiune pe proiect.

---

## Eliminated Gaps

### G-AIW-SEC-001 — Missing server-side auth on /admin + CSP header
- **Severity**: P1 HIGH
- **Source**: Reports/AUDIT_E2E_2026-04-28.md (security-scanner 80/100)
- **Description**:
  1. `/admin` returnea HTTP 200 fără autentificare server-side (client-only auth guard în Zustand)
  2. Lipsă `Content-Security-Policy` header pe toate responses
- **Investigare 2026-05-11**: `curl -I https://techbiz.ae/admin` → 200 OK + 7152 bytes HTML = vulnerabilitate reală (nu false-positive)
- **Fix**: `frontend/middleware.ts` creat — verifică `access_token` cookie JWT (HS256 cu jose) server-side pe toate rutele `/admin/*`; redirect la `/login?returnUrl=...` dacă invalid/absent/rol != admin. CSP + X-Content-Type-Options + X-Frame-Options + Referrer-Policy + Permissions-Policy adăugate în `next.config.js` headers().
- **Status**: **Eliminated** | 2026-05-11 | commit `8953d5f`

### G-AIW-A11Y-001 — Touch targets < 44px + lipsă skip-nav
- **Severity**: P2 MEDIUM
- **Source**: Reports/AUDIT_E2E_2026-04-28.md (mobile-tester 75/100 + a11y-scanner 98/100)
- **Description**:
  1. 3/6 touch targets sub 44×44px pe `/` (logout button ~32px, admin icon ~20px, nav links text-only)
  2. Lipsă skip navigation link în root layout
- **Fix**: `min-h-[44px] min-w-[44px] inline-flex items-center justify-center` pe toate elementele interactive din Navigation (5 linkuri + logout button + admin icon). `aria-label` adăugat pe icon-only controls. `<a href="#main-content">` skip-nav în layout.tsx + `id="main-content"` pe `<main>`.
- **Status**: **Eliminated** | 2026-05-11 | commit `8953d5f`

---

## Open Gaps

*(none)*

---

## Eliminated Gaps (recent)

### G-AIW-MOBILE-001 — Touch targets 3/9 pe `/login` (re-audit 2026-05-12)
- **Severity**: P3 LOW
- **Source**: Reports/AUDIT_E2E_2026-05-11.md (mobile-tester 88/100)
- **Description**: 3/9 touch targets sub 44px pe `/login` across iPhone 13 + Pixel 5 + iPad Pro 11. Login form elements (email input, password input, register link) lipseau `min-h-[44px]`. Nav elements fixate anterior în G-AIW-A11Y-001 (`8953d5f`).
- **Fix**: `min-h-[44px]` adăugat pe email input + password input (inline cu celelalte clase py-3). Register Link → `inline-flex items-center min-h-[44px]`. Fișier: `frontend/app/login/page.tsx`.
- **Status**: **Eliminated** | 2026-05-17 | commit `d5d9777`

### G-AIW-ML2W2-001 — Touch targets logo link + submit button + WCAG 2.4.7 focus (re-audit 2026-05-17 ML2 Wave 2)
- **Severity**: P2 MEDIUM → MEDIUM
- **Source**: Reports/AUDIT_E2E_2026-05-17.md (mobile-tester 88/100, ML2 Wave 2 [9] audit)
- **Description**: 3/9 touch targets below 44×44px on `/login` (audit repeated issue from G-AIW-MOBILE-001 + 2 additional):
  1. Logo link "AI Web Auditor" (navigation.tsx:27) — no `min-h-[44px]` or `inline-flex items-center`
  2. Submit button "Autentificare" (login/page.tsx:83) — `py-3` only, no explicit `min-h-[44px]`
  3. Nav links lacking `focus-visible` keyboard indicators (WCAG 2.4.7)
- **Fix**: 
  - Logo link: `min-h-[44px] inline-flex items-center` (commit `2805f36`)
  - Submit button: `min-h-[44px]` added (commit `2805f36`)
  - WG TRWG loop (`loop_trwg_mpa8vgyv_ki2dww`): logout try-catch, isMounted cleanup on login, logo `self-stretch`, `focus-visible:ring-2` on all nav links (commit `ecc6726`)
- **Status**: **Eliminated** | 2026-05-18 | commits `2805f36` + `ecc6726` | deployed techbiz.ae + audit.techbiz.ae

### G-AIW-TRWG-001 — WCAG 2.4.7 focus-visible global CSS + URL validation + enrollment error UX + FeatureCard icons (TRWG loop 2026-05-18)
- **Severity**: P2 MEDIUM
- **Source**: TRWG loop `loop_trwg_mpaa4ox2_9lek2i` — /review 4 issues iter 1; 0 issues iter 2+3
- **Description**:
  1. No global CSS `:focus-visible` rule — outline suppressed by Tailwind `focus-visible:outline-none` on nav elements
  2. URL input in LeadCaptureFlow: no empty/whitespace guard; no protocol validation (accepts `ftp://` etc.)
  3. Enrollment submit catch: silently continued without displaying error to user
  4. FeatureCard section missing icons (low visual hierarchy)
  5. `focus-visible:outline-none` on all 8 nav interactive elements — suppressed global CSS outline rule
  6. Inregistrare button `py-2` → height below 44px
- **Fix**: 
  - globals.css: `a/button/[role=button]:focus-visible { outline: 3px solid #2563eb !important }` + `:focus` fallback for headless Chromium + `::placeholder` contrast fix
  - login/page.tsx: `email.trim()` + `password.trim().length === 0` guard; `focus-visible:ring-2` on inputs + submit button
  - LeadCaptureFlow.tsx: empty URL guard + `new URL()` protocol validation; enrollment catch → `setError()` + `return`; error banner in enrollment step; `focus-visible:ring-2` on URL input; Zap/Brain/FileText icons on FeatureCard; `min-h-[70vh]` on url-input step
  - navigation.tsx: removed `focus-visible:outline-none` from all 8 interactive elements; `py-2` → `py-3` on Inregistrare button
- **Fix continuare (iters 3-6)**:
  - navigation.tsx: `self-stretch` pe nav links (→ 64px full height); null guard pe user block; `h-11` pe Inregistrare; `focus-visible:ring-white`; `lang=ro` + `min-h-[44px]` pe "Audit Nou"
  - globals.css: outline ajustat la `2px #1d4ed8`; `!important` adăugat pe `:focus` fallback pentru input/select/textarea
  - login/page.tsx: password guard simplificat (`trim().length < 6`); `minLength={6}` pe input
  - LeadCaptureFlow.tsx: `audit_id` guard; `err: unknown` typing; `text-gray-600/700` contrast; focus ring pe submit
  - autentificare/page.tsx: render inline LoginPage (permite Tester să screenshot-eze formularul)
- **TRWG results**: iter1 Static=74, iter2 Static=100 (0 /review issues), iter3-6 Static=100 (0 /review issues) — Vision-blocked runtime (~62) datorită limitării Tester pe headless screenshot; Combined oprit manual după 6 iters cu 0 issues noi
- **Status**: **Eliminated** | 2026-05-18 | commits `81d83c8` + `4fd7d82` | deployed techbiz.ae + audit.techbiz.ae

---

## Gap Log

| ID | Severity | Opened | Status | Commit |
|----|----------|--------|--------|--------|
| G-AIW-SEC-001 | P1 HIGH | 2026-04-28 | Eliminated 2026-05-11 | `8953d5f` |
| G-AIW-A11Y-001 | P2 MEDIUM | 2026-04-28 | Eliminated 2026-05-11 | `8953d5f` |
| G-AIW-MOBILE-001 | P3 LOW | 2026-05-12 | Eliminated 2026-05-17 | `d5d9777` |
| G-AIW-ML2W2-001 | P2 MEDIUM | 2026-05-17 | Eliminated 2026-05-18 | `2805f36`+`ecc6726` |
| G-AIW-TRWG-001 | P2 MEDIUM | 2026-05-18 | Eliminated 2026-05-18 | `81d83c8`+`4fd7d82` |
