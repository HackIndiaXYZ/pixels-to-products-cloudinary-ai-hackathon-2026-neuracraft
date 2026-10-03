# CreativePulse AI — Implementation Plan

**Based on:** IMPLEMENTATION_AUDIT.md  
**Date:** 2026-10-02  
**Goal:** End-to-end working hackathon-ready product — no bypasses, no fake data, no simulated responses

---

## EXECUTION STRATEGY

Work in small, verifiable increments:
1. Fix backend correctness bugs first (safe, no UI impact)
2. Fix API contract (types + api.ts)
3. Fix authentication (login → DashboardLayout → protected routes)
4. Fix individual pages (API calls + dark theme)
5. Run verification

---

## PHASE 1 — BACKEND CORRECTNESS FIXES

### 1.1 Fix validation_service.py — duplicate removal
**File:** `backend/app/services/validation_service.py`  
**Problem:** `_check_duplicates` detects but does not remove duplicates from the DataFrame  
**Fix:** After detecting duplicates, call `df.drop_duplicates(subset=duplicate_cols, keep='first', inplace=True)` and update the returned DataFrame

### 1.2 Fix feature_service.py — deterministic hashing
**File:** `backend/app/services/feature_service.py`  
**Problem:** `id_hash = hash(creative_id)` — Python's `hash()` varies across process runs  
**Fix:** Replace with `hashlib.sha256(creative_id.encode()).hexdigest()` and derive int from hex

### 1.3 Fix deps.py — remove debug token logging
**File:** `backend/app/core/deps.py`  
**Problem:** `print()` statements log JWT token content and user data  
**Fix:** Replace all `print(f"DEBUG: ...")` with `logger.debug(...)` calls — these won't appear in production logs unless DEBUG level is enabled

### 1.4 Fix execution endpoint — allow performance-only analysis
**File:** `backend/app/api/endpoints/execution.py`  
**Problem:** Requires `len(analysis.assets) > 0` — blocks analysis if no Cloudinary assets uploaded  
**Fix:** Remove the asset count check. Pipeline already handles this gracefully — demo assets get generated from performance data IDs when no real assets exist. Update pipeline to auto-register demo assets if none exist.

### 1.5 Fix pipeline — auto-register demo assets when none exist
**File:** `backend/app/services/pipeline.py`  
**Problem:** If no assets, feature extraction returns 0 and pipeline fails  
**Fix:** Add a stage before feature extraction: if `len(analysis.assets) == 0`, auto-register `local_demo` assets for each unique `creative_id` found in `performance_records`

### 1.6 Fix pipeline — enrich stage names
**File:** `backend/app/services/pipeline.py`  
**Problem:** Only 3 stages; plan calls for 8 meaningful stages  
**Fix:** Update stage messages to: "Loading data", "Validating data", "Computing metrics", "Extracting visual features", "Running statistical analysis", "Building Creative DNA", "Persisting results", "Finalizing"

### 1.7 Fix CORS config
**File:** `backend/app/main.py`  
**Problem:** `allow_origins=["*"]`  
**Fix:** Read `FRONTEND_URL` from settings. Default to `http://localhost:3000` for dev. Keep `["*"]` as fallback only for environments where FRONTEND_URL is not set.

### 1.8 Add FRONTEND_URL to config
**File:** `backend/app/core/config.py`  
**Fix:** Add `FRONTEND_URL: str = "http://localhost:3000"` to Settings

---

## PHASE 2 — API CONTRACT (TYPES + API CLIENT)

### 2.1 Fix types/index.ts
**File:** `frontend/types/index.ts`  
**Fixes:**
- Add `DNAInsight` as alias or rename: export `DNAInsight = CreativeDNAInsight`
- Ensure `Analysis.id` is `number` ✓ (already correct)
- Add `AssetWithFeatures` type for library page
- Add `PerformanceCreative` type for performance page
- Fix `Asset` type — add optional `metrics?: PerformanceMetrics`

