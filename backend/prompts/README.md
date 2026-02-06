# AI Tester Agent

> Agent AI pentru testare comprehensivă a aplicațiilor software

## Ce Este?

AI Tester Agent este un set de instrucțiuni și template-uri care transformă Claude într-un QA Engineer experimentat. Agentul poate analiza orice codebase și genera rapoarte detaliate de testare.

## Structura Proiectului

```
ai-tester-agent/
├── AGENT-TESTER-PROMPT.md   # Promptul principal - CITEȘTE ASTA PRIMUL
├── CHECKLIST-TESTING.md     # Checklist complet de testare
├── REPORT-TEMPLATE.md       # Template pentru rapoarte
├── CONFIG-EXAMPLE.md        # Exemple de configurare
└── README.md                # Acest fișier
```

## Cum Se Folosește

### Metoda 1: Quick Start

1. Deschide o conversație nouă cu Claude Code
2. Copiază conținutul din `AGENT-TESTER-PROMPT.md`
3. Spune:
   ```
   [Paste prompt aici]

   Testează C:\Projects\NumeProiect
   ```

### Metoda 2: Cu Configurare

1. Deschide `CONFIG-EXAMPLE.md`
2. Completează configurarea pentru proiectul tău
3. În Claude Code, spune:
   ```
   [Paste AGENT-TESTER-PROMPT.md]

   Configurare:
   [Paste configurarea ta]

   Începe testarea.
   ```

### Metoda 3: Focus Specific

```
[Paste prompt]

Testează security C:\Projects\NumeProiect
```

Sau:
```
Testează UI C:\Projects\NumeProiect
```

Sau:
```
Quick scan C:\Projects\NumeProiect
```

## Ce Poate Face Agentul

### ✅ Poate

- Analiza statică completă a codului sursă
- Identificare vulnerabilități de securitate din patterns
- Review UI/UX bazat pe cod și best practices
- Detectare memory leaks și performance issues din cod
- Identificare code smells și tech debt
- Generare rapoarte detaliate cu fix-uri sugerate
- Generare scripturi de test (Playwright, Cypress, Jest)

### ❌ Nu Poate

- Rula aplicația în browser real
- Face screenshots live
- Măsura performanță runtime reală
- Testa cu utilizatori reali
- Accesa baze de date sau servicii externe

## Tipuri de Testare Acoperite

| Categorie | Descriere |
|-----------|-----------|
| **Funcțional** | Business logic, fluxuri, CRUD, formulare |
| **Edge Cases** | Input-uri invalide, boundary conditions |
| **Securitate** | OWASP Top 10, auth, injection, XSS |
| **UI/UX** | Consistență, responsive, accessibility |
| **Performanță** | Memory leaks, re-renders, bundle size |
| **Code Quality** | Best practices, DRY, error handling |
| **API** | REST conventions, validation, responses |

## Format Output

Raportul include:

1. **Executive Summary** - Scor general și statistici
2. **Probleme Critical/High** - Prioritate maximă
3. **Toate Problemele** - Detaliate cu:
   - Locație exactă (fișier:linie)
   - Pași de reproducere
   - Cod problematic
   - Soluție recomandată
4. **Oportunități Îmbunătățire** - Sugestii extra
5. **Anexe** - Fișiere analizate, comenzi sugerate

## Severități

| Nivel | Când se folosește |
|-------|-------------------|
| 🔴 Critical | Blochează funcționalitate, security breach, data loss |
| 🟠 High | Feature important broken, security risk |
| 🟡 Medium | Funcționalitate afectată, există workaround |
| 🟢 Low | Minor, nu afectează funcționalitatea |
| 🔵 Info | Observație, sugestie de îmbunătățire |

## Limba

Agentul suportă orice limbă. Dacă nu specifici limba, te va întreba înainte de a începe.

Specifică limba în configurare:
```
- **Limba raport:** Română
```

Sau când pornești:
```
Testează C:\Projects\App în română
```

## Exemple Practice

### Testare Aplicație React

```
[AGENT-TESTER-PROMPT.md content]

Configurare:
- Limba: Română
- Cale: C:\Projects\my-react-app
- Tip: React + TypeScript
- Focus: Full

Începe testarea.
```

### Security Audit API

```
[AGENT-TESTER-PROMPT.md content]

Testează security C:\Projects\my-api
Limba: English
Focus pe authentication și data validation.
```

### Quick Pre-Release Check

```
[AGENT-TESTER-PROMPT.md content]

Quick scan C:\Projects\app
Doar Critical și High.
Release mâine.
```

## Tips

1. **Pentru rezultate optime**, oferă context despre ce face aplicația
2. **Specifică zonele critice** (ex: "focus pe checkout flow")
3. **Menționează known issues** pentru a le exclude din raport
4. **Oferă credențiale test** dacă ai fluxuri de autentificare

## Limitări

- Analiza este bazată pe cod, nu pe execuție reală
- Nu poate testa integrări cu servicii externe în timp real
- Performanța runtime nu poate fi măsurată (doar estimată din cod)
- Screenshots și video nu sunt posibile

## Contribuții

Feedback și sugestii sunt binevenite. Deschide un issue sau PR.

---

**Versiune:** 1.0
**Autor:** AI Tester Agent Generator
**Licență:** MIT
