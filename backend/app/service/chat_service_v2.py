from typing import List, Dict, Any
from .chat_service import ChatService
from .document_service import DocumentService
from .web_search_service import WebSearchService
from .session_service import SessionService
from .policy_search_service import PolicySearchService
import json


class ChatServiceV2(ChatService):
    """Chat service that extends ChatService to use PolicySearchService for knowledge base retrieval"""
    
    def __init__(self, document_service: DocumentService, web_search_service: WebSearchService, 
                 session_service: SessionService, policy_search_service: PolicySearchService):
        """
        Initialize the ChatServiceV2.
        
        Args:
            document_service: Document service for knowledge base retrieval (fallback)
            web_search_service: Web search service for internet search
            session_service: Session service for chat history management
            policy_search_service: Policy search service for policy document retrieval
        """
        super().__init__(document_service, web_search_service, session_service)
        self.policy_search_service = policy_search_service
    
    def retrieve_from_policy_documents(self, question: str, top_n: int = 10) -> List[Dict[str, Any]]:
        """
        Retrieve documents from policy document index using hybrid search.
        
        Args:
            question: User question
            top_n: Number of results to retrieve
            
        Returns:
            List of retrieved documents
        """
        try:
            print(f"\n{'='*50}")
            print(f"政策文档检索请求: '{question}'")
            print(f"{'='*50}")
            
            # 使用政策文档搜索服务进行混合检索
            response = self.policy_search_service.search(
                query=question,
                method="hybrid",
                top_n=top_n
            )
            
            print(f"\n政策检索API响应:")
            print(f"成功状态: {response.get('success', False)}")
            print(f"检索方法: {response.get('method', 'unknown')}")
            print(f"检索耗时: {response.get('took_ms', 0)}ms")
            print(f"检索结果数: {response.get('total', 0)}")
            
            if not response.get("success", False):
                print(f"检索失败: {response.get('message', '未知错误')}")
                return []
                
            # 从响应中提取文档
            documents = []
            # 用于去重的URL集合
            seen_urls = set()
            
            if "results" in response:
                print(f"\n{'='*50}")
                print(f"检索到的政策文档详情:")
                print(f"{'='*50}")
                
                for i, result in enumerate(response["results"]):
                    # 检查URL是否已存在（去重逻辑）
                    detail_url = result.get("detail_url", "")
                    if detail_url and detail_url in seen_urls:
                        print(f"跳过重复的文档: {result.get('title', '无标题')} - {detail_url}")
                        continue
                    
                    # 记录已处理的URL
                    if detail_url:
                        seen_urls.add(detail_url)
                    
                    # 获取原始内容，而不是高亮的内容
                    original_content = result.get("content", "")
                    
                    # 处理高亮信息，作为展示内容
                    highlighted_content = original_content
                    if "highlights" in result and "content" in result["highlights"]:
                        highlighted_content = result["highlights"]["content"]
                    
                    print(f"\n文档 #{i+1}:")
                    print(f"标题: {result.get('title', '无标题')}")
                    print(f"来源: {result.get('website', '未知来源')}")
                    print(f"日期: {result.get('date', '未知日期')}")
                    print(f"分数: {result.get('score', 0)}")
                    print(f"链接: {detail_url}")
                    print(f"内容预览: {highlighted_content[:200]}...")
                    
                    doc = {
                        "id": len(documents) + 1,  # 使用有序ID而不是原始索引i
                        "content": original_content,  # 使用原始内容
                        "content_with_weight": f"{highlighted_content} (相关度: {result.get('score', 0):.2f})",
                        "source": "knowledge",  # 将来源设置为knowledge
                        "title": result.get("title", "政策文档"),
                        "link": detail_url,
                        "weight": result.get("score", 1.0)
                    }
                    documents.append(doc)
            
            print(f"\n{'='*50}")
            print(f"共处理 {len(documents)} 个政策文档检索结果（去重后）")
            print(f"{'='*50}\n")
            
            return documents
        except Exception as e:
            print(f"Error retrieving from policy documents: {str(e)}")
            return [] 