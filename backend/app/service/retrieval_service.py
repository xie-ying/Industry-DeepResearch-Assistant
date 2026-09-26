"""
知识库检索服务 - 基于 Milvus

功能：
1. retrieve_content - 从指定集合检索内容
2. retrieve_from_knowledge_base - 从知识库检索内容
"""

from typing import List, Dict, Any, Optional
from service.milvus_service import get_milvus_service
from service.embedding_service import generate_embedding


def retrieve_content(
    indexNames: str,
    question: str,
    top_k: int = 5,
    kb_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    检索相关内容

    Args:
        indexNames: 集合名称（知识库索引）
        question: 查询问题
        top_k: 返回结果数量
        kb_id: 知识库ID（可选过滤）

    Returns:
        检索结果列表
    """
    try:
        # 1. 生成查询向量
        query_vectors = generate_embedding([question])
        if not query_vectors or len(query_vectors) == 0:
            print("生成查询向量失败")
            return []

        query_vector = query_vectors[0]

        # 2. 执行向量搜索
        milvus = get_milvus_service()
        results = milvus.search(
            collection_name=indexNames,
            query_vector=query_vector,
            top_k=top_k,
            kb_id=kb_id,
        )

        # 3. 格式化结果
        extracted_data = []
        for i, result in enumerate(results, start=1):
            message = {
                "id": i,
                "document_id": result.get("doc_id", "N/A"),
                "document_name": result.get("filename", "N/A"),
                "content_with_weight": result.get("content", ""),
                "score": result.get("score", 0),
            }
            extracted_data.append(message)

        return extracted_data

    except Exception as e:
        print(f"检索错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return []


def retrieve_from_knowledge_base(
    kb_name: str,
    question: str,
    top_k: int = 5,
) -> List[Dict[str, Any]]:
    """
    从知识库检索内容

    Args:
        kb_name: 知识库名称
        question: 查询问题
        top_k: 返回结果数量

    Returns:
        检索结果列表
    """
    # 将知识库名称转换为集合名称
    collection_name = f"kb_{kb_name}".lower().replace(" ", "_")
    return retrieve_content(collection_name, question, top_k)