### 2.2 Fix api.ts — remove non-existent methods, add missing ones
**File:** `frontend/lib/api.ts`  
**Remove:**
- `executeAnalysis()` — does not exist on backend
**Add / fix:**
- `getAnalysisOverview(analysisId)` ✓ already exists
- `getAnalysisAssets(analysisId)` ✓ already exists
- `getAnalysisPerformance(analysisId)` ✓ already exists
- `getCreativeDNA(analysisId)` ✓ already exists
- Ensure `repurposeAsset(analysisId, { source_asset_id, format })` signature matches backend
- Remove console.log statements that could expose tokens

---

## PHASE 3 — AUTHENTICATION REPAIR

### 3.1 Fix login/page.tsx
**File:** `frontend/app/(auth)/login/page.tsx`  
**Remove:** `setTimeout(() => router.push('/dashboard'), 500)` bypass and "Skip to Dashboard" button  
**Replace:** Real `api.login(email, password)` call → on success store token → `router.push('/dashboard')`  
**Add:** Proper error handling with user-friendly messages

### 3.2 Fix DashboardLayout.tsx
**File:** `frontend/components/DashboardLayout.tsx`  
**Remove:** `setUser({ email: 'demo@example.com', id: 1 })` bypass  
**Replace:** `api.getCurrentUser()` → on 401 redirect to `/login`  
**Add:** Loading state while fetching user; redirect on auth failure

### 3.3 Fix landing page CTA
**File:** `frontend/app/page.tsx`  
**Problem:** "Start Analyzing" always links to `/dashboard`  
**Fix:** Check for token on click. If token exists → `/dashboard`. If not → `/login`. Use `useEffect` to check auth state for auto-redirect if already logged in.

---

## PHASE 4 — DASHBOARD REPAIR

### 4.1 Fix dashboard/page.tsx
**File:** `frontend/app/(dashboard)/dashboard/page.tsx`  
**Remove:** `demoKPIs`, `demoInsight`, all hardcoded values, commented-out backend calls  
**Replace:**
- Fetch `api.getAnalyses()` → get list
- If no completed analyses → show empty state with "Create Analysis" CTA
- If analyses exist → pick most recent completed → fetch `api.getAnalysisOverview(id)`
- Display real: spend, revenue, ROAS, CTR, CVR, CPM, creative count, record count
- Display real top Creative DNA insights from `api.getInsights(id)` (limit 3)
- Show analysis selector to switch between completed analyses

---

## PHASE 5 — NEW ANALYSIS WIZARD REPAIR

### 5.1 Fix new/page.tsx
**File:** `frontend/app/(dashboard)/new/page.tsx`  
**Fixes:**
- Fix `api.createAnalysis(name, description)` → `api.createAnalysis({ name, description })`
- Remove non-existent `api.executeAnalysis()` → replace with `api.runAnalysis(id)`
- Add actual run + poll flow: `runAnalysis()` → poll `getAnalysisStatus()` every 2s until completed/failed
- Fix step 3 (assets): Show Cloudinary status. If not configured, show clear message and offer "Demo mode" (local_demo assets). If configured, show upload UI.
- Fix step ordering to match actual API: 1=Create, 2=Upload Performance, 3=Upload Assets (or skip), 4=Review, 5=Run + Poll
- Show validation summary from performance upload response
- Show matched/unmatched creative IDs
- Apply full dark design system styling

---

## PHASE 6 — PERFORMANCE PAGE REPAIR

### 6.1 Fix performance/page.tsx
**File:** `frontend/app/(dashboard)/performance/page.tsx`  
**Remove:** `api.getAnalysisMetrics()` calls  
**Replace:** Use `api.getAnalysisOverview(id)` for aggregate metrics + `api.getAnalysisPerformance(id)` for per-creative table  
**Add:** Platform breakdown from `api.getAnalysisPlatforms(id)` (need to add to api.ts)  
**Style:** Apply dark design system

---

