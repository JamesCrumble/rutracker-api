import uvicorn

from src.settings import settings

if __name__ == '__main__':
    uvicorn.run(
        app='src:app',
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.AUTORELOAD,
        workers=settings.WORKERS,
    )
