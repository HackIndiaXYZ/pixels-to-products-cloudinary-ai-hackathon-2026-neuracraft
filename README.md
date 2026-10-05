CreativePulse AI

AI-powered creative intelligence platform for marketing teams.

Live Demo AI Assistant

Live Demo: https://creativepulse-ai-one.vercel.app
AI Assistant: https://creativepulse-ai-one.vercel.app/assistant
Source Code: https://github.com/HackIndiaXYZ/pixels-to-products-cloudinary-ai-hackathon-2026-neuracraft

CreativePulse connects campaign performance data with real creative assets to identify the visual characteristics statistically associated with stronger results — turning observed patterns into evidence-backed Creative DNA.


---

Overview

Marketing teams often have campaign performance metrics and creative assets stored separately. While teams can identify which creatives performed well, they often struggle to understand which visual characteristics are associated with stronger performance.

CreativePulse bridges this gap by combining campaign analytics, real creative assets, visual feature extraction, statistical analysis, and evidence-based Creative DNA in one platform.


---

The Problem

Marketing teams can answer:

> Which ad performed best?



But answering:

> What visual characteristics are associated with better performance?



requires connecting performance data with the actual creative assets.

CreativePulse addresses this problem by building a data-driven connection between campaign performance and creative characteristics.


---

The Solution

Campaign Performance Data + Real Creative Assets
                       │
                       ▼
                Data Validation
                       │
                       ▼
              Campaign Metrics
            CTR • ROAS • CVR • CPC • CPM
                       │
                       ▼
             Visual Feature Extraction
                       │
                       ▼
              Statistical Analysis
                Mann-Whitney U
                       │
                       ▼
                 Creative DNA
                       │
                       ▼
              Data-Grounded Assistant
                       │
                       ▼
              Creative Repurposing


---

Core Features

Feature	Description

Campaign Analytics	Calculates CTR, ROAS, CVR, CPC, and CPM from uploaded campaign data
CSV/Excel Ingestion	Supports flexible column mapping with alias support
Data Validation	Performs row-level validation, duplicate detection, and excluded-row reporting
Creative Library	Displays Cloudinary-hosted creative assets with associated performance
Visual Analysis	Extracts pixel-level visual characteristics from real images
Creative DNA	Identifies evidence-tiered statistical associations between visual features and performance
AI Assistant	Provides natural-language answers grounded in the application's analysis data
Reports	Generates printable analysis reports with methodology disclosure
Creative Repurposing	Transforms creatives into multiple aspect ratios using Cloudinary



---

Product Workflow

1. Upload campaign performance data.


2. Upload real creative assets through Cloudinary.


3. Validate and process the campaign data.


4. Calculate campaign performance metrics.


5. Extract visual features from the uploaded creatives.


6. Compare visual groups statistically.


7. Generate evidence-tiered Creative DNA insights.


8. Explore insights using the data-grounded Analytics Assistant.


9. Repurpose high-performing creatives into new formats.




---

Cloudinary Integration

Cloudinary is a core part of CreativePulse's visual intelligence workflow.

Signed Uploads

The backend generates secure Cloudinary upload signatures, allowing the browser to upload directly without exposing the Cloudinary API secret.

Asset Management

Creative assets are stored using the following structure:

creativepulse/{analysis_id}/{creative_id}

Visual Analysis

The analytics pipeline retrieves images from their Cloudinary secure URLs and extracts pixel-level visual characteristics.

Creative DNA

Visual features extracted from real Cloudinary-hosted images are used as inputs to the statistical analysis pipeline.

Creative Repurposing

Cloudinary transformations generate new creative variants for:

4:5

9:16

16:9

1:1


Performance-only analytics can operate without Cloudinary. Visual analysis and creative repurposing require Cloudinary credentials.


---

Architecture

┌─────────────────────────────────────┐
│       Browser / Next.js 14          │
│       TypeScript + Tailwind         │
└──────────────────┬──────────────────┘
                   │
                   │ REST API + CORS
                   ▼
┌─────────────────────────────────────┐
│           FastAPI Backend           │
│              Python                 │
└───────┬─────────────┬───────────────┘
        │             │
        ▼             ▼
