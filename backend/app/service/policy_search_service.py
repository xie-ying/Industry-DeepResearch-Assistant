"""基于 Milvus 的政策文档搜索服务"""
import os
from typing import List, Dict, Any, Optional
from pymilvus import (
    connections,
    Collection,
    CollectionSchema,
    FieldSchema,
    DataType,
    utility,
)
from service.embedding_service import generate_embedding


class PolicySearchService:
    """政策文档搜索服务类 - 基于 Milvus"""

    def __init__(self, collection_name: str = "policy_documents"):
        """初始化 Milvus 连接"""
        self.host = os.getenv("MILVUS_HOST", "localhost")
        self.port = int(os.getenv("MILVUS_PORT", "19530"))
        self.collection_name = collection_name
        self.vector_dim = 1024
        self._connect()

    def _connect(self):
        """连接到 Milvus"""
        try:
            connections.connect(
                alias="default",
                host=self.host,
                port=self.port,
            )
            print(f"PolicySearchService 已连接到 Milvus: {self.host}:{self.port}")
        except Exception as e:
            print(f"连接 Milvus 失败: {e}")

    def _ensure_collection(self) -> Optional[Collection]:
        """确保集合存在"""
        try:
            if utility.has_collection(self.collection_name):
                collection = Collection(self.collection_name)
                collection.load()
                return collection

            # 创建集合
            fields = [
                FieldSchema(name="id", dtype=DataType.VARCHAR, is_primary=True, max_length=64),
                FieldSchema(name="title", dtype=DataType.VARCHAR, max_length=1024),
                FieldSchema(name="website", dtype=DataType.VARCHAR, max_length=256),
                FieldSchema(name="entry_url", dtype=DataType.VARCHAR, max_length=1024),
                FieldSchema(name="detail_url", dtype=DataType.VARCHAR, max_length=1024),
                FieldSchema(name="date", dtype=DataType.VARCHAR, max_length=64),
                FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=65535),
                FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=self.vector_dim),
            ]

            schema = CollectionSchema(fields=fields, description="Policy documents")
            collection = Collection(name=self.collection_name, schema=schema)

            # 创建索引
            index_params = {
                "metric_type": "COSINE",
                "index_type": "IVF_FLAT",
                "params": {"nlist": 128},
            }
            collection.create_index(field_name="vector", index_params=index_params)
            collection.load()

            print(f"集合 {self.collection_name} 创建成功")
            return collection

        except Exception as e:
            print(f"创建集合失败: {e}")
            return None

    def check_connection(self) -> Dict[str, Any]:
        """检查连接状态"""
        try:
            connected = connections.has_connection("default")
            if connected:
                return {
                    "success": True,
                    "status": "green",
                    "message": "Milvus 连接正常"
                }
            return {
                "success": False,
                "status": "red",
                "message": "Milvus 未连接"
            }
        except Exception as e:
            return {
                "success": False,
                "status": "error",
                "message": f"检查连接出错: {str(e)}"
            }

    def get_index_info(self) -> Dict[str, Any]:
        """获取索引信息"""
        try:
            if not utility.has_collection(self.collection_name):
                return {
                    "success": False,
                    "message": f"集合 '{self.collection_name}' 不存在"
                }

            collection = Collection(self.collection_name)
            return {
                "success": True,
                "index_name": self.collection_name,
                "doc_count": collection.num_entities,
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"获取索引信息出错: {str(e)}"
            }

    def list_indices(self) -> Dict[str, Any]:
        """列出所有集合"""
        try:
            collections = utility.list_collections()
            return {
                "success": True,
                "indices": [{"index": c} for c in collections]
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"获取集合列表出错: {str(e)}"
            }

    def get_document(self, doc_id: str) -> Dict[str, Any]:
        """获取指定文档"""
        try:
            collection = self._ensure_collection()
            if not collection:
                return {"success": False, "message": "集合不存在"}

            results = collection.query(
                expr=f'id == "{doc_id}"',
                output_fields=["id", "title", "website", "entry_url", "detail_url", "date", "content"]
            )

            if results:
                return {
                    "success": True,
                    "document": results[0],
                    "id": doc_id
                }
            return {
                "success": False,
                "message": "文档不存在"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"获取文档出错: {str(e)}"
            }

    def hybrid_search(self, query: str, top_n: int = 3) -> Dict[str, Any]:
        """向量搜索（Milvus 不支持关键词搜索，使用纯向量搜索）"""
        return self.vector_search(query, top_n)

    def keyword_search(self, query: str, top_n: int = 10) -> Dict[str, Any]:
        """关键词搜索（Milvus 不直接支持，降级为向量搜索）"""
        return self.vector_search(query, top_n)

    def vector_search(self, query: str, top_n: int = 10) -> Dict[str, Any]:
        """向量搜索"""
        try:
            collection = self._ensure_collection()
            if not collection:
                return {"success": False, "message": "集合不存在或为空"}

            # 生成查询向量
            query_vectors = generate_embedding([query])
            if not query_vectors:
                return {
                    "success": False,
                    "message": "无法生成查询向量"
                }

            query_vector = query_vectors[0]

            # 搜索参数
            search_params = {
                "metric_type": "COSINE",
                "params": {"nprobe": 10},
            }

            results = collection.search(
                data=[query_vector],
                anns_field="vector",
                param=search_params,
                limit=top_n,
                output_fields=["id", "title", "website", "entry_url", "detail_url", "date", "content"],
            )

            # 格式化结果
            search_results = []
            for hits in results:
                for hit in hits:
                    content = hit.entity.get("content", "")
                    item = {
                        "id": hit.entity.get("id"),
                        "title": hit.entity.get("title", ""),
                        "website": hit.entity.get("website", ""),
                        "entry_url": hit.entity.get("entry_url", ""),
                        "detail_url": hit.entity.get("detail_url", ""),
                        "date": hit.entity.get("date", ""),
                        "content": content,
                        "content_preview": content[:300] + "..." if len(content) > 300 else content,
                        "score": hit.score,
                    }
                    search_results.append(item)

            return {
                "success": True,
                "query": query,
                "method": "vector",
                "total": len(search_results),
                "results": search_results,
            }

        except Exception as e:
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "message": f"搜索出错: {str(e)}"
            }

    def search(self, query: str, method: str = "hybrid", top_n: int = 10) -> Dict[str, Any]:
        """统一搜索接口"""
        if method == "hybrid":
            return self.hybrid_search(query, top_n)
        elif method == "keyword":
            return self.keyword_search(query, top_n)
        elif method == "vector":
            return self.vector_search(query, top_n)
        else:
            return {
                "success": False,
                "message": f"不支持的搜索方法: {method}"
            }

    def insert_document(self, doc: Dict[str, Any]) -> bool:
        """插入单个文档"""
        try:
            collection = self._ensure_collection()
            if not collection:
                return False

            # 生成向量
            content = doc.get("content", "")
            vectors = generate_embedding([content])
            if not vectors:
                print("生成向量失败")
                return False

            # 插入数据
            data = [
                [doc.get("id", "")],
                [doc.get("title", "")[:1024]],
                [doc.get("website", "")[:256]],
                [doc.get("entry_url", "")[:1024]],
                [doc.get("detail_url", "")[:1024]],
                [doc.get("date", "")[:64]],
                [content[:65535]],
                [vectors[0]],
            ]

            collection.insert(data)
            collection.flush()
            return True

        except Exception as e:
            print(f"插入文档失败: {e}")
            return False


if __name__ == "__main__":
    service = PolicySearchService()
    print(service.check_connection())
    print(service.get_index_info())
