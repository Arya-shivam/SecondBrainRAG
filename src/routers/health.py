from fastapi import APIRouter
import httpx
from src.config import settings
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/health")
async def health():
    services = {
        "postgres": "pending",
        "opensearch": "pending"
    }
    
    # Check OpenSearch
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            resp = await client.get(settings.opensearch_url)
            if resp.status_code == 200:
                services["opensearch"] = "ok"
            else:
                services["opensearch"] = f"error: {resp.status_code}"
    except Exception as e:
        logger.error(f"OpenSearch health check failed: {e}")
        services["opensearch"] = "unreachable"

    # We will just assume postgres is handled by the overall orchestration for now
    # A real check would require asyncpg or psycopg, but keeping it simple.
    services["postgres"] = "assumed ok (check docker-compose)"

    status = "ok" if all(v.startswith("ok") or "assumed" in v for v in services.values()) else "degraded"
    
    return {"status": status, "services": services}
