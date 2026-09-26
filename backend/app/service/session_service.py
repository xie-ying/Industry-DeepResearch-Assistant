import json
import os
import time
import uuid
from typing import List, Dict, Any, Optional
import redis
import tiktoken

class SessionService:
    """会话服务，用于管理聊天历史记录"""
    
    def __init__(self):
        """初始化会话服务"""
        redis_host = os.environ.get("REDIS_HOST", "redis")
        redis_port = int(os.environ.get("REDIS_PORT", 6379))
        redis_password = os.environ.get("REDIS_PASSWORD", None)
        self.redis_client = redis.Redis(
            host=redis_host,
            port=redis_port,
            password=redis_password,
            decode_responses=True
        )
        self.token_limit = 5000
        self.max_messages = 20  # 最大保存的消息数量
        self.encoding = tiktoken.get_encoding("cl100k_base")  # OpenAI通用编码
    
    def create_session(self) -> Dict[str, Any]:
        """创建新的会话
        
        Returns:
            包含会话信息的字典
        """
        session_id = str(uuid.uuid4())
        timestamp = int(time.time())
        
        session_data = {
            "session_id": session_id,
            "created_at": timestamp,
            "updated_at": timestamp,
            "message_count": 0
        }
        
        # 存储会话信息到Redis
        self.redis_client.hset(f"session:{session_id}", mapping=session_data)
        
        return session_data
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话信息
        
        Args:
            session_id: 会话ID
            
        Returns:
            会话信息，如果不存在则返回None
        """
        session_data = self.redis_client.hgetall(f"session:{session_id}")
        if not session_data:
            return None
        return session_data
    
    def add_message(self, session_id: str, role: str, content: str) -> bool:
        """向会话添加消息
        
        Args:
            session_id: 会话ID
            role: 消息角色（user或assistant）
            content: 消息内容
            
        Returns:
            是否成功添加
        """
        # 检查会话是否存在
        session = self.get_session(session_id)
        if not session:
            return False
        
        message_id = str(uuid.uuid4())
        timestamp = int(time.time())
        
        message_data = {
            "message_id": message_id,
            "session_id": session_id,
            "role": role,
            "content": content,
            "created_at": timestamp
        }
        
        # 存储消息到Redis
        message_key = f"message:{session_id}:{message_id}"
        self.redis_client.hset(message_key, mapping=message_data)
        
        # 添加到会话的消息列表（按时间排序）
        self.redis_client.zadd(f"session:{session_id}:messages", {message_id: timestamp})
        
        # 更新会话信息
        message_count = int(session.get("message_count", 0)) + 1
        self.redis_client.hset(f"session:{session_id}", "message_count", message_count)
        self.redis_client.hset(f"session:{session_id}", "updated_at", timestamp)
        
        # 如果消息数量超过限制，删除最早的消息
        if message_count > self.max_messages:
            oldest_message_ids = self.redis_client.zrange(f"session:{session_id}:messages", 0, 0)
            if oldest_message_ids:
                oldest_id = oldest_message_ids[0]
                # 删除消息
                self.redis_client.delete(f"message:{session_id}:{oldest_id}")
                # 从会话消息列表中移除
                self.redis_client.zrem(f"session:{session_id}:messages", oldest_id)
                # 更新计数
                self.redis_client.hincrby(f"session:{session_id}", "message_count", -1)
        
        return True
    
    def get_history(self, session_id: str) -> List[Dict[str, Any]]:
        """获取会话历史消息
        
        Args:
            session_id: 会话ID
            
        Returns:
            历史消息列表
        """
        # 获取会话的所有消息ID（按时间排序）
        message_ids = self.redis_client.zrange(f"session:{session_id}:messages", 0, -1)
        
        # 获取所有消息
        messages = []
        for msg_id in message_ids:
            msg_data = self.redis_client.hgetall(f"message:{session_id}:{msg_id}")
            if msg_data:
                messages.append(msg_data)
        
        return messages
    
    def get_messages_for_prompt(self, session_id: str) -> List[Dict[str, str]]:
        """获取格式化的历史消息，适用于提示词
        
        Args:
            session_id: 会话ID
            
        Returns:
            格式化的消息列表，优先保留最近的消息
        """
        history = self.get_history(session_id)
        formatted_messages = []
        total_tokens = 0
        
        # 从最近的消息开始处理（倒序）
        history.reverse()
        
        for msg in history:
            # 过滤出需要的字段
            formatted_msg = {
                "role": msg["role"],
                "content": msg["content"]
            }
            
            # 计算tokens
            msg_tokens = len(self.encoding.encode(msg["content"]))
            
            # 如果添加此消息会超出token限制，则跳出循环
            if total_tokens + msg_tokens > self.token_limit:
                break
                
            # 添加消息并累计tokens（添加到列表前面，保持时间顺序）
            formatted_messages.insert(0, formatted_msg)
            total_tokens += msg_tokens
        
        # 此时消息已经按时间顺序排列（最早的在前面），无需再次反转
        return formatted_messages 