┌──────────────┐  ┌──────────────────┐
│ Database     │  │    Cloudinary    │
│              │  │                  │
│ Analyses     │  │ Signed Uploads   │
│ Assets       │  │ Media Storage    │
│ Performance  │  │ Secure Delivery  │
│ DNA Insights │  │ Transformations  │
└──────────────┘  └──────────────────┘
        │
        ▼
┌─────────────────────────────────────┐
│         Analytics Pipeline          │
│                                     │
│ Metrics → Features → Statistics     │
│              → Creative DNA         │
└─────────────────────────────────────┘


---

Technology Stack

Frontend

Next.js 14

React

TypeScript

Tailwind CSS


Backend

FastAPI

Python

SQLAlchemy

Pydantic


Analytics

Pandas

NumPy

SciPy

Pillow


Database

SQLite

PostgreSQL-compatible architecture


Media

Cloudinary


Authentication

JWT

bcrypt



---

Performance Metrics

CreativePulse calculates the following metrics directly from uploaded campaign data.

Metric	Formula

CTR	clicks ÷ impressions
CVR	conversions ÷ clicks
CPC	spend ÷ clicks
ROAS	revenue ÷ spend
CPM	(spend ÷ impressions) × 1,000


Division-by-zero cases are handled safely throughout the analytics pipeline.


---

Creative DNA

Creative DNA identifies visual characteristics that are statistically associated with differences in creative performance.

Supported visual characteristics include:

Bright background

Portrait orientation

Landscape orientation

Human presence

Brightness

Contrast

Edge density

Dominant colour


Statistical Method

For supported binary visual features, creatives are divided into two groups and their performance distributions are compared using:

Mann-Whitney U test

Rank-biserial effect size


The Mann-Whitney U test provides a non-parametric comparison of performance distributions, while rank-biserial effect size describes the magnitude and direction of the observed difference.

Evidence Requirements

Statistical comparisons require a minimum of:

5 creatives per comparison group

2 real creatives with extracted visual features at the pipeline level


Evidence Tiers

Insights are classified as:

Strong

Moderate

Weak

No Clear Evidence

Insufficient Evidence


This prevents insufficient sample sizes from being presented as strong evidence.


---

Data Integrity

CreativePulse is designed around evidence-based analysis.

No Synthetic Visual Data

Visual features are extracted only from real uploaded images.

Placeholder Isolation

Placeholder assets produce null visual features and never contribute to Creative DNA.

Evidence Gating

Creative DNA comparisons are only attempted when sufficient real visual data is available.

Honest Evidence Tiers

Insufficient sample sizes are explicitly classified as insufficient_evidence.

Association, Not Causation

CreativePulse reports statistical associations rather than causal relationships.

The system uses language such as:

> "associated with"



rather than:

> "causes"



Metrics From Uploaded Data

Campaign metrics are calculated from the uploaded campaign records and are not hardcoded into the analytics pipeline.


---

AI Assistant

CreativePulse includes a data-grounded Analytics Assistant for natural-language exploration of campaign insights.

The production assistant operates in deterministic analytics mode and does not require an LLM.

Data Sources

The assistant answers questions using application data from:

performance_records
creative_dna_insights
creative_features

Supported Queries

The assistant supports 20+ intent patterns, including:

ROAS

CTR

CVR

Spend

Revenue

Creative rankings

Platform breakdowns

Creative DNA summaries

Date-range analysis

Performance comparisons


Grounding Principles

The assistant:

Uses actual analysis data

Does not fabricate numbers

Does not invent insights

Does not make causal claims

Provides data sources for its answers



---

Creative Library

The Creative Library connects campaign performance with the actual creative assets used in campaigns.

Users can explore:

Creative assets

Creative performance

Cloudinary media

Extracted visual features

Creative DNA relationships


This creates a direct workflow from:

Performance
     ↓
Creative
     ↓
Visual Characteristics
     ↓
Evidence


---

Creative Repurposing

High-performing creatives can be transformed into new formats using Cloudinary transformations.

Supported formats:

4:5
9:16
16:9
1:1

This enables teams to adapt successful creatives for different channels and placements.


---

Reports

CreativePulse provides printable reports containing:

Campaign metrics

Creative performance

