"""
Run the OCR API server.
"""
import uvicorn
from app.config import get_settings


if __name__ == "__main__":
    settings = get_settings()
    
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║                    🔍 OCR API SERVICE                        ║
╠══════════════════════════════════════════════════════════════╣
║  Starting server...                                          ║
║                                                              ║
║  API Docs:    http://{settings.host}:{settings.port}/docs                          ║
║  ReDoc:       http://{settings.host}:{settings.port}/redoc                         ║
║  Health:      http://{settings.host}:{settings.port}/health                        ║
║                                                              ║
║  Admin Login: POST /admin/login                              ║
║  Username:    {settings.admin_username:<20}                         ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info" if settings.debug else "warning"
    )