## PHASE 7 — CREATIVE LIBRARY PAGE REPAIR

### 7.1 Fix library/page.tsx
**File:** `frontend/app/(dashboard)/library/page.tsx`  
**Remove:** `api.getAnalysisMetrics()` calls  
**Replace:** `api.getAnalysisAssets(analysisId)` — returns assets with metrics embedded  
**Fix:** Asset filtering/search  
**Style:** Apply dark design system

---

## PHASE 8 — CREATIVE DNA PAGE REPAIR

### 8.1 Fix dna/page.tsx
**File:** `frontend/app/(dashboard)/dna/page.tsx`  
**Remove:** `api.getDNAInsights()` calls  
**Replace:** `api.getCreativeDNA(analysisId)` (correct method from api.ts)  
**Fix:** Import `CreativeDNAInsight` from types (not `DNAInsight`)  
**Fix:** Field names: `insight.positive_median` not `insight.with_feature_median`  
**Fix:** Guard `p_value` and `effect_size` for null  
**Fix:** Direction from `positive_median > negative_median` comparison  
**Style:** Apply dark design system

---

## PHASE 9 — REPURPOSE PAGE REPAIR

### 9.1 Fix repurpose/page.tsx
**File:** `frontend/app/(dashboard)/repurpose/page.tsx`  
**Remove:** `api.getAnalysisMetrics()` calls  
**Replace:** `api.getAnalysisAssets(analysisId)` for asset listing  
**Fix:** `api.repurposeAsset(selectedAsset, format)` → `api.repurposeAsset(analysisId, { source_asset_id: selectedAsset, format })`  
**Add:** Cloudinary status check — if not configured, show clear "Cloudinary not configured" message  
**Style:** Apply dark design system

---

## PHASE 10 — REPORTS PAGE REPAIR

### 10.1 Fix reports/page.tsx
**File:** `frontend/app/(dashboard)/reports/page.tsx`  
**Remove:** `setTimeout` + `alert()` simulation; fake "Recent Reports" placeholder entries  
**Replace:** Real printable report page  
- Fetch analysis overview, DNA insights, performance data, platform breakdown
- Render a structured report in-page with: analysis name, date, creative count, aggregate metrics, top DNA insights with evidence, methodology note, association disclaimer
- Provide "Print / Save as PDF" via `window.print()` (browser native)
- No fake download button claiming a PDF exists when it doesn't  
**Style:** Apply dark design system

---

## PHASE 11 — AI ASSISTANT REPAIR

### 11.1 Fix assistant/page.tsx
**File:** `frontend/app/(dashboard)/assistant/page.tsx`  
**Remove:** `setTimeout` fake AI response  
**Replace:**  
- Check if AI provider is configured (add `/api/health/ai` endpoint or check via flag)
- If not configured: show clear "AI Assistant not connected" state with grounded navigation options ("Explore Creative DNA", "View Performance", "Browse Creative Library")
- If configured (future): route through backend with analysis context  
**Add:** Grounded context links — clicking a suggested question navigates to the relevant page  
**Style:** Apply dark design system

---

## PHASE 12 — SETTINGS PAGE REPAIR

### 12.1 Fix settings/page.tsx
**File:** `frontend/app/(dashboard)/settings/page.tsx`  
**Remove:** `setTimeout` fake save  
**Fix:** Notification preferences: label clearly as "not yet persisted" or remove the save button from that section  
**Keep:** Account info display (reads real user from API) ✓  
**Add:** Backend connection status, Cloudinary status, app version  
**Style:** Apply dark design system

---

## PHASE 13 — BACKEND DEMO DATA

### 13.1 Add demo seed endpoint
**File:** `backend/app/api/endpoints/analyses.py` (or new file)  
**Endpoint:** `POST /api/analyses/{id}/seed-demo`  
**Function:** Populate an analysis with demo performance data (40 creatives, ~400 records) from `sample_data.py` and register `local_demo` assets  
**Use:** New analysis wizard can offer "Load Demo Data" button

