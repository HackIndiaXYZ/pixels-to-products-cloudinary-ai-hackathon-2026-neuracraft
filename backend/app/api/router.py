"""Main API router"""
from fastapi import APIRouter
from app.api.endpoints import auth, analyses, execution, upload, analytics, cloudinary, repurpose, features, assistant


api_router = APIRouter()

# Auth routes
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["authentication"]
)

# Analysis routes
api_router.include_router(
    analyses.router,
    prefix="/analyses",
    tags=["analyses"]
)

# Execution routes (nested under analyses)
api_router.include_router(
    execution.router,
    prefix="/analyses",
    tags=["execution"]
)

# Upload routes (nested under analyses)
api_router.include_router(
    upload.router,
    prefix="/analyses",
    tags=["upload"]
)

# Analytics routes (nested under analyses)
api_router.include_router(
    analytics.router,
    prefix="/analyses",
    tags=["analytics"]
)

# Features routes (nested under analyses)
api_router.include_router(
    features.router,
    prefix="/analyses",
    tags=["features"]
)

# Repurpose routes (nested under analyses)
api_router.include_router(
    repurpose.router,
    prefix="/analyses",
    tags=["repurpose"]
)

# Analytics assistant (nested under analyses)
api_router.include_router(
    assistant.router,
    prefix="/analyses",
    tags=["assistant"]
)

# Cloudinary routes
api_router.include_router(
    cloudinary.router,
    prefix="/cloudinary",
    tags=["cloudinary"]
)
