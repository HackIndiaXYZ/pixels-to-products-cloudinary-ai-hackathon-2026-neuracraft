# CreativePulse AI Backend

FastAPI-based backend for the CreativePulse AI platform.

## Setup

### 1. Create Virtual Environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Unix/Mac
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

Create a `.env` file in the `backend/` directory:

```bash
DATABASE_URL=postgresql://user:password@localhost:5432/creativepulse
JWT_SECRET=your-secret-key-minimum-32-characters-long
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key
CLOUDINARY_API_SECRET=your-api-secret
```

### 4. Run Database Migrations

```bash
alembic upgrade head
```

### 5. Start the Server

```bash
python start.py
```

Or using uvicorn directly:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Running Tests

```bash
pytest
```

With coverage:

```bash
pytest --cov=app --cov-report=html
```

## Database Migrations

### Create a new migration

```bash
alembic revision --autogenerate -m "Description of changes"
```

### Apply migrations

```bash
alembic upgrade head
```

### Rollback one migration

```bash
alembic downgrade -1
```

### View migration history

```bash
alembic history
```

## Project Structure

```
backend/
├── app/
│   ├── api/
│   │   ├── endpoints/      # API endpoint handlers
│   │   └── router.py       # API router configuration
│   ├── analytics/          # Analytics and statistics modules
│   ├── core/               # Core configuration and security
│   ├── db/                 # Database connection and session
│   ├── models/             # SQLAlchemy models
│   ├── schemas/            # Pydantic schemas
│   ├── services/           # Business logic services
│   └── main.py             # FastAPI application
├── alembic/                # Database migrations
├── tests/                  # Test suite
├── requirements.txt        # Production dependencies
└── start.py                # Startup script
```

## Development

### Code Style

This project uses:
- Black for code formatting
- Flake8 for linting
- MyPy for type checking

### Testing

Write tests in the `tests/` directory. Follow the naming convention `test_*.py`.

### Logging

The application uses Python's built-in logging module. Logs are output to stdout.

## Troubleshooting

### Database Connection Issues

Ensure PostgreSQL is running and the connection string in `.env` is correct.

### Missing Dependencies

Run `pip install -r requirements.txt` again.

### Migration Issues

If migrations fail, check the database connection and ensure all models are imported in `alembic/env.py`.
