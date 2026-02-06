# CONFIGURARE AI TESTER AGENT

> Copiază și adaptează această configurare când pornești o sesiune de testare.

---

## CONFIGURARE RAPIDĂ (QUICK START)

```markdown
# CONFIGURARE TESTARE

## Setări de Bază
- **Limba raport:** Română
- **Cale proiect:** C:\Projects\NumeProiect
- **Tip aplicație:** Web App (React)
- **Focus:** Full (toate categoriile)

## URL-uri de Test (opțional)
- **Local:** http://localhost:3000
- **Staging:** https://staging.example.com

## Note Speciale
- [Adaugă orice context important pentru tester]
```

---

## CONFIGURARE COMPLETĂ

```markdown
# CONFIGURARE TESTARE DETALIATĂ

## 1. SETĂRI GENERALE

### Limba
- **Limba raport:** [Română | English | Altă limbă]
- **Limba cod/comentarii:** [Română | English]

### Proiect
- **Nume proiect:** [Numele aplicației]
- **Cale proiect:** [C:\path\to\project]
- **Repository:** [URL git dacă relevant]
- **Branch:** [main/develop/feature-x]

### Tip Aplicație
- [ ] Web App - Frontend Only
- [ ] Web App - Full Stack
- [ ] API Only (REST/GraphQL)
- [ ] Mobile App (React Native/Flutter)
- [ ] Desktop App (Electron)
- [ ] Library/Package

### Stack Tehnologic (dacă cunoscut)
- **Frontend:** [React, Vue, Angular, Svelte, etc.]
- **Backend:** [Node.js, Python, Java, Go, etc.]
- **Database:** [PostgreSQL, MySQL, MongoDB, etc.]
- **ORM:** [Prisma, TypeORM, Sequelize, etc.]
- **State Management:** [Redux, Zustand, MobX, etc.]
- **Styling:** [Tailwind, Styled Components, CSS Modules, etc.]

---

## 2. SCOPE TESTARE

### Categorii de Testat
- [x] Funcțional - Business Logic
- [x] Funcțional - Edge Cases
- [x] Securitate - OWASP Top 10
- [x] Securitate - Authentication/Authorization
- [x] UI/UX - Visual Consistency
- [x] UI/UX - Responsive Design
- [x] UI/UX - Accessibility (WCAG)
- [x] Performanță - Code Analysis
- [x] Performanță - Bundle Size
- [x] Code Quality - Best Practices
- [x] Code Quality - Type Safety
- [x] API Testing (dacă aplicabil)
- [x] Oportunități de Îmbunătățire

### Excluderi (Nu Testa)
- [ ] [Folder/feature de exclus]
- [ ] [Exemplu: node_modules, dist, .git]
- [ ] [Exemplu: __tests__ - dacă nu vrei review pe teste]

### Focus Special
- [ ] [Zonă critică care necesită atenție specială]
- [ ] [Exemplu: Fluxul de plăți]
- [ ] [Exemplu: Sistemul de autentificare]

---

## 3. CONTEXT BUSINESS

### Descriere Aplicație
[2-3 propoziții despre ce face aplicația]

### Utilizatori Țintă
- [Tip utilizator 1 - ex: Admin]
- [Tip utilizator 2 - ex: Customer]
- [Tip utilizator 3 - ex: Guest]

### Fluxuri Principale
1. [Flux 1 - ex: Înregistrare și Login]
2. [Flux 2 - ex: Browse produse și adăugare în coș]
3. [Flux 3 - ex: Checkout și plată]
4. [Flux 4 - ex: Managementul contului]

### Funcționalități Critice
- [ ] [Feature critic 1 - unde un bug = blocaj major]
- [ ] [Feature critic 2]

---

## 4. ENVIRONMENT

### URL-uri de Test
- **Development:** [http://localhost:3000]
- **Staging:** [https://staging.app.com]
- **Production:** [https://app.com] (doar read/observare)

### Credențiale Test (dacă necesare)
- **Admin:** [user/pass sau "în .env"]
- **User normal:** [user/pass sau "în .env"]

### Environment Variables Necesare
```env
# Exemplu - NU pune valori reale aici
DATABASE_URL=
API_KEY=
JWT_SECRET=
```

---

## 5. DOCUMENTAȚIE EXISTENTĂ

### Fișiere de Referință
- [ ] README.md
- [ ] docs/ folder
- [ ] Swagger/OpenAPI spec
- [ ] Figma/Design files
- [ ] User stories/Requirements

### Locații Importante
- **Entry point:** [src/index.tsx sau similar]
- **Routes:** [src/routes/ sau src/pages/]
- **API endpoints:** [src/api/ sau server/routes/]
- **Components:** [src/components/]
- **Services:** [src/services/]
- **Types:** [src/types/]

---

## 6. OUTPUT PREFERENCES

### Format Raport
- [ ] Markdown complet (recomandat)
- [ ] Summary only (doar probleme Critical/High)
- [ ] JSON (pentru procesare automată)

### Nivel de Detaliu
- [ ] Maxim - toate problemele, inclusiv Info
- [ ] Standard - Critical, High, Medium, Low
- [ ] Minimal - doar Critical și High

### Salvare Raport
- **Locație:** [C:\Projects\NumeProiect\test-reports\]
- **Naming:** [YYYY-MM-DD-test-report.md]

### Generare Teste Automate
- [ ] Da - generează scripturi Playwright
- [ ] Da - generează scripturi Cypress
- [ ] Da - generează teste Jest
- [ ] Nu - doar raport

---

## 7. NOTE SPECIALE

### Known Issues (de ignorat)
- [Issue cunoscut care nu trebuie raportat]
- [Exemplu: Bug X e deja în backlog]

### Dependențe Externe
- [Serviciu extern 1 - ex: Stripe pentru plăți]
- [Serviciu extern 2 - ex: SendGrid pentru email]

### Constrângeri
- [Constrângere 1 - ex: trebuie să suporte IE11]
- [Constrângere 2 - ex: max bundle size 500KB]

### Alte Observații
[Orice altceva relevant pentru tester]
```

