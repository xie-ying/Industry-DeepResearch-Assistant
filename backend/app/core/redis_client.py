"""Redis 客户端"""
import os
import json
from typing import Optional, Any
import redis

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "") or None

# 创建 Redis 连接池
redis_pool = redis.ConnectionPool(
    host=REDIS_HOST,
    port=REDIS_PORT,
    password=REDIS_PASSWORD,
    decode_responses=True,
    max_connections=20
)


def get_redis_client() -> redis.Redis:
    """获取 Redis 客户端"""
    return redis.Redis(connection_pool=redis_pool)


class RedisCache:
    """Redis 缓存工具类"""

    def __init__(self):
        self.client = get_redis_client()

    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        try:
            value = self.client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            print(f"Redis get error: {e}")
            return None

    def set(self, key: str, value: Any, expire: int = 3600) -> bool:
        """设置缓存，默认过期时间 1 小时"""
        try:
            self.client.setex(key, expire, json.dumps(value, ensure_ascii=False))
            return True
        except Exception as e:
            print(f"Redis set error: {e}")
            return False

    def delete(self, key: str) -> bool:
        """删除缓存"""
        try:
            self.client.delete(key)
            return True
        except Exception as e:
            print(f"Redis delete error: {e}")
            return False

    def exists(self, key: str) -> bool:
        """检查 key 是否存在"""
        try:
            return bool(self.client.exists(key))
        except Exception as e:
            print(f"Redis exists error: {e}")
            return False

    def set_session(self, session_id: str, data: dict, expire: int = 86400) -> bool:
        """设置会话数据，默认过期时间 24 小时"""
        key = f"session:{session_id}"
        return self.set(key, data, expire)

    def get_session(self, session_id: str) -> Optional[dict]:
        """获取会话数据"""
        key = f"session:{session_id}"
        return self.get(key)

    def delete_session(self, session_id: str) -> bool:
        """删除会话"""
        key = f"session:{session_id}"
        return self.delete(key)

    def add_to_list(self, key: str, value: Any, max_length: int = 100) -> bool:
        """添加到列表（用于短期记忆）"""
        try:
            self.client.lpush(key, json.dumps(value, ensure_ascii=False))
            self.client.ltrim(key, 0, max_length - 1)
            return True
        except Exception as e:
            print(f"Redis add_to_list error: {e}")
            return False

    def get_list(self, key: str, start: int = 0, end: int = -1) -> list:
        """获取列表"""
        try:
            items = self.client.lrange(key, start, end)
            return [json.loads(item) for item in items]
        except Exception as e:
            print(f"Redis get_list error: {e}")
            return []


# 全局缓存实例
cache = RedisCache()
