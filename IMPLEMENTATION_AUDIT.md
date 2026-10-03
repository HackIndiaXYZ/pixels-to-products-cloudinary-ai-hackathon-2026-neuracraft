# CreativePulse AI — Implementation Audit

**Date:** 2026-10-02  
**Auditor:** Kiro (Senior Full-Stack Engineer)  
**Source of Truth:** Actual repository code inspection  
**Status:** Pre-fix baseline

---

## 1. EXISTING FRONTEND ROUTES

| Route | File | Status |
|---|---|---|
| `/` | `app/page.tsx` | Exists — landing page with broken CTA (sends unauthenticated users to `/dashboard` directly) |
| `/login` | `app/(auth)/login/page.tsx` | Exists — **AUTH BYPASS: `setTimeout → router.push('/dashboard')`, never calls backend** |
| `/signup` | `app/(auth)/signup/page.tsx` | Exists — calls real `api.signup()` ✓ |
| `/dashboard` | `app/(dashboard)/dashboard/page.tsx` | Exists — **BYPASS: does not call backend, shows hardcoded KPIs and hardcoded DNA insight** |
| `/new` | `app/(dashboard)/new/page.tsx` | Exists — **Uses `api.executeAnalysis()` which does not exist in api.ts; styled in old white/gray** |
| `/library` | `app/(dashboard)/library/page.tsx` | Exists — **Calls `api.getAnalysisMetrics()` which does not exist in api.ts; old white/gray styling** |
| `/dna` | `app/(dashboard)/dna/page.tsx` | Exists — **Calls `api.getDNAInsights()` which does not exist in api.ts; old white/gray styling; uses `DNAInsight` type not defined in types/index.ts** |
| `/performance` | `app/(dashboard)/performance/page.tsx` | Exists — **Calls `api.getAnalysisMetrics()` which does not exist in api.ts; old white/gray styling** |
| `/repurpose` | `app/(dashboard)/repurpose/page.tsx` | Exists — **Calls `api.getAnalysisMetrics()` which does not exist; calls `api.repurposeAsset(selectedAsset, format)` with wrong signature; old white/gray styling** |
| `/reports` | `app/(dashboard)/reports/page.tsx` | Exists — **Report generation simulated with `setTimeout` + `alert()`; old white/gray styling** |
| `/assistant` | `app/(dashboard)/assistant/page.tsx` | Exists — **AI response simulated with `setTimeout`; pretends to be real AI; old white/gray styling** |
| `/settings` | `app/(dashboard)/settings/page.tsx` | Exists — calls real `api.getCurrentUser()` ✓; **settings save simulated with `setTimeout`; old white/gray styling** |

---

## 2. EXISTING BACKEND ROUTES

| Method | Path | Auth | Status |
|---|---|---|---|
| POST | `/api/auth/signup` | No | ✓ Working |
| POST | `/api/auth/login` | No | ✓ Working |
| GET | `/api/auth/me` | Bearer | ✓ Working |
| POST | `/api/analyses` | Bearer | ✓ Working |
| GET | `/api/analyses` | Bearer | ✓ Working |
| GET | `/api/analyses/{id}` | Bearer | ✓ Working |
| DELETE | `/api/analyses/{id}` | Bearer | ✓ Working |
| GET | `/api/analyses/{id}/status` | Bearer | ✓ Working |
| POST | `/api/analyses/{id}/run` | Bearer | **PROBLEM: requires `len(analysis.assets) > 0`, but new analysis wizard has no real asset upload** |
| POST | `/api/analyses/{id}/performance/upload` | Bearer | ✓ Working — BUT duplicate detection reports but does NOT remove duplicates before persistence |
| POST | `/api/analyses/{id}/assets/register` | Bearer | ✓ Working |
| GET | `/api/analyses/{id}/assets/list` | Bearer | ✓ Working |
| DELETE | `/api/analyses/{id}/assets/{asset_id}` | Bearer | ✓ Working |
| GET | `/api/analyses/{id}/overview` | Bearer | ✓ Working |
| GET | `/api/analyses/{id}/performance` | Bearer | ✓ Working |
| GET | `/api/analyses/{id}/assets` | Bearer | ✓ Working |
| GET | `/api/analyses/{id}/platforms` | Bearer | ✓ Working |
| GET | `/api/analyses/{id}/creative-dna` | Bearer | ✓ Working |
| GET | `/api/analyses/{id}/insights` | Bearer | ✓ Working |
| GET | `/api/analyses/{id}/features` | **MISSING** | ❌ Route referenced in plan but not in router.py or any endpoint file |
| GET | `/api/analyses/{id}/features/{creative_id}` | **MISSING** | ❌ Not implemented |
| POST | `/api/analyses/{id}/repurpose` | Bearer | ✓ Working — BUT requires Cloudinary AND requires source to be 'cloudinary' source |
| GET | `/api/analyses/{id}/generated-assets` | Bearer | ✓ Working |
| DELETE | `/api/analyses/{id}/generated-assets/{id}` | Bearer | ✓ Working |
| POST | `/api/cloudinary/signature` | No auth | ✓ Working — returns 503 if not configured |
| GET | `/api/cloudinary/status` | No | ✓ Working |
| GET | `/api/health` | No | ✓ Working |
| GET | `/api/health/cloudinary` | No | ✓ Working |