---

## EXEMPLE DE CONFIGURARE RAPIDĂ

### Exemplu 1: Testare Completă React App

```markdown
# CONFIG: Full Test - React Dashboard

- **Limba:** Română
- **Cale:** C:\Projects\admin-dashboard
- **Tip:** Web App Full Stack (React + Node.js)
- **Focus:** Full scan
- **Note:** Focus special pe role-based access control
```

### Exemplu 2: Security Audit Only

```markdown
# CONFIG: Security Audit - E-commerce API

- **Limba:** English
- **Cale:** C:\Projects\shop-api
- **Tip:** REST API (Node.js + Express)
- **Focus:** Security only
- **Note:** Prioritate pe payment endpoints și user data
```

### Exemplu 3: Quick Scan Pre-Release

```markdown
# CONFIG: Quick Scan - Mobile App

- **Limba:** Română
- **Cale:** C:\Projects\mobile-app
- **Tip:** React Native
- **Focus:** Critical și High only
- **Note:** Release în 2 zile, doar blocker-uri
```

### Exemplu 4: UI/UX Review

```markdown
# CONFIG: UI/UX Review - Landing Page

- **Limba:** English
- **Cale:** C:\Projects\landing-page
- **Tip:** Static site (Next.js)
- **Focus:** UI/UX + Accessibility
- **Note:** Trebuie WCAG 2.1 AA compliance
```

---

## COMENZI DE PORNIRE

După ce ai setat configurarea, pornește testarea cu una din comenzile:

```
Testează C:\Projects\NumeProiect

Testează security C:\Projects\NumeProiect

Testează UI C:\Projects\NumeProiect

Quick scan C:\Projects\NumeProiect
```

Sau pentru control maxim:

```
Folosește configurarea de mai sus și începe testarea proiectului [CALE].
Focus pe [CATEGORIE]. Raportul să fie în [LIMBA].
```
