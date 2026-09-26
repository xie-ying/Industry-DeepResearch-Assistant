"""
长期记忆服务 - Long-term Memory Service

功能：
1. 对话历史压缩和总结
2. 记忆向量化存储到 Milvus
3. 记忆检索和召回
4. 用户偏好学习
"""

import os
import json
import uuid
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from openai import OpenAI

from dotenv import load_dotenv
load_dotenv()

from models.chat import ChatSession, ChatMessage, LongTermMemory
from service.embedding_service import generate_embedding
from service.milvus_service import get_milvus_service, MilvusService

# 记忆触发阈值
MEMORY_TOKEN_THRESHOLD = 10000  # 超过此 token 数触发记忆压缩
MEMORY_COLLECTION_NAME = "long_term_memories"  # Milvus 集合名称


class MemoryService:
    """长期记忆服务"""

    def __init__(self):
        self.api_key = os.getenv("DASHSCOPE_API_KEY")
        self.base_url = os.getenv("DASHSCOPE_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
        self.model = os.getenv("DASHSCOPE_MODEL", "qwen-plus")
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        self._milvus: Optional[MilvusService] = None

    @property
    def milvus(self) -> MilvusService:
        """懒加载 Milvus 服务"""
        if self._milvus is None:
            self._milvus = get_milvus_service()
            self._ensure_memory_collection()
        return self._milvus

    def _ensure_memory_collection(self):
        """确保记忆集合存在（使用专门的 schema）"""
        from pymilvus import connections, Collection, CollectionSchema, FieldSchema, DataType, utility

        collection_name = MEMORY_COLLECTION_NAME

        if utility.has_collection(collection_name):
            return

        # 定义记忆专用字段
        fields = [
            FieldSchema(name="id", dtype=DataType.VARCHAR, is_primary=True, max_length=64),
            FieldSchema(name="user_id", dtype=DataType.VARCHAR, max_length=64),
            FieldSchema(name="session_id", dtype=DataType.VARCHAR, max_length=64),
            FieldSchema(name="memory_type", dtype=DataType.VARCHAR, max_length=32),  # summary/insight/preference
            FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=65535),
            FieldSchema(name="metadata", dtype=DataType.VARCHAR, max_length=8192),  # JSON 格式的额外信息
            FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=1024),
        ]

        schema = CollectionSchema(fields=fields, description="Long-term memories")
        collection = Collection(name=collection_name, schema=schema)

        # 创建索引
        index_params = {
            "metric_type": "COSINE",
            "index_type": "IVF_FLAT",
            "params": {"nlist": 128},
        }
        collection.create_index(field_name="vector", index_params=index_params)
        collection.load()

        print(f"记忆集合 {collection_name} 创建成功")

    def estimate_tokens(self, text: str) -> int:
        """估算文本的 token 数量（简单估算：中文约2字符/token，英文约4字符/token）"""
        # 简单估算：假设平均每3个字符为1个 token
        return len(text) // 3

    def should_compress(self, messages: List[ChatMessage]) -> bool:
        """判断是否需要压缩记忆"""
        total_tokens = sum(self.estimate_tokens(msg.content) for msg in messages)
        return total_tokens > MEMORY_TOKEN_THRESHOLD

    def summarize_conversation(self, messages: List[ChatMessage]) -> Dict[str, Any]:
        """
        使用 LLM 总结对话并提取关键洞察

        Returns:
            {
                "summary": "对话摘要",
                "key_insights": ["洞察1", "洞察2", ...],
                "user_preferences": {"preference_type": "value", ...},
                "topics": ["主题1", "主题2", ...]
            }
        """
        # 构建对话文本
        conversation_text = "\n".join([
            f"{'用户' if msg.role == 'user' else '助手'}: {msg.content}"
            for msg in messages
        ])

        # 限制长度避免超过上下文
        if len(conversation_text) > 30000:
            conversation_text = conversation_text[:30000] + "\n...(对话过长，已截断)"

        prompt = f"""请分析以下对话，并按JSON格式输出总结信息：

对话内容：
{conversation_text}

请输出以下格式的JSON（不要包含```json标记）：
{{
    "summary": "用2-3句话总结这段对话的主要内容和结论",
    "key_insights": ["从对话中提取的3-5个关键信息或知识点"],
    "user_preferences": {{
        "interests": ["用户感兴趣的领域"],
        "communication_style": "用户偏好的沟通风格（如：详细/简洁/专业/通俗）",
        "focus_areas": ["用户关注的重点领域"]
    }},
    "topics": ["对话涉及的主题标签"]
}}"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个专业的对话分析助手，擅长总结对话内容并提取关键信息。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
            )

            result_text = response.choices[0].message.content.strip()

            # 清理可能的 markdown 标记
            if result_text.startswith("```json"):
                result_text = result_text[7:]
            if result_text.startswith("```"):
                result_text = result_text[3:]
            if result_text.endswith("```"):
                result_text = result_text[:-3]

            return json.loads(result_text.strip())

        except Exception as e:
            print(f"总结对话失败: {e}")
            # 返回默认结构
            return {
                "summary": f"对话包含 {len(messages)} 条消息",
                "key_insights": [],
                "user_preferences": {},
                "topics": []
            }

    def create_memory(
        self,
        db: Session,
        user_id: str,
        session_id: str,
        messages: List[ChatMessage]
    ) -> Optional[LongTermMemory]:
        """
        创建长期记忆

        Args:
            db: 数据库会话
            user_id: 用户ID
            session_id: 会话ID
            messages: 消息列表

        Returns:
            创建的记忆对象
        """
        if not messages:
            return None

        # 总结对话
        summary_data = self.summarize_conversation(messages)

        # 计算 token 数
        total_tokens = sum(self.estimate_tokens(msg.content) for msg in messages)

        # 创建数据库记录
        memory = LongTermMemory(
            user_id=user_id,
            session_id=session_id,
            summary=summary_data.get("summary", ""),
            key_insights=summary_data,
            token_count=total_tokens,
        )

        db.add(memory)
        db.commit()
        db.refresh(memory)

        # 向量化并存储到 Milvus
        milvus_ids = self._store_memory_vectors(
            memory_id=str(memory.id),
            user_id=user_id,
            session_id=session_id,
            summary_data=summary_data
        )

        # 更新 Milvus IDs
        memory.milvus_ids = milvus_ids
        db.commit()

        print(f"创建长期记忆成功: {memory.id}")
        return memory

    def _store_memory_vectors(
        self,
        memory_id: str,
        user_id: str,
        session_id: str,
        summary_data: Dict[str, Any]
    ) -> List[str]:
        """将记忆内容向量化并存储到 Milvus"""
        from pymilvus import Collection

        milvus_ids = []
        documents_to_insert = []

        # 1. 存储摘要向量
        summary = summary_data.get("summary", "")
        if summary:
            summary_vector = generate_embedding(summary)
            if summary_vector:
                doc_id = f"{memory_id}_summary"
                documents_to_insert.append({
                    "id": doc_id,
                    "user_id": user_id,
                    "session_id": session_id,
                    "memory_type": "summary",
                    "content": summary,
                    "metadata": json.dumps({"memory_id": memory_id}),
                    "vector": summary_vector
                })
                milvus_ids.append(doc_id)

        # 2. 存储关键洞察向量
        insights = summary_data.get("key_insights", [])
        for i, insight in enumerate(insights):
            if insight:
                insight_vector = generate_embedding(insight)
                if insight_vector:
                    doc_id = f"{memory_id}_insight_{i}"
                    documents_to_insert.append({
                        "id": doc_id,
                        "user_id": user_id,
                        "session_id": session_id,
                        "memory_type": "insight",
                        "content": insight,
                        "metadata": json.dumps({"memory_id": memory_id, "index": i}),
                        "vector": insight_vector
                    })
                    milvus_ids.append(doc_id)

        # 3. 存储主题向量
        topics = summary_data.get("topics", [])
        if topics:
            topics_text = "用户关注的主题: " + ", ".join(topics)
            topics_vector = generate_embedding(topics_text)
            if topics_vector:
                doc_id = f"{memory_id}_topics"
                documents_to_insert.append({
                    "id": doc_id,
                    "user_id": user_id,
                    "session_id": session_id,
                    "memory_type": "topics",
                    "content": topics_text,
                    "metadata": json.dumps({"memory_id": memory_id, "topics": topics}),
                    "vector": topics_vector
                })
                milvus_ids.append(doc_id)

        # 批量插入 Milvus
        if documents_to_insert:
            try:
                collection = Collection(MEMORY_COLLECTION_NAME)
                collection.load()

                ids = [doc["id"] for doc in documents_to_insert]
                user_ids = [doc["user_id"] for doc in documents_to_insert]
                session_ids = [doc["session_id"] for doc in documents_to_insert]
                memory_types = [doc["memory_type"] for doc in documents_to_insert]
                contents = [doc["content"][:65535] for doc in documents_to_insert]
                metadatas = [doc["metadata"][:8192] for doc in documents_to_insert]
                vectors = [doc["vector"] for doc in documents_to_insert]

                data = [ids, user_ids, session_ids, memory_types, contents, metadatas, vectors]
                collection.insert(data)
                collection.flush()

                print(f"成功存储 {len(documents_to_insert)} 条记忆向量")
            except Exception as e:
                print(f"存储记忆向量失败: {e}")

        return milvus_ids

    def retrieve_memories(
        self,
        user_id: str,
        query: str,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        检索与查询相关的记忆

        Args:
            user_id: 用户ID
            query: 查询文本
            top_k: 返回结果数量

        Returns:
            相关记忆列表
        """
        from pymilvus import Collection, utility

        if not utility.has_collection(MEMORY_COLLECTION_NAME):
            return []

        # 生成查询向量
        query_vector = generate_embedding(query)
        if not query_vector:
            return []

        try:
            collection = Collection(MEMORY_COLLECTION_NAME)
            collection.load()

            # 按用户过滤
            expr = f'user_id == "{user_id}"'

            search_params = {
                "metric_type": "COSINE",
                "params": {"nprobe": 10},
            }

            results = collection.search(
                data=[query_vector],
                anns_field="vector",
                param=search_params,
                limit=top_k,
                expr=expr,
                output_fields=["id", "session_id", "memory_type", "content", "metadata"],
            )

            formatted_results = []
            for hits in results:
                for hit in hits:
                    formatted_results.append({
                        "id": hit.entity.get("id"),
                        "session_id": hit.entity.get("session_id"),
                        "memory_type": hit.entity.get("memory_type"),
                        "content": hit.entity.get("content"),
                        "metadata": hit.entity.get("metadata"),
                        "score": hit.score,
                    })

            return formatted_results

        except Exception as e:
            print(f"检索记忆失败: {e}")
            return []

    def get_user_memories(
        self,
        db: Session,
        user_id: str,
        limit: int = 10
    ) -> List[LongTermMemory]:
        """获取用户的所有长期记忆"""
        return db.query(LongTermMemory).filter(
            LongTermMemory.user_id == user_id
        ).order_by(LongTermMemory.created_at.desc()).limit(limit).all()

    def delete_memory(
        self,
        db: Session,
        memory_id: str,
        user_id: str
    ) -> bool:
        """删除指定的长期记忆"""
        from pymilvus import Collection, utility

        memory = db.query(LongTermMemory).filter(
            LongTermMemory.id == memory_id,
            LongTermMemory.user_id == user_id
        ).first()

        if not memory:
            return False

        # 删除 Milvus 中的向量
        if memory.milvus_ids and utility.has_collection(MEMORY_COLLECTION_NAME):
            try:
                collection = Collection(MEMORY_COLLECTION_NAME)
                for milvus_id in memory.milvus_ids:
                    expr = f'id == "{milvus_id}"'
                    collection.delete(expr)
            except Exception as e:
                print(f"删除 Milvus 记忆失败: {e}")

        # 删除数据库记录
        db.delete(memory)
        db.commit()

        return True

    def build_memory_context(
        self,
        user_id: str,
        current_query: str,
        max_memories: int = 3
    ) -> str:
        """
        构建记忆上下文，用于增强当前对话

        Args:
            user_id: 用户ID
            current_query: 当前查询
            max_memories: 最大记忆数量

        Returns:
            记忆上下文文本
        """
        memories = self.retrieve_memories(user_id, current_query, top_k=max_memories)

        if not memories:
            return ""

        # 按相关度排序并去重
        seen_contents = set()
        unique_memories = []
        for mem in memories:
            content = mem.get("content", "")
            if content not in seen_contents:
                seen_contents.add(content)
                unique_memories.append(mem)

        if not unique_memories:
            return ""

        # 构建上下文
        context_parts = ["[相关历史记忆]"]
        for mem in unique_memories:
            memory_type = mem.get("memory_type", "unknown")
            content = mem.get("content", "")

            if memory_type == "summary":
                context_parts.append(f"- 历史对话摘要: {content}")
            elif memory_type == "insight":
                context_parts.append(f"- 相关知识点: {content}")
            elif memory_type == "topics":
                context_parts.append(f"- {content}")

        context_parts.append("")  # 空行分隔

        return "\n".join(context_parts)


# 单例实例
_memory_service: Optional[MemoryService] = None


def get_memory_service() -> MemoryService:
    """获取记忆服务单例"""
    global _memory_service
    if _memory_service is None:
        _memory_service = MemoryService()
    return _memory_service
