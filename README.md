# CreativePulse AI

**AI-powered creative intelligence platform for marketing teams.**

CreativePulse connects campaign performance data with real creative assets to identify the visual characteristics statistically associated with stronger results — turning observed patterns into evidence-backed Creative DNA.

---

## The Problem

Marketing teams have campaign metrics and creative assets stored separately. They can see *which* creatives performed well, but struggle to understand *what visual characteristics* are associated with better performance. The gap between "this ad worked" and "this visual pattern is associated with results" costs time and limits evidence-based creative decisions.

## The Solution

CreativePulse bridges that gap:

```
Upload performance CSV  +  Upload real creative images via Cloudinary
            ↓
Automatic metric calculation (CTR, ROAS, CVR, CPC, CPM)
            ↓
Visual feature extraction (brightness, contrast, orientation, edge density…)
            ↓
Statistical comparison of visual groups (Mann-Whitney U test)
            ↓
Creative DNA — evidence-tiered visual-performance associations
            ↓
Data-grounded AI Assistant — answers from your actual data, no fabrication
            ↓
Repurpose high-performing creatives into new formats via Cloudinary
```

---

## Core Features

| Feature | Description |
|---|---|
| **Campaign Analytics** | CTR, ROAS, CVR, CPC, CPM computed from your uploaded data |
| **CSV/Excel ingestion** | Flexible column mapping with alias support |
| **Data validation** | Row-level checks, duplicate detection, excluded-row reporting |
| **Creative Library** | Browse Cloudinary-hosted assets with per-creative performance |
| **Visual Analysis** | Pixel-level feature extraction from real images |
| **Creative DNA** | Evidence-tiered statistical associations (not guesses) |
| **AI Assistant** | Natural-language Q&A backed entirely by your database |
| **Reports** | Printable analysis report with full methodology disclosure |
| **Repurpose** | Transform creatives into 4:5, 9:16, 16:9, 1:1 via Cloudinary |

---

## Cloudinary Integration

Cloudinary is central to CreativePulse's visual intelligence pipeline:

1. **Signed uploads** — the backend generates a secure upload signature; the browser uploads directly to Cloudinary without exposing the API secret.
2. **Asset management** — every uploaded creative is stored in Cloudinary under `creativepulse/{analysis_id}/{creative_id}`.
3. **Visual analysis** — the pipeline fetches images from their Cloudinary secure URLs and extracts pixel-level features.
4. **Creative DNA** — visual features from real Cloudinary-hosted images feed the statistical engine.
5. **Repurposing** — Cloudinary transformations produce new aspect-ratio variants of high-performing creatives.

The application works in performance-only mode without Cloudinary (CSV metrics still calculated), but visual analysis and repurposing require Cloudinary credentials.

---

## Architecture

```
Browser (Next.js 14 / TypeScript)
        │
        │  REST API + CORS
        ▼
FastAPI backend (Python)
        │
        ├─── SQLite / PostgreSQL (analyses, assets, metrics, DNA)
        │
        ├─── Cloudinary SDK (asset upload, transformations)
        │         ▲
        │         └── Browser uploads directly (signed)
        │
        └─── Analytics pipeline
                ├── Metrics (MetricsCalculator)
                ├── Feature extraction (FeatureExtractor — Pillow)
                ├── Statistics (Mann-Whitney U — SciPy)
                └── Creative DNA (CreativeDNAGenerator)
```

---

## Data Integrity Principles

- **No synthetic data** — visual features are extracted only from real uploaded images.
- **Placeholder isolation** — placeholder assets produce `null` features and never contribute to Creative DNA.
- **Evidence gating** — DNA requires ≥2 real creatives with extracted features before any comparison is attempted.
- **Honest evidence tiers** — insufficient sample sizes are explicitly marked `insufficient_evidence`, not silently promoted.
- **Association, not causation** — the UI and assistant always say "associated with", never "causes".
- **Metrics from your data** — all displayed numbers are calculated from your uploaded CSV records; nothing is hardcoded.

---

## Performance Metrics Formulas

| Metric | Formula |
|---|---|
| CTR | clicks ÷ impressions |
| CVR | conversions ÷ clicks |
| CPC | spend ÷ clicks |
| ROAS | revenue ÷ spend |
| CPM | (spend ÷ impressions) × 1,000 |

Division-by-zero is handled safely throughout.

---

## Creative DNA — Statistical Method

For each binary visual feature (bright background, portrait orientation, landscape, human present), creatives are split into two groups and compared using:

