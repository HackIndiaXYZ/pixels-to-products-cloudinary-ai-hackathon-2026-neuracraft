# CreativePulse AI — Audit Findings & Fix Record

**Date:** 2026-10-02  
**Scope:** Data contamination, column normalisation, pipeline integrity, wizard UX

---

## Problem 1 — Demo data automatically contaminated real user analyses

### Root cause

Two separate mechanisms silently injected demo data into a user's analysis after
they uploaded their own CSV:

**Mechanism A — Pipeline Stage 4 (`pipeline.py`)**  
`AnalysisPipeline.run_complete_pipeline()` contained a Stage 4 block that, if
`asset_count == 0`, called `_auto_register_demo_assets()`. That helper queried
`PerformanceRecord` for all unique `creative_id` values and created `Asset`
rows with `source="local_demo"` for each one. This ran automatically every time
a user ran an analysis without having uploaded Cloudinary images — i.e. in the
normal no-Cloudinary flow.

**Mechanism B — Wizard Step 3 button (`new/page.tsx`)**  
Step 3 of the New Analysis wizard displayed a "Register demo assets" button
that called `api.seedDemoData(analysisId)`. That backend endpoint (`seed-demo`)
**deleted all existing performance records** for the analysis before inserting
~400 deterministic demo records for 40 demo creative IDs (C001–C040). The
effect: a user who clicked "Register demo assets" after uploading their 100-row
CSV would silently lose their real data and receive 471 fake records instead.

### What was changed

**`backend/app/services/pipeline.py`** — completely rewritten:
- Stage 4 (`Auto-register demo assets`) removed in its entirety.
- `_auto_register_demo_assets()` helper removed.
- No-assets case now: visual feature extraction is skipped; DNA is skipped; the
  pipeline completes successfully with performance-only results and logs
  `"Creative DNA unavailable — no assets registered"`.
- The pipeline now contains an explicit data-integrity guarantee comment
  stating it will never create, modify, or delete performance records or assets.

**`backend/app/api/endpoints/analyses.py`** — `seed_demo_data` endpoint hardened:
- Added a safety guard at the top: queries `PerformanceRecord` count for the
  analysis and raises `HTTP 409 CONFLICT` if any records exist.
- Error message explains exactly what happened and instructs the user to create
  a new empty analysis for demo exploration.
- The endpoint still exists for development/demo use but can no longer
  contaminate an analysis that holds user-uploaded data.

**`frontend/app/(dashboard)/new/page.tsx`** — Step 3 fully redesigned:
- `handleSeedDemo` function and its `api.seedDemoData()` call removed.
- `demoSeeded` / `Database` icon state removed.
- New flow: the backend upload response now returns `creative_ids` — the exact
  unique creative IDs from the user's uploaded CSV.
- Step 3 displays those IDs as labelled chips so the user can see exactly what
  came from their file.
- A new "Register placeholder assets" button calls
  `api.registerPlaceholderAssets(analysisId, uploadedCreativeIds)` which
  creates `local_demo` placeholder `Asset` rows for exactly those IDs — and
  only those IDs. It refuses to register any ID that is not already present in
  the analysis's performance records.
- The info note "Demo assets will be auto-registered if none exist" removed
  (that referred to the now-removed pipeline Stage 4).
- Review step now shows an honest message when no assets are registered:
  "No assets registered — analysis will complete with performance data only
  (Creative DNA unavailable)".

---

## Problem 2 — Column normalization was case/whitespace only

### Root cause

`PerformanceValidator._validate_columns()` lowercased and stripped whitespace
from column names but had no alias mapping. A CSV with headers like `ad_id`,
`cost`, `sales`, `purchases`, or `Creative ID` would fail with a
`MISSING_COLUMNS` error even though the data was semantically valid.

### What was changed

**`backend/app/services/validation_service.py`** — rewritten with alias layer:
- Added `COLUMN_ALIASES` dictionary mapping canonical names to lists of common
  real-world variants (see the module docstring for the full table).
- Added `_normalise_token()` (lowercase, collapse spaces/dashes to underscore).
- Added `_build_reverse_alias_map()` that constructs an O(1) lookup dict from
  normalised alias → canonical name.
- New `_normalise_columns()` method renames DataFrame columns to their canonical
  equivalents before any other validation. It:
  - Emits a `COLUMN_ALIAS_MAPPING` warning listing every mapping applied.
  - Handles duplicate canonical mappings (if two columns both map to the same
    canonical name, keeps the first and drops the second with a log warning).
  - Does not attempt to map columns it does not recognise — they remain with
    their normalised name and are ignored downstream.
