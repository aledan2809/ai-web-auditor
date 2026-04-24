# Lessons Learned — AIWebAuditor

> Incident root causes and patterns specific to AIWebAuditor.
> Master-level lessons: `Master/knowledge/lessons-learned.md`.
> When a lesson derives from a Master-level pattern, cross-reference `Master L##`.

## Lessons

#### L01: GitHub push ≠ live deploy — /var/www/aiwebauditor is NOT a git repo on VPS1
- **Date**: 2026-04-24
- **Category**: Deploy / Infrastructure / Observability
- **Lesson**: Pushed recovery commit `36b6564` to GitHub (`aledan2809/AIWebAuditor` main). Expected live `techbiz.ae` + `audit.techbiz.ae` to reflect the update. Neither did — because `/var/www/aiwebauditor/` on VPS1 is a plain directory (historically populated by rsync), NOT a git clone. PM2 runs whatever code is in-place; no post-receive hook, no CI/CD. This pattern extends to every PM2 project on VPS1: PRO, eCabinet, ave-platform, guru, ma, tester, 4pro-client, 4pro-biz, 4pro-landing, 4pro-eat. For this project specifically, deploy to live requires: `rsync -avz --exclude=node_modules --exclude=.next --exclude=venv --exclude=.git /Users/danciulescu/Projects/AIWebAuditor/ root@187.77.179.159:/var/www/aiwebauditor/` + VPS1 rebuild + `pm2 restart aiwebauditor aiwebauditor-frontend`.
- **Action**: (1) **Short-term**: documented in Master DEPLOY_REGISTRY.md that AIWebAuditor VPS sync is manual rsync. Phase 2 next session will either execute the rsync, or perform one-time upgrade to git-based deploy. (2) **One-time upgrade candidate**: `ssh root@187.77.179.159 "cd /var/www/aiwebauditor && git init && git remote add origin git@github.com:aledan2809/AIWebAuditor.git && git fetch && git reset --hard origin/main"` + verify PM2 still works. Then future deploys = `git pull && npm run build && pip install && pm2 restart`. Reduces deploy surface area and eliminates "is GitHub == live?" ambiguity. (3) Cross-ref `Master L45` — this pattern is not AIWebAuditor-specific; applies to all VPS1 PM2 projects. (4) Smoke check command for post-deploy: `curl -I https://techbiz.ae && curl -I https://audit.techbiz.ae` — both should return 200, with `server: nginx` header.

#### L02: Frontend (Next.js) + Backend (FastAPI) dual-stack means TWO build steps, TWO pm2 restarts
- **Date**: 2026-04-24
- **Category**: Deploy / Multi-stack
- **Lesson**: AIWebAuditor is split into `frontend/` (Next.js on port 3001) + backend runs Python FastAPI in a venv (port 8001). PM2 manages both as separate processes (`aiwebauditor` + `aiwebauditor-frontend`). Forgetting to rebuild one side leaves a stale version serving — `npm run build` in `frontend/` is separate from `pip install -r backend/requirements.txt` and activating venv. On VPS1, both restarts are needed: `pm2 restart aiwebauditor aiwebauditor-frontend`.
- **Action**: (1) **Deploy checklist for this project** (add to top of README or dedicated `DEPLOY.md`): (a) rsync code, (b) `cd frontend && npm install && npm run build`, (c) `source backend/venv/bin/activate && pip install -r backend/requirements.txt`, (d) `pm2 restart aiwebauditor aiwebauditor-frontend`, (e) `curl -I https://techbiz.ae && curl -I https://techbiz.ae/api/health`. (2) **Ecosystem file**: create `ecosystem.config.js` that declares both processes with their exact commands and working dirs — reproducible state on VPS. (3) If AIWebAuditor has its own health endpoint (check backend routes), include in smoke test.

---

## How to Add New Lessons

1. Identify the lesson from your project work
2. Add it under an appropriate category
3. Follow the format above
4. Cross-reference Master L## if the pattern applies broadly

Claude should update this file automatically when significant lessons are learned during development.
