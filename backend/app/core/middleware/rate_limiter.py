from fastapi import Request, HTTPException
from redis import Redis
from app.core.config import settings
import time

class RateLimiter:
    def __init__(self, redis_client: Redis):
        self.redis = redis_client
        self.rate_limit = 100  # requests per minute
        self.window = 60  # seconds
    
    async def check_rate_limit(self, request: Request):
        if settings.ENVIRONMENT == "development":
            return
            
        client_ip = request.client.host
        key = f"rate_limit:{client_ip}"
        
        # Get current count for this IP
        current = self.redis.get(key)
        if current is None:
            # First request from this IP
            pipeline = self.redis.pipeline()
            pipeline.incr(key)
            pipeline.expire(key, self.window)
            pipeline.execute()
        else:
            count = int(current)
            if count >= self.rate_limit:
                raise HTTPException(
                    status_code=429,
                    detail="Too many requests"
                )
            self.redis.incr(key)
            
rate_limiter = None

def setup_rate_limiter():
    global rate_limiter
    try:
        redis_client = Redis.from_url(settings.REDIS_URL, decode_responses=True)
        rate_limiter = RateLimiter(redis_client)
    except Exception as e:
        from loguru import logger
        logger.warning(f"Failed to initialize rate limiter: {e}")
        rate_limiter = None

async def rate_limit_middleware(request: Request, call_next):
    if rate_limiter:
        await rate_limiter.check_rate_limit(request)
    response = await call_next(request)
    return response