- `_validate_columns()` renamed to `_check_required_columns()` and now runs
  after normalisation; its error message includes the list of present columns
  after normalisation so the user can diagnose unmapped fields.
- Backward-compatible: CSVs using exact canonical names still pass without any
  `COLUMN_ALIAS_MAPPING` warning.
- Creative IDs are never remapped — they pass through verbatim. A file with
  `ad_id` values `['creative_001', 'creative_002']` will produce
  `creative_id` values `['creative_001', 'creative_002']`, not `C001`, `C002`.

---

## Problem 3 — Upload response did not include the creative IDs

### Root cause

`PerformanceUploadResponse` returned only `validation`, `records_created`, and
`message`. The frontend had no way to know which creative IDs were in the
uploaded file without making a separate API call.

### What was changed

**`backend/app/schemas/validation.py`**  
Added `creative_ids: List[str] = []` field to `PerformanceUploadResponse`.

**`backend/app/api/endpoints/upload.py`**  
- Populates `creative_ids` from `valid_df['creative_id'].astype(str).unique()`,
  sorted alphabetically.
- Added new endpoint: `POST /{analysis_id}/assets/register-placeholders`
  - Accepts a JSON body `List[str]` of creative IDs.
  - Validates that each ID exists in `PerformanceRecord` for the analysis.
  - Creates `Asset` rows with `source="local_demo"` for IDs not yet registered.
  - Rejects IDs not found in performance data (cannot register phantom creatives).
  - Never touches performance records.
  - Returns detailed result: registered / skipped / rejected with explanations.

**`frontend/types/index.ts`**  
Added `creative_ids: string[]` to `PerformanceUploadResponse`.

**`frontend/lib/api.ts`**  
Added `registerPlaceholderAssets(analysisId, creativeIds)` method.

---

## Problem 4 — No .env.local in frontend

The `frontend/.env.local` file did not exist (only `.env.local.example`), so
`NEXT_PUBLIC_API_URL` was not set and the frontend fell back to the hardcoded
default `http://localhost:8000`.

### What was changed

Created `frontend/.env.local` with `NEXT_PUBLIC_API_URL=http://localhost:8000`.  
Updated `.env.example` (root) to include `FRONTEND_URL` and document the
SQLite-vs-PostgreSQL distinction clearly.

---

## Tests

| Suite | Before | After | Delta |
|---|---|---|---|
| test_auth.py | 5/5 | 5/5 | — |
| test_features.py | 10/10 | 10/10 | — |
| test_metrics.py | 10/10 | 10/10 | — |
| test_statistical.py | 12/12 | 12/12 | — |
| test_validation.py | 9/9 | 18/18 | +9 alias tests |
| **Total** | **46/46** | **55/55** | **+9** |

All 55 backend tests pass. TypeScript compilation passes. Production build
succeeds (13/13 routes).

---

## Data integrity guarantee — post-fix

After these changes, the following invariant holds:

> If a user uploads a CSV with **N valid rows** and **K unique creative IDs**,
> the analysis will contain exactly **N performance records** and at most **K assets**
> after running the pipeline — regardless of whether Cloudinary is configured.

Specifically:
- The pipeline will never add performance records.
- The pipeline will never add assets the user did not explicitly register.
- The `seed-demo` endpoint will return HTTP 409 if any performance records
  already exist, preventing demo data from overwriting real data.
- The "Register placeholders" wizard action creates assets only for creative IDs
  already in the user's performance dataset.

---

## Remaining known limitations

| Item | Status | Notes |
|---|---|---|
| PostgreSQL | BLOCKED — not configured | SQLite used for dev; set `DATABASE_URL` to PostgreSQL for production |
| Cloudinary upload | BLOCKED — not configured | Assets can be registered as `local_demo` placeholders; real image extraction requires Cloudinary credentials |
| AI Assistant (LLM) | BLOCKED — not configured | Shows grounded navigation using real analysis data; LLM responses require provider configuration |
| Creative detail page | NOT IMPLEMENTED | Assets visible in library card view; no `/library/[id]` detail route |
| Alembic vs SQLite | KNOWN LIMITATION | Alembic migration uses PostgreSQL `now()` syntax; `create_all()` fallback used for SQLite dev |
