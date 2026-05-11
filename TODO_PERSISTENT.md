# TODO Persistent — AIWebAuditor

> **IMPORTANT:** Read at start of EVERY session on this project.
> Items stay here until marked DONE with date + commit hash.
> Surface OPEN items at session start (per Master CLAUDE.md regula 2b).

**Project safety**: ACTIVE | **Production**: techbiz.ae + audit.techbiz.ae (VPS1, port 3001/8001)
**Score history**: 91/100 (2026-04-28 AUDIT_E2E_2026-04-28.md — 7/14 plugins active, PASSED)

---

## [x] G-AIW-SEC-001 — [P1] [security] Missing CSP header + /admin unauthenticated (creat 2026-05-11, DONE 2026-05-11, commit 8953d5f)

**Source**: `Reports/AUDIT_E2E_2026-04-28.md` security-scanner 80/100, 2 HIGH findings.

**Issues**:
1. Missing `Content-Security-Policy` header on all responses
2. `/admin` route accessible without authentication (HTTP 200)

**Fix plan**:
- **ÎNAINTE de orice fix**: `curl -I https://techbiz.ae/admin` — confirmă dacă returnează 200 cu conținut real sau redirect JS-side. Dacă e false-positive, marchează explicit în TODO și scade severitatea.
- Add CSP header in Next.js `next.config.js` headers() or middleware.ts
- Verify /admin route — if it's intentionally public (landing/demo), mark as false-positive; otherwise add auth middleware

**Estimated effort**: 30-60min (inclusiv investigare /admin).

---

## [x] G-AIW-A11Y-001 — [P2] [a11y+mobile] Touch targets + skip nav (creat 2026-05-11, DONE 2026-05-11, commit 8953d5f)

**Source**: `Reports/AUDIT_E2E_2026-04-28.md` mobile-tester 75/100 + a11y-scanner 98/100.

**Issues**:
1. iPhone 13: 3/6 touch targets below 44×44px on `/` (mobile-tester MEDIUM)
2. No skip navigation link (a11y-scanner LOW)

**Fix plan**:
- Apply `min-h-[44px] min-w-[44px] inline-flex items-center justify-center` pattern (same as MA ecosystem fix)
- Add `<a class="skip-link" href="#main-content">Skip to content</a>` in root layout

**Estimated effort**: 30-60min.

---

## Session log

| Date | Change | Commit |
|------|--------|--------|
| 2026-04-28 | [7] E2E audit: 91/100 PASS, security-scanner 80 + mobile-tester 75 flagged | — |
| 2026-05-11 | TODO_PERSISTENT.md created with G-AIW-SEC-001 + G-AIW-A11Y-001 | — |
| 2026-05-11 | G-AIW-SEC-001 + G-AIW-A11Y-001 fixed: middleware.ts (server-side JWT auth on /admin), CSP headers (next.config.js), touch targets (nav), skip-nav (layout) | 8953d5f |

---

*Last updated: 2026-05-11. Toate gap-urile închise. Next: deploy VPS1 + re-audit [7].*
