from fastapi import APIRouter, Depends
from app.api.deps import require_api_key

router = APIRouter()


@router.get("/auth/verify", summary="Verify API Key")
async def verify_key(api_key: str = Depends(require_api_key)):
    return {"status": "authenticated", "key_prefix": api_key[:8] + "..."}