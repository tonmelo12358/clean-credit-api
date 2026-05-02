from datetime import datetime, timezone

from fastapi import FastAPI
from app.api.proposal_routes import router as proposal_router
from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    timestamp: datetime


app = FastAPI(title="CleanCredit API")

# Incluir roteadores da API
app.include_router(proposal_router)


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health() -> HealthResponse:
    """Health check endpoint.

    Returns a simple status and the current UTC timestamp in ISO 8601.
    """
    now = datetime.now(timezone.utc)
    return HealthResponse(status="ok", timestamp=now)
