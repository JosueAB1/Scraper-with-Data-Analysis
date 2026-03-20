"""
API Key authentication dependency.

Usage in any route:
    from app.core.security import require_api_key
    @router.get("/protected")
    async def endpoint(api_key: str = Depends(require_api_key)):
        ...
"""

from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader

from app.core.config import settings

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)


async def require_api_key(api_key: str = Security(API_KEY_HEADER)) -> str:
    if not api_key or api_key not in settings.valid_api_keys:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing API Key. Pass it in the X-API-Key header.",
        )
    return api_key