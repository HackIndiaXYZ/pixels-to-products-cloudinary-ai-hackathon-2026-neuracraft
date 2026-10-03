# CreativePulse AI - Quick Start Guide

Get CreativePulse AI running in 5 minutes!

## Prerequisites

- Python 3.9+
- Node.js 18+
- PostgreSQL 13+

## Step 1: Clone & Setup (1 min)

```bash
cd "Hackathon Project"
```

## Step 2: Backend Setup (2 min)

```bash
# Navigate to backend
cd backend

# Install dependencies
pip install -r requirements.txt

# Create database
createdb creativepulse

# Set up environment
cp ../.env.example .env
# Edit .env and update DATABASE_URL if needed

# Run migrations
alembic upgrade head

# Start backend
python start.py
```

Backend now running at **http://localhost:8000**

## Step 3: Frontend Setup (2 min)

Open a new terminal:

```bash
# Navigate to frontend
cd frontend

# Install dependencies (if not done already)
npm install

# Set up environment
cp .env.local.example .env.local
# Default API URL is http://localhost:8000

# Start frontend
npm run dev
```

Frontend now running at **http://localhost:3000**

## Step 4: Test the Platform (<1 min)

### Option A: Use the UI

1. Visit http://localhost:3000
2. Click "Sign up"
3. Create account (email + password)
4. You're in! Click "New Analysis" to start

### Option B: Run Demo Script

```bash
# In a new terminal, from project root
cd backend
python ../scripts/run_demo_analysis.py
```

This creates a demo analysis with:
- 40 creatives
- 471 performance records  
- Computed metrics
- Creative DNA insights

## Step 5: Explore Features

### Dashboard Pages

- **Dashboard** - Overview and analysis list
- **Creative Library** - Browse assets with metrics
- **Creative DNA** - Pattern insights
- **Performance** - Analytics dashboard
- **Repurpose** - Transform assets (needs Cloudinary)
- **AI Assistant** - Chat interface
- **Reports** - Export reports
- **Settings** - User preferences

### API Documentation

Visit: http://localhost:8000/docs (Swagger UI)

### Health Check

```bash
curl http://localhost:8000/health
# Returns: {"status": "healthy"}
```

## Common Issues

### Backend won't start

**Issue:** Database connection error  
**Fix:** Check DATABASE_URL in `.env`, ensure PostgreSQL is running

### Frontend shows "Network Error"

**Issue:** Backend not running  
**Fix:** Start backend first: `cd backend && python start.py`

### npm install fails

**Issue:** Network timeout  
**Fix:** Try: `npm install --prefer-offline`

## What's Next?

### Customize

1. Edit `backend/.env` for your config
2. Edit `frontend/.env.local` for API URL
3. Add Cloudinary credentials (optional)

### Deploy

See `DEPLOYMENT_GUIDE.md` for production setup

### Learn More

- `README.md` - Full architecture
- `FRONTEND_COMPLETE_GUIDE.md` - Frontend details
- `backend/README.md` - Backend API docs
- `FINAL_VERIFICATION_REPORT.md` - Complete verification

## Quick Commands

```bash
# Backend
cd backend
python start.py              # Start server
pytest                       # Run tests
python ../scripts/run_demo_analysis.py  # Demo data

# Frontend
cd frontend
npm run dev                  # Development
npm run build                # Production build
npm start                    # Production server

# Database
alembic upgrade head         # Run migrations
alembic downgrade -1         # Rollback one migration
```

## Support

- Backend issues? Check `backend/README.md`
- Frontend issues? Check `FRONTEND_COMPLETE_GUIDE.md`
- Deployment? Check `DEPLOYMENT_GUIDE.md`

---

**You're all set! 🚀**

Visit http://localhost:3000 to start using CreativePulse AI.
