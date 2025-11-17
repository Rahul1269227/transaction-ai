"""
Authentication and Rate Limiting Module
Provides API key authentication and rate limiting for production security
"""

import hashlib
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from functools import wraps
import logging

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader
from redis import Redis
from redis.exceptions import RedisError

logger = logging.getLogger(__name__)

# API Key Header
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


class RateLimiter:
    """Rate limiting using Redis"""
    
    def __init__(self, redis_client: Optional[Redis] = None):
        self.redis = redis_client
    
    def is_allowed(
        self,
        identifier: str,
        limit: int = 100,
        window: int = 60,
        key_prefix: str = "rate_limit"
    ) -> tuple[bool, Dict]:
        """
        Check if request is within rate limit
        
        Args:
            identifier: Unique identifier (API key, IP, user ID)
            limit: Maximum requests per window
            window: Time window in seconds
            key_prefix: Redis key prefix
            
        Returns:
            (is_allowed, rate_limit_info)
        """
        if not self.redis:
            # No Redis = no rate limiting (development mode)
            return True, {
                "limit": limit,
                "remaining": limit,
                "reset": int(time.time()) + window
            }
        
        key = f"{key_prefix}:{identifier}"
        now = time.time()
        
        try:
            # Use sliding window log algorithm
            pipe = self.redis.pipeline()
            pipe.zremrangebyscore(key, 0, now - window)  # Remove old entries
            pipe.zcard(key)  # Count current entries
            pipe.zadd(key, {str(now): now})  # Add current request
            pipe.expire(key, window)  # Set expiry
            results = pipe.execute()
            
            current_count = results[1]
            remaining = max(0, limit - current_count - 1)
            reset_time = int(now) + window
            
            is_allowed = current_count < limit
            
            return is_allowed, {
                "limit": limit,
                "remaining": remaining,
                "reset": reset_time
            }
        except RedisError as e:
            logger.error(f"Rate limit check failed: {e}")
            # Fail open - allow request if Redis is down
            return True, {
                "limit": limit,
                "remaining": limit,
                "reset": int(time.time()) + window
            }


class APIKeyAuth:
    """API Key Authentication"""
    
    def __init__(self, redis_client: Optional[Redis] = None):
        self.redis = redis_client
        self.api_keys: Dict[str, Dict] = {}  # In-memory fallback
        
        # Default API keys for development (should be in DB/Redis in production)
        self.api_keys = {
            "dev-key-123": {
                "name": "Development Key",
                "organization_id": "dev-org",
                "user_id": "dev-user",
                "permissions": ["read", "write"],
                "rate_limit": 1000,
                "rate_window": 60,
                "created_at": datetime.now().isoformat()
            }
        }
    
    def validate_api_key(self, api_key: Optional[str]) -> Optional[Dict]:
        """
        Validate API key
        
        Args:
            api_key: API key string
            
        Returns:
            API key info dict or None if invalid
        """
        if not api_key:
            return None
        
        # Check Redis first (production)
        if self.redis:
            try:
                key_data = self.redis.get(f"api_key:{api_key}")
                if key_data:
                    import json
                    return json.loads(key_data)
            except RedisError as e:
                logger.error(f"Redis lookup failed: {e}")
        
        # Fallback to in-memory
        return self.api_keys.get(api_key)
    
    def create_api_key(
        self,
        name: str,
        organization_id: str,
        user_id: str,
        permissions: List[str] = None,
        rate_limit: int = 100
    ) -> str:
        """
        Create a new API key
        
        Args:
            name: Key name/description
            organization_id: Organization ID
            user_id: User ID
            permissions: List of permissions
            rate_limit: Rate limit per minute
            
        Returns:
            Generated API key
        """
        # Generate secure API key
        import secrets
        api_key = f"txn_{secrets.token_urlsafe(32)}"
        
        key_data = {
            "name": name,
            "organization_id": organization_id,
            "user_id": user_id,
            "permissions": permissions or ["read", "write"],
            "rate_limit": rate_limit,
            "rate_window": 60,
            "created_at": datetime.now().isoformat()
        }
        
        # Store in Redis if available
        if self.redis:
            try:
                import json
                self.redis.setex(
                    f"api_key:{api_key}",
                    86400 * 365,  # 1 year expiry
                    json.dumps(key_data)
                )
            except RedisError as e:
                logger.error(f"Failed to store API key in Redis: {e}")
        
        # Also store in memory
        self.api_keys[api_key] = key_data
        
        return api_key


# Global instances
rate_limiter: Optional[RateLimiter] = None
api_auth: Optional[APIKeyAuth] = None


def init_auth(redis_client: Optional[Redis] = None):
    """Initialize authentication and rate limiting"""
    global rate_limiter, api_auth
    rate_limiter = RateLimiter(redis_client)
    api_auth = APIKeyAuth(redis_client)
    logger.info("Authentication and rate limiting initialized")


def require_auth(api_key: Optional[str] = Security(api_key_header)) -> Dict:
    """
    Dependency for requiring API key authentication
    
    Usage:
        @app.get("/endpoint")
        def endpoint(user: Dict = Depends(require_auth)):
            ...
    """
    if not api_auth:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication not initialized"
        )
    
    key_info = api_auth.validate_api_key(api_key)
    if not key_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    return key_info


def check_rate_limit(identifier: str, limit: int = 100, window: int = 60):
    """
    Dependency for rate limiting
    
    Usage:
        @app.get("/endpoint")
        def endpoint(rate_limit_info: Dict = Depends(check_rate_limit)):
            ...
    """
    if not rate_limiter:
        return {
            "limit": limit,
            "remaining": limit,
            "reset": int(time.time()) + window
        }
    
    is_allowed, info = rate_limiter.is_allowed(identifier, limit, window)
    
    if not is_allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded",
            headers={
                "X-RateLimit-Limit": str(info["limit"]),
                "X-RateLimit-Remaining": str(info["remaining"]),
                "X-RateLimit-Reset": str(info["reset"])
            }
        )
    
    return info