---

## 3. EXISTING DATABASE TABLES

| Table | Status |
|---|---|
| `users` | ✓ Defined in model + migration |
| `analyses` | ✓ Defined in model + migration |
| `assets` | ✓ Defined in model + migration |
| `performance_records` | ✓ Defined in model + migration |
| `creative_features` | ✓ Defined in model + migration |
| `creative_dna_insights` | ✓ Defined in model + migration |
| `generated_assets` | ✓ Defined in model + migration |

**Database engine currently configured:** SQLite (`sqlite:///./creativepulse_test.db`)  
**Alembic migration:** Exists in `versions/20261002_initial_schema.py`  
**Problem:** Migration uses `sa.text('now()')` — this is PostgreSQL syntax, fails on SQLite. The app uses `Base.metadata.create_all()` on startup as a workaround (bypass of migration strategy).

---

## 4. EXISTING ANALYTICS MODULES

| Module | Status |
|---|---|
| `app/analytics/features.py` — `FeatureExtractor` | ✓ Real PIL/NumPy feature extraction for brightness, contrast, edge density, dominant color, orientation. `human_present` → `None` / `Unavailable` (correct) |
| `app/analytics/metrics.py` — `MetricsCalculator` | ✓ Aggregate-based CTR/CVR/CPC/ROAS/CPM with zero-division safety |
| `app/analytics/statistical.py` — `StatisticalAnalyzer`, `CreativeDNAGenerator` | ✓ Mann-Whitney U, rank-biserial effect size, evidence tiers. Uses "Association does not imply causation" disclaimer |
| `app/services/feature_service.py` — `FeatureService` | **PROBLEM: `_get_demo_features` uses Python built-in `hash()` which is non-deterministic across runs (PYTHONHASHSEED)** |
| `app/services/dna_service.py` — `DNAService` | ✓ Working |
| `app/services/validation_service.py` — `PerformanceValidator` | **PROBLEM: `_check_duplicates` detects duplicates and WARNS but does NOT remove them from DataFrame. The `validate_file` method returns the un-deduplicated DataFrame.** |
| `app/services/pipeline.py` — `AnalysisPipeline` | ✓ Pipeline logic correct. Only 3 stages reported (not 8). Stage names could be richer. |
| `app/services/analysis_service.py` | Need to read — not yet inspected |
| `app/services/cloudinary_service.py` | Need to read — not yet inspected |

---

## 5. EXISTING TESTS

| Test File | Status |
|---|---|
| `tests/conftest.py` | Minimal fixtures only; no HTTP test client set up |
| `tests/test_auth.py` | Not yet read |
| `tests/test_features.py` | Not yet read |
| `tests/test_metrics.py` | Not yet read |
| `tests/test_statistical.py` | Not yet read |
| `tests/test_validation.py` | Not yet read |

**Database for tests:** Backend `.env` points to SQLite test DB. Tests likely use SQLite.

---

## 6. EXISTING INTEGRATIONS

| Integration | Status |
|---|---|
| Cloudinary | NOT CONFIGURED — credentials not in `.env`; app handles this gracefully with 503 responses |
| PostgreSQL | NOT CONFIGURED — `.env` uses SQLite; migration file uses PostgreSQL-specific `now()` |
| LLM / AI Provider | NOT CONFIGURED — no API client, no env vars |
| JWT Authentication | ✓ Configured with `python-jose` + `passlib/bcrypt` |

---

## 7. MISSING FEATURES

| Feature | Gap |
|---|---|
| Creative asset upload (Cloudinary flow) | New analysis wizard has placeholder "Skip & Continue" — no actual Cloudinary upload UI |
| Analysis features endpoint | `/api/analyses/{id}/features` route referenced in plan but not implemented |
| Per-creative feature detail | `/api/analyses/{id}/features/{creative_id}` not implemented |
| AI Assistant grounding | No RAG layer; pure simulated response with `setTimeout` |
| PDF/printable report | Reports page uses `setTimeout` + `alert()` — no real generation |
| Analysis selector (global) | Each page independently queries all analyses; no shared selection state |
| Creative detail page | No route `/library/{creative_id}` exists |
| Demo seed endpoint | No endpoint to seed demo data via API |
| FRONTEND_URL env var | Not defined in backend `.env.example` |

