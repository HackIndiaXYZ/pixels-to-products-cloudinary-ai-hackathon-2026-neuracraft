"""Main FastAPI application"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.router import api_router
import logging



# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="AI-powered creative analytics platform for marketing teams",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)


# Configure CORS
# Allow the configured FRONTEND_URL plus localhost variants for development
_allowed_origins = [
    settings.FRONTEND_URL,
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include API router
app.include_router(api_router, prefix="/api")


# Health check endpoints
@app.get("/api/health")
def health_check():
    """
    Health check endpoint
    
    Returns:
        Status information
    """
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": "1.0.0"
    }


@app.get("/api/health/cloudinary")
def cloudinary_health_check():
    """
    Check Cloudinary configuration status
    
    Returns:
        Cloudinary configuration status
    """
    from app.core.cloudinary_config import is_cloudinary_available
    
    return {
        "configured": is_cloudinary_available(),
        "message": "Cloudinary is configured" if is_cloudinary_available() 
                  else "Cloudinary is not configured"
    }


@app.get("/api/health/ai")
def ai_health_check():
    """
    Check AI/LLM configuration status
    
    Returns:
        AI configuration status
    """
    # Check if AI API is configured
    ai_configured = bool(settings.OPENAI_API_BASE and settings.OPENAI_API_KEY)
    
    return {
        "configured": ai_configured,
        "message": "AI Assistant is configured" if ai_configured 
                  else "AI Assistant is not configured",
        "endpoint": settings.OPENAI_API_BASE if ai_configured else None,
        "model": settings.AI_MODEL if ai_configured else None
    }


@app.on_event("startup")
async def startup_event():
    """Application startup event"""
    logger.info(f"Starting {settings.APP_NAME}")
    logger.info(f"Database: {settings.DATABASE_URL.split('@')[-1]}")  # Log without credentials
    logger.info(f"Cloudinary configured: {settings.cloudinary_configured}")
    logger.info(f"AI Assistant configured: {settings.ai_configured}")
    if settings.ai_configured:
        logger.info(f"AI endpoint: {settings.OPENAI_API_BASE}")
        logger.info(f"AI model: {settings.AI_MODEL}")
    
    # Create database tables if they don't exist
    try:
        from app.db.session import engine, Base
        # Import all models so they're registered with Base
        from app.models import User, Analysis, Asset, PerformanceRecord, CreativeFeature, CreativeDNAInsight, GeneratedAsset
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created/verified successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event"""
    logger.info(f"Shutting down {settings.APP_NAME}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
