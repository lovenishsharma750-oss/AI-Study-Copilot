from fastapi import FastAPI

from app.api.auth import router as auth_router

app = FastAPI(title="AI Study Copilot API", version="0.1.0")
app.include_router(auth_router)


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Return the service health status."""
    return {"status": "ok"}
