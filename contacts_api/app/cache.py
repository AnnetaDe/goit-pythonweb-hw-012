import json
import os
import redis.asyncio as redis

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
ENV = os.getenv("ENV", "test")

r = redis.from_url(REDIS_URL, decode_responses=True)


def _user_key(user_id: int) -> str:
    return f"{ENV}:user:{user_id}"



async def get_cached_user(user_id: int):
    raw = await r.get(_user_key(user_id))
    return json.loads(raw) if raw else None

async def set_cached_user(user_id: int, payload: dict, ttl: int = 300):
    await r.set(_user_key(user_id), json.dumps(payload), ex=ttl)

async def del_cached_user(user_id: int):
    await r.delete(_user_key(user_id))