- **Mann-Whitney U test** — non-parametric, appropriate for skewed performance distributions
- **Rank-biserial effect size** — quantifies magnitude of difference
- **Minimum 5 creatives per group** — enforced before any test is run
- **Minimum 2 real creatives total** — enforced at the pipeline level

Evidence tiers: **Strong → Moderate → Weak → No Clear Evidence → Insufficient Evidence**

---

## AI Assistant

The assistant is deterministic and grounded in your analysis data:

- Answers come directly from `performance_records`, `creative_dna_insights`, and `creative_features` tables
- No LLM calls are made; no numbers are fabricated
- Supports 20+ intent patterns: ROAS, CTR, CVR, spend, revenue, creative rankings, platform breakdowns, DNA summaries, date ranges, and more
- Every answer cites its data source

---

## Setup

### Prerequisites

- Python 3.10+
- Node.js 18+
- A Cloudinary account (free tier sufficient for development)

### 1. Clone and configure

```bash
git clone https://github.com/HackIndiaXYZ/pixels-to-products-cloudinary-ai-hackathon-2026-neuracraft.git
cd pixels-to-products-cloudinary-ai-hackathon-2026-neuracraft

cp .env.example backend/.env
# Edit backend/.env with your actual values
```

### 2. Backend setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate
# Activate (Unix/Mac)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start the server (tables are created automatically on startup)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Frontend setup

```bash
cd frontend

# Configure API URL
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local

# Install dependencies
npm install

# Start development server
npm run dev
```

Open http://localhost:3000

### 4. Environment variables (backend/.env)

| Variable | Required | Description |
|---|---|---|
| `DATABASE_URL` | Yes | SQLite or PostgreSQL connection string |
| `JWT_SECRET` | Yes | Random secret ≥32 chars — `python -c "import secrets; print(secrets.token_urlsafe(64))"` |
| `CLOUDINARY_CLOUD_NAME` | Optional | Enables image upload and repurposing |
| `CLOUDINARY_API_KEY` | Optional | Cloudinary API key |
| `CLOUDINARY_API_SECRET` | Optional | Cloudinary API secret (never exposed to browser) |
| `OPENAI_API_BASE` | Optional | OpenAI-compatible LLM endpoint (assistant works without it) |
| `OPENAI_API_KEY` | Optional | LLM API key |
| `AI_MODEL` | Optional | Model name |

---

## Running Tests

```bash
# Backend (118 tests)
cd backend
pytest

# Frontend TypeScript check
cd frontend
npx tsc --noEmit

# Frontend production build
npm run build
```

### Verified test state

| Check | Result |
|---|---|
| Backend tests | 118 / 118 PASS |
| TypeScript | PASS (0 errors) |
| Production build | PASS (16/16 routes) |

---

## API Documentation

With the backend running:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## Project Structure

```
.
├── backend/                  FastAPI backend
│   ├── app/
│   │   ├── api/endpoints/    Route handlers
│   │   ├── analytics/        Metrics, features, statistics
│   │   ├── core/             Config, security, dependencies
│   │   ├── db/               Session management
│   │   ├── models/           SQLAlchemy models
│   │   ├── schemas/          Pydantic schemas
│   │   └── services/         Pipeline, DNA, features
│   ├── alembic/              Database migrations
│   ├── tests/                118 pytest tests
│   └── requirements.txt
│
├── frontend/                 Next.js 14 frontend
│   ├── app/
│   │   ├── (auth)/           Login, signup
│   │   └── (dashboard)/      All dashboard routes
│   ├── components/           Shared UI components
│   ├── lib/                  API client, error handling
│   └── types/                TypeScript type definitions
│
├── .env.example              Environment variable template
├── .gitignore
└── README.md
```

---

## Security

- JWT authentication (HS256, configurable expiry)
- bcrypt password hashing
- All secrets via environment variables — never in source code
- Cloudinary signed uploads — API secret stays server-side
- Analysis ownership enforced on every endpoint
- CORS restricted to configured frontend origin

---

## Limitations

- Creative DNA identifies associations, not causes
- Small datasets (< 5 creatives per feature group) return `insufficient_evidence`
- Visual feature extraction covers brightness, contrast, edge density, orientation, and dominant colour; deep semantic features require a trained model
- Platform differences may confound results
- Temporal factors are not modelled

---

## Hackathon

**Team:** NeuraCraft  
**Event:** HackIndia × Cloudinary 2026  
**Track:** Pixels to Products — Cloudinary AI  
**Theme:** Real creative intelligence from real creative data

---

*Association does not imply causation. CreativePulse identifies statistical patterns in your dataset.*
