"""
Redis Cache Connection & Utilities
"""

import os
import redis
from typing import Optional, Any
import json

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Global Redis client
redis_client: Optional[redis.Redis] = None

def connect_redis():
    """Kết nối Redis"""
    global redis_client
    try:
        redis_client = redis.from_url(REDIS_URL, decode_responses=True)
        redis_client.ping()
        print("✅ Connected to Redis successfully")
    except Exception as e:
        print(f"⚠️  Redis not available: {e}")

def disconnect_redis():
    """Ngắt kết nối Redis"""
    global redis_client
    if redis_client:
        redis_client.close()
        print("✅ Redis disconnected")

def get_redis() -> redis.Redis:
    """Get Redis client"""
    global redis_client
    if not redis_client:
        connect_redis()
    return redis_client

# Cache operations
def cache_get(key: str) -> Optional[Any]:
    """Get from cache"""
    try:
        if redis_client is None:
            return None
        value = redis_client.get(key)
        if value:
            try:
                return json.loads(value)
            except:
                return value
        return None
    except:
        return None

def cache_set(key: str, value: Any, ttl: int = 3600):
    """Set cache with TTL (seconds)"""
    try:
        if redis_client is None:
            return
        if isinstance(value, dict) or isinstance(value, list):
            value = json.dumps(value)
        redis_client.setex(key, ttl, value)
    except:
        pass

def cache_delete(key: str):
    """Delete from cache"""
    try:
        if redis_client is None:
            return
        redis_client.delete(key)
    except:
        pass

def cache_clear():
    """Clear all cache"""
    try:
        if redis_client is None:
            return
        redis_client.flushdb()
    except:
        pass

# Schedule cache helpers
def cache_schedule_today(user_id: str, schedules: list, ttl: int = 3600):
    """Cache today's schedule"""
    cache_set(f"schedule:user:{user_id}:today", schedules, ttl)

def get_schedule_today(user_id: str) -> Optional[list]:
    """Get today's schedule from cache"""
    return cache_get(f"schedule:user:{user_id}:today")

# AI parse result cache
def cache_ai_parse(request_id: str, result: dict, ttl: int = 604800):  # 7 days
    """Cache AI parse result"""
    cache_set(f"cache:ai:parse:{request_id}", result, ttl)

def get_ai_parse(request_id: str) -> Optional[dict]:
    """Get AI parse result from cache"""
    return cache_get(f"cache:ai:parse:{request_id}")
