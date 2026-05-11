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

_(niciun gap deschis la 2026-05-11)_

---

## Gap Log

| ID | Severity | Opened | Status | Commit |
|----|----------|--------|--------|--------|
| G-AIW-SEC-001 | P1 HIGH | 2026-04-28 | Eliminated 2026-05-11 | `8953d5f` |
| G-AIW-A11Y-001 | P2 MEDIUM | 2026-04-28 | Eliminated 2026-05-11 | `8953d5f` |