Creative DNA findings

Statistical methodology

Evidence tiers

Analysis limitations


The methodology and evidence behind the results are explicitly disclosed.


---

Security

JWT authentication with configurable expiry

bcrypt password hashing

Environment-based secret management

Cloudinary signed uploads

Server-side Cloudinary API secret protection

Analysis ownership enforcement

CORS restricted to the configured frontend origin



---

Project Structure

.
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── endpoints/
│   │   ├── analytics/
│   │   ├── core/
│   │   ├── db/
│   │   ├── models/
│   │   ├── schemas/
│   │   └── services/
│   ├── alembic/
│   ├── tests/
│   └── requirements.txt
│
├── frontend/
│   ├── app/
│   │   ├── (auth)/
│   │   └── (dashboard)/
│   ├── components/
│   ├── lib/
│   └── types/
│
├── .env.example
├── .gitignore
└── README.md


---

Setup

Prerequisites

Python 3.10+

Node.js 18+

Cloudinary account


Clone the Repository

git clone https://github.com/HackIndiaXYZ/pixels-to-products-cloudinary-ai-hackathon-2026-neuracraft.git
cd pixels-to-products-cloudinary-ai-hackathon-2026-neuracraft

Backend

cd backend

python -m venv venv

Windows

venv\Scripts\activate

macOS / Linux

source venv/bin/activate

Install dependencies:

pip install -r requirements.txt

Create the environment file:

cp ../.env.example .env

Configure the required values and start the server:

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

Frontend

Open a new terminal:

cd frontend
npm install

Create .env.local:

NEXT_PUBLIC_API_URL=http://localhost:8000

Start the development server:

npm run dev

Open:

http://localhost:3000


---

Environment Variables

Variable	Required	Description

DATABASE_URL	Yes	SQLite or PostgreSQL connection string
JWT_SECRET	Yes	Random secret of at least 32 characters
CLOUDINARY_CLOUD_NAME	Optional	Cloudinary cloud name
CLOUDINARY_API_KEY	Optional	Cloudinary API key
CLOUDINARY_API_SECRET	Optional	Cloudinary API secret
OPENAI_API_BASE	Optional	OpenAI-compatible LLM endpoint for development
OPENAI_API_KEY	Optional	LLM API key
AI_MODEL	Optional	Model name


Generate a secure JWT secret:

python -c "import secrets; print(secrets.token_urlsafe(64))"

Never commit real secrets or .env files to the repository.


---

API Documentation

When running locally:

Swagger UI

http://localhost:8000/docs

ReDoc

http://localhost:8000/redoc


---

Testing

Backend

cd backend
pytest

Frontend TypeScript

cd frontend
npx tsc --noEmit

Production Build

npm run build

Verified Test State

Check	Result

Backend tests	118 / 118 PASS
TypeScript	PASS — 0 errors
Production build	PASS — 16/16 routes



---

Limitations

Association Is Not Causation

Creative DNA identifies statistical associations and does not establish causality.

Small Datasets

Datasets with fewer than 5 creatives per feature group are marked as insufficient evidence.

Visual Feature Coverage

Current visual feature extraction focuses on characteristics such as brightness, contrast, edge density, orientation, and dominant colour.

Deep semantic visual understanding would require a trained or multimodal model.

Platform Differences

Differences between advertising platforms may influence performance and act as confounding factors.

Temporal Factors

The current analysis does not model temporal effects such as seasonality, changing audiences, or campaign-period effects.


---

Live Demo

Web Application:
https://creativepulse-ai-one.vercel.app

Analytics Assistant:
https://creativepulse-ai-one.vercel.app/assistant

Source Code:
https://github.com/HackIndiaXYZ/pixels-to-products-cloudinary-ai-hackathon-2026-neuracraft


---

Hackathon

Team: NeuraCraft

Event: HackIndia × Cloudinary 2026

Track: Pixels to Products — Cloudinary AI

Theme: Real creative intelligence from real creative data


---

Key Idea

> Campaign data tells you what performed. Creative assets show you what was created. Creative DNA connects the two.



CreativePulse turns campaign performance data and real creative assets into evidence-based creative intelligence, helping marketing teams make faster and more informed creative decisions.