---

## 8. BROKEN INTEGRATIONS

| Item | Problem |
|---|---|
| Login → Dashboard | `handleSubmit` in login page ignores backend entirely; uses `setTimeout` bypass |
| DashboardLayout user | Sets `{ email: 'demo@example.com', id: 1 }` directly; never calls `api.getCurrentUser()` |
| Landing page CTA | "Start Analyzing" links to `/dashboard` regardless of auth state |
| Dashboard KPIs | Hardcoded `demoKPIs` array; backend calls commented out |
| Dashboard DNA insight | Hardcoded `demoInsight` object |
| AI Assistant response | `setTimeout` fake response; says "In production..." — pretends to be real AI |
| Reports generation | `setTimeout` + browser `alert()` |
| Settings save | `setTimeout` fake save |

---

## 9. API MISMATCHES

| Frontend Call | Actual Backend Endpoint | Fix |
|---|---|---|
| `api.executeAnalysis(id)` | Does not exist | Replace with `api.runAnalysis(id)` |
| `api.getAnalysisMetrics(id)` | Does not exist | Replace with `api.getAnalysisOverview(id)`, `api.getAnalysisPerformance(id)`, or `api.getAnalysisAssets(id)` |
| `api.getDNAInsights(id)` | Does not exist | Replace with `api.getCreativeDNA(id)` |
| `api.repurposeAsset(assetId, format)` | Exists but signature is `repurposeAsset(analysisId, { source_asset_id, format })` | Fix call site |
| `analysis.id` used as string in comparisons | Backend returns `id: int` | Fix type — use `number` not `string` in TypeScript |
| `DNAInsight` type used in dna/page.tsx | Not defined in `types/index.ts` | Add type |
| `insight.direction` used in dna/page.tsx | Not a field in `CreativeDNAInsight` | Use `positive_median > negative_median` comparison |
| `insight.with_feature_median` in dna/page.tsx | Fields are `positive_median`/`negative_median` | Fix field names |
| `insight.p_value.toFixed(4)` | `p_value` is `number | null` in response | Guard for null |
| `asset.ctr`, `asset.roas` etc. on `Asset` type in library/page.tsx | `Asset` doesn't have metrics; they come from separate `metrics` object | Fix data shape |
| `asset.record_count` in library/page.tsx | Field doesn't exist on Asset or metrics | Remove or use `total_impressions` etc. |

---

## 10. UI INCONSISTENCIES

| Page | Current Style | Expected Style |
|---|---|---|
| `/login` | Dark design system ✓ | ✓ OK |
| `/signup` | Dark design system ✓ | ✓ OK |
| `/` (landing) | Dark design system ✓ | ✓ OK |
| `/dashboard` | Dark design system ✓ | ✓ OK |
| `/new` | **Old white/gray (`bg-white`, `border-gray-300`, `text-gray-900`, `bg-blue-600`)** | Dark design system |
| `/library` | **Old white/gray** | Dark design system |
| `/dna` | **Old white/gray** | Dark design system |
| `/performance` | **Old white/gray** | Dark design system |
| `/repurpose` | **Old white/gray** | Dark design system |
| `/reports` | **Old white/gray** | Dark design system |
| `/assistant` | **Old white/gray** | Dark design system |
| `/settings` | **Old white/gray** | Dark design system |

8 of 11 dashboard pages use old white/gray styling.

---

## 11. SECURITY PROBLEMS

| Problem | Severity | Location |
|---|---|---|
| Debug `print()` statements log JWT token prefixes and full user data | Medium | `backend/app/core/deps.py` lines 16, 17, 22, 27, 32, 37, 40, 42, 43 |
| CORS `allow_origins=["*"]` | Medium | `backend/app/main.py` |
| Backend `.env` has `JWT_SECRET=test-secret-key-minimum-32-characters-long-for-security` — weak test key | Low (dev only) | `backend/.env` |
| Login bypass — any click reaches dashboard without authentication | Critical | `app/(auth)/login/page.tsx` |
| DashboardLayout bypasses auth check | Critical | `components/DashboardLayout.tsx` |
| Landing CTA sends unauthenticated users to dashboard | High | `app/page.tsx` |
| `CLOUDINARY_API_SECRET` never exposed to browser ✓ | OK | Backend only |

---

## 12. INFRASTRUCTURE BLOCKERS

| Blocker | Impact |
|---|---|
| PostgreSQL not configured — SQLite used | Analysis pipeline works on SQLite for dev/demo. For production, PostgreSQL required. Migration `now()` syntax incompatible with SQLite. |
| Cloudinary not configured | Asset upload UI, Cloudinary repurpose are unavailable. App handles gracefully with 503. |
| LLM provider not configured | AI Assistant cannot be grounded. Will show "not connected" message. |
| `FRONTEND_URL` not in env | CORS uses `*` wildcard — acceptable for hackathon demo. |

