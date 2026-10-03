"""Backend startup script"""
import uvicorn
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

if __name__ == "__main__":
    print("=" * 60)
    print("CreativePulse AI Backend")
    print("=" * 60)
    print()
    print("Starting FastAPI server...")
    print("API documentation will be available at:")
    print("  - Swagger UI: http://localhost:8000/docs")
    print("  - ReDoc: http://localhost:8000/redoc")
    print()
    print("Health check: http://localhost:8000/api/health")
    print()
    print("=" * 60)
    print()
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
