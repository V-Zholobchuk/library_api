import time
import os
from fastapi import Request, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from redis.asyncio import Redis
from security import SECRET_KEY, ALGORITHM

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
redis_client = Redis.from_url(REDIS_URL, decode_responses=True)

oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)

async def get_current_user_optional(token: str = Depends(oauth2_scheme_optional)):
    if not token:
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None

RATE_LIMITS = {
    "authenticated": (10, 60),
    "anonymous": (2, 60)
}

async def rate_limit(request: Request, user_id: str | None = Depends(get_current_user_optional)):
    identity = user_id or request.client.host
    limit_type = "authenticated" if user_id else "anonymous"
    limit, period = RATE_LIMITS[limit_type]

    now = time.time()
    window_start = now - period
    key = f"rate_limit_{identity}"

    await redis_client.zremrangebyscore(key, min=0, max=window_start)
    request_count = await redis_client.zcard(key)
    
    if request_count >= limit:
        raise HTTPException(status_code=429, detail="Too many requests")
        
    await redis_client.zadd(key, {str(now): now})
    await redis_client.expire(key, period)