---

## PHASE 14 — BACKEND API ADDITIONS

### 14.1 Add platforms endpoint to api.ts
**File:** `frontend/lib/api.ts`  
**Add:** `getAnalysisPlatforms(analysisId)` calling `GET /api/analyses/{id}/platforms`

### 14.2 Add Cloudinary status to api.ts
**File:** `frontend/lib/api.ts`  
**Add:** `getCloudinaryStatus()` calling `GET /api/cloudinary/status` ✓ (already exists, just needs adding)

---

## PHASE 15 — COMPLETE DARK DESIGN SYSTEM APPLICATION

All 8 white/gray pages need the following changes:  
- Replace `bg-white` → `bg-surface` or `Card` component  
- Replace `border-gray-300` → `border-border`  
- Replace `text-gray-900` → `text-text-primary`  
- Replace `text-gray-600` → `text-text-secondary`  
- Replace `bg-blue-600` → `bg-primary-600`  
- Replace `hover:bg-gray-50` → `hover:bg-surface-secondary`  
- Replace `focus:ring-blue-500` → `focus:ring-primary-500`  
- Use `Card`, `Button`, `Input`, `SectionHeader`, `EmptyState`, `StatusBadge` components  
- Use `Skeleton` for loading states  

Pages: `new`, `library`, `dna`, `performance`, `repurpose`, `reports`, `assistant`, `settings`

---

## PHASE 16 — VERIFICATION

### 16.1 Backend tests
```bash
cd backend
pytest tests/ -v
```

### 16.2 Frontend lint + build
```bash
cd frontend
npm run lint
npm run build
```

### 16.3 Manual golden path verification
1. Open `http://localhost:3000`
2. Click "Start Analyzing" → redirects to `/login` (not authenticated)
3. Click "Create one now" → `/signup`
4. Create account → auto-login → `/dashboard` (empty state)
5. Click "New Analysis" → fill name → create → analysis ID returned
6. Upload performance CSV → see validation summary
7. Skip or upload Cloudinary assets
8. Review → click "Run Analysis"
9. Watch status polling
10. On completion → redirect to dashboard with real metrics
11. Verify Creative Library shows real assets
12. Verify DNA page shows real insights with evidence tiers
13. Verify Performance page shows real metrics
14. Verify Repurpose shows Cloudinary status
15. Verify Reports renders real data and print works
16. Verify AI Assistant shows "not connected" state
17. Verify Settings shows real user and connection status
18. Logout → redirected to login

---

## PHASE 17 — ENVIRONMENT DOCUMENTATION

### Required environment variables

**Backend (`backend/.env`):**
```
DATABASE_URL=postgresql://user:password@localhost:5432/creativepulse
JWT_SECRET=<minimum 32 character random string>
FRONTEND_URL=http://localhost:3000
CLOUDINARY_CLOUD_NAME=<optional>
CLOUDINARY_API_KEY=<optional>
CLOUDINARY_API_SECRET=<optional>
```

**Frontend (`frontend/.env.local`):**
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## RISK LOG

| Risk | Mitigation |
|---|---|
| PostgreSQL not available in demo env | SQLite works for hackathon demo — document limitation |
| Cloudinary not configured | App handles gracefully with clear UI messages |
| LLM not configured | Show "not connected" state — never fake AI |
| Migration `now()` syntax fails on SQLite | App uses `create_all()` fallback — document that Alembic is for PostgreSQL |

---

## FINAL SUCCESS CONDITION

The application is complete when:
1. A new user can sign up, log in, and see a real empty dashboard
2. A new analysis can be created and performance data uploaded
3. Analysis can be run and status polled in real time
4. Dashboard shows real computed metrics from the completed analysis
5. Creative Library, DNA, Performance pages show real data
6. Repurpose shows Cloudinary status honestly
7. AI Assistant shows "not connected" honestly
8. Reports renders real data and print works
9. Settings shows real user data
10. Logout clears auth and redirects to login