---

## CONFIRMED PROBLEMS (VERIFIED AGAINST CODE)

### A. Frontend authentication bypass — CONFIRMED
- `login/page.tsx` line 23: `setTimeout(() => { router.push('/dashboard') }, 500)` — never calls `api.login()`
- `DashboardLayout.tsx` useEffect: `setUser({ email: 'demo@example.com', id: 1 })` — never calls `api.getCurrentUser()`
- `app/page.tsx`: "Start Analyzing" links directly to `/dashboard`

### B. Dashboard bypass — CONFIRMED
- `dashboard/page.tsx`: `useEffect` has `setLoading(false)` with all backend calls commented out
- `demoKPIs` array hardcoded with `$128,420`, `$384,210`, `2.99x`, `3.42%`
- `demoInsight` hardcoded with `Human presence`, `+21.9%`

### C. API contract mismatch — CONFIRMED
- `api.executeAnalysis()` — called in `new/page.tsx:62`, does NOT exist in `api.ts`
- `api.getAnalysisMetrics()` — called in `performance/page.tsx:22`, `library/page.tsx:24`, `repurpose/page.tsx:36` — does NOT exist in `api.ts`
- `api.getDNAInsights()` — called in `dna/page.tsx:19` — does NOT exist in `api.ts`

### D. New Analysis wizard mismatch — CONFIRMED
- `api.createAnalysis(name, description)` called as positional args — but `api.ts` signature is `createAnalysis({ name, description })`
- Wizard step 3 is a pure placeholder with "Skip & Continue" — no Cloudinary upload
- Wizard calls non-existent `api.executeAnalysis()`

### E. Reports simulated — CONFIRMED
- `reports/page.tsx` line 63: `setTimeout(() => { setGenerating(false); alert('Report generated!...') }, 2000)`

### F. AI Assistant simulated — CONFIRMED
- `assistant/page.tsx` uses `setTimeout` fake response
- Response text literally says "In production environment, this would connect to an AI service"

### G. Settings save simulated — CONFIRMED
- `settings/page.tsx` line 36: `setTimeout(() => { setMessage('Settings saved successfully!') ... }, 1000)`
- Notification preferences not persisted

### H. Validation duplicate detection reports but does not remove — CONFIRMED
- `validation_service.py` `_check_duplicates`: reports `duplicate_count` warning but returns without removing
- `validate_file` returns un-deduplicated df

### I. Demo feature generation uses Python `hash()` — CONFIRMED
- `feature_service.py` line 102: `id_hash = hash(creative_id)` — Python's `hash()` is randomized by PYTHONHASHSEED in Python 3.3+, giving different values across runs

### J. Debug token logging — CONFIRMED
- `deps.py` lines 16-43: multiple `print(f"DEBUG: ...")` statements including `print(f"DEBUG: Received token: {token[:20]}...")`

### K. Alembic migration uses PostgreSQL `now()` — CONFIRMED
- `20261002_initial_schema.py`: `server_default=sa.text('now()')` — fails on SQLite

### L. Execution endpoint requires assets — CONFIRMED
- `execution.py` line 24: `if len(analysis.assets) == 0: raise HTTP 400`
- New analysis wizard has no working asset upload — the `run` step will always fail

### M. Analysis.id type inconsistency — CONFIRMED
- Backend: `id: int`
- Frontend `types/index.ts`: `id: number` ✓
- But `library/page.tsx` compares `asset.analysis_id === selectedAnalysis` where `selectedAnalysis` is `string` state

### N. `DNAInsight` type missing from types/index.ts — CONFIRMED
- `dna/page.tsx` imports `{ DNAInsight, Analysis }` from `@/types` but `types/index.ts` exports only `CreativeDNAInsight`, not `DNAInsight`

### O. CORS wildcard — CONFIRMED
- `main.py` line 19: `allow_origins=["*"]`

---

## SUMMARY COUNTS

- **Critical bypasses:** 3 (login, DashboardLayout, execution requires assets)
- **Non-existent API calls:** 3 (`executeAnalysis`, `getAnalysisMetrics`, `getDNAInsights`)
- **Simulated features:** 3 (reports, AI assistant, settings save)
- **Pages with old white/gray styling:** 8 of 11 dashboard pages
- **Missing TypeScript types:** 1 (`DNAInsight`)
- **Security debug logs:** 9 print statements in deps.py
- **Backend correctness bugs:** 2 (duplicate removal, hash() non-determinism)
- **Infrastructure blockers:** 3 (PostgreSQL, Cloudinary, LLM)
