import json
import os
from typing import List, Dict, Any, Optional, Generator
import uuid
from openai import OpenAI
import numpy as np
from llama_index.core.data_structs import Node
from llama_index.core.schema import NodeWithScore
from llama_index.postprocessor.dashscope_rerank import DashScopeRerank
import tiktoken

from .document_service import DocumentService
from .web_search_service import WebSearchService
from .session_service import SessionService
from .memory_service import get_memory_service


class ChatService:
    """Chat service that combines document retrieval and LLM generation"""
    
    def __init__(self, document_service: DocumentService, web_search_service: WebSearchService, session_service: SessionService):
        """
        Initialize the ChatService.
        
        Args:
            document_service: Document service for knowledge base retrieval
            web_search_service: Web search service for internet search
            session_service: Session service for chat history management
        """
        self.document_service = document_service
        self.web_search_service = web_search_service
        self.session_service = session_service
        self.openai_api_key = os.environ.get("DASHSCOPE_API_KEY", "")
        self.openai_base_url = os.environ.get("OPENAI_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
        self.openai_model = os.environ.get("OPENAI_MODEL", "deepseek-r1")
        self.encoding = tiktoken.get_encoding("cl100k_base")  # OpenAI通用编码
        self.max_tokens = 12000  # 最大token数量限制
    
    def retrieve_from_knowledge_base(self, question: str, dataset_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve documents from knowledge base.
        
        Args:
            question: User question
            dataset_id: Dataset ID
            
        Returns:
            List of retrieved documents
        """
        try:
            response = self.document_service.retrieve_documents(
                question=question,
                dataset_ids=[dataset_id]
            )
            
            if response.get("code") != 0:
                return []
                
            # 从响应中提取文档
            documents = []
            if "data" in response and "chunks" in response["data"]:
                for i, chunk in enumerate(response["data"]["chunks"]):
                    # 使用document_keyword作为title
                    title = chunk.get("document_keyword", None)
                    
                    doc = {
                        "id": i+1,
                        "content": chunk.get("content", ""),
                        "content_with_weight": f"{chunk.get('content', '')} (相关度: {chunk.get('score', 0):.2f})",
                        "source": "knowledge",
                        "title": title,
                        "weight": chunk.get("score", 1.0)
                    }
                    documents.append(doc)
            
            return documents
        except Exception as e:
            print(f"Error retrieving from knowledge base: {str(e)}")
            return []
    
    def retrieve_from_web(self, question: str) -> List[Dict[str, Any]]:
        """
        Retrieve information from web search.
        
        Args:
            question: User question
            
        Returns:
            List of search results formatted as documents
        """
        try:
            # 执行Web搜索
            search_results = self.web_search_service.search(query=question)
            
            if "error" in search_results and search_results["error"]:
                return []
            
            # 提取并格式化搜索结果
            formatted_results = self.web_search_service.extract_search_results(search_results)
            
            # 转换为文档格式
            documents = []
            for i, result in enumerate(formatted_results):
                if result.get("type") == "organic":
                    # 只使用有机搜索结果
                    doc = {
                        "id": i+1,
                        "content": result.get("snippet", ""),
                        "content_with_weight": result.get("snippet", ""),
                        "source": "web",
                        "title": result.get("title", None),
                        "link": result.get("link", None),
                        "weight": 1.0 - (i * 0.1)  # 根据位置降低权重
                    }
                    documents.append(doc)
                elif result.get("type") == "knowledgeGraph":
                    # 知识图谱结果
                    description = result.get("description", "")
                    if description:
                        doc = {
                            "id": len(documents) + 1,
                            "content": description,
                            "content_with_weight": description,
                            "source": "web",
                            "title": result.get("title", None),
                            "link": result.get("link", None),
                            "weight": 1.2  # 知识图谱通常更相关
                        }
                        documents.append(doc)
            
            return documents
        except Exception as e:
            print(f"Error retrieving from web: {str(e)}")
            return []
    
    def rerank_similarity(self, query: str, documents: List[Dict[str, Any]]) -> List[float]:
        """
        使用DashScope重排对文档进行相似度评分
        
        Args:
            query: 用户查询
            documents: 要评分的文档列表
            
        Returns:
            文档相似度分数列表
        """
        try:
            api_key = os.getenv("DASHSCOPE_API_KEY", self.openai_api_key)
            
            # 从文档中提取文本
            texts = [doc["content"] for doc in documents]
            
            # 创建节点列表
            nodes = [NodeWithScore(node=Node(text=text), score=1.0) for text in texts]
            
            # 初始化 DashScopeRerank
            dashscope_rerank = DashScopeRerank(top_n=len(texts), api_key=api_key)
            
            # 执行重排序
            results = dashscope_rerank.postprocess_nodes(nodes, query_str=query)
            
            # 提取分数
            scores = [res.score for res in results]
            scores = np.array(scores)
            
            return scores
        except Exception as e:
            print(f"Error in rerank_similarity: {str(e)}")
            # 出错时返回原始权重
            return [doc.get("weight", 1.0) for doc in documents]
    
    def rerank_documents(self, question: str, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        使用DashScope重排对文档进行重排序，并确保不超过token数量限制。
        
        Args:
            question: 用户问题
            documents: 要重排的文档列表
            
        Returns:
            重排后的文档列表，确保总token数不超过限制
        """
        if not documents:
            return []
        
        try:
            # 使用DashScope重排进行重排序
            similarity_scores = self.rerank_similarity(question, documents)
            
            # 更新文档的权重和content_with_weight字段
            for i, score in enumerate(similarity_scores):
                if i < len(documents):  # 防止索引越界
                    documents[i]["weight"] = float(score)
                    documents[i]["content_with_weight"] = f"{documents[i]['content']} (相关度: {float(score):.2f})"
            
            # 根据新权重排序（权重越高越相关）
            sorted_docs = sorted(documents, key=lambda x: x.get("weight", 0), reverse=True)
            
            # 计算token并截断，保证总token数不超过限制
            filtered_docs = []
            total_tokens = 0
            
            print(f"\n{'='*50}")
            print(f"文档Token数量控制:")
            print(f"{'='*50}")
            
            for doc in sorted_docs:
                # 计算此文档的token数量（内容部分）
                doc_tokens = len(self.encoding.encode(doc["content"]))
                
                # 检查是否会超出限制
                if total_tokens + doc_tokens > self.max_tokens:
                    print(f"跳过文档: {doc.get('title', '无标题')} ({doc_tokens} tokens)，会超出限制")
                    continue
                
                # 加入文档并累计token数
                filtered_docs.append(doc)
                total_tokens += doc_tokens
                print(f"添加文档: {doc.get('title', '无标题')} ({doc_tokens} tokens), 累计: {total_tokens}/{self.max_tokens}")
                
                # 如果已经有10个文档，跳出循环（保持现有的文档数量限制）
                if len(filtered_docs) >= 10:
                    break
            
            print(f"\n文档筛选结果: 选择了 {len(filtered_docs)}/{len(sorted_docs)} 个文档，总token数: {total_tokens}")
            print(f"{'='*50}\n")
            
            # 确保文档ID是连续的
            for i, doc in enumerate(filtered_docs):
                doc["id"] = i + 1
                
            return filtered_docs
        except Exception as e:
            print(f"Error in rerank_documents: {str(e)}")
            # 出错时回退到简单排序
            sorted_docs = sorted(documents, key=lambda x: x.get("weight", 0), reverse=True)
            return sorted_docs[:10]
    
    def get_chat_completion(self, session_id: Optional[str], question: str,
                           retrieved_content: List[Dict[str, Any]],
                           user_id: Optional[str] = None) -> Generator[str, None, None]:
        """
        获取流式聊天完成结果，并按照指定格式输出。

        Args:
            session_id: 会话ID（可选）
            question: 用户问题
            retrieved_content: 检索到的内容
            user_id: 用户ID（用于检索长期记忆）

        Returns:
            流式输出的生成器，每个元素为符合SSE格式的字符串
        """
        # 判断 contents 是否为空
        if not retrieved_content:
            formatted_references = "知识库没有找到相关内容, 请结合你自己的知识回答"
        else:
            # 格式化参考内容，添加序号
            formatted_refs = []
            for i, ref in enumerate(retrieved_content):
                formatted_refs.append(f"[{i+1}] [{ref['source']}] {ref['content_with_weight']}")
            formatted_references = "\n".join(formatted_refs)

        # 获取会话历史消息
        history_messages = []
        if session_id:
            # 将用户当前问题添加到会话历史
            self.session_service.add_message(session_id, "user", question)
            # 获取历史对话（不包含当前问题）
            history_messages = self.session_service.get_messages_for_prompt(session_id)

        # 格式化历史对话
        if history_messages:
            # 注意：history_messages已经按时间顺序排列，最近的对话在后面
            history_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in history_messages])
            history_context = f"\n\n历史对话（最近的对话内容更重要）：\n{history_text}"
        else:
            history_context = ""

        # 获取长期记忆上下文
        memory_context = ""
        if user_id:
            try:
                memory_service = get_memory_service()
                memory_context = memory_service.build_memory_context(
                    user_id=user_id,
                    current_query=question,
                    max_memories=3
                )
            except Exception as e:
                print(f"获取长期记忆失败: {e}")

        prompt = f"""你是一个智能助手，负责根据用户的问题和提供的参考内容生成回答。请严格按照以下要求生成回答：
1. 回答必须基于提供的参考内容。
2. 在回答中，每一块内容都必须标注引用的来源，格式为：##编号$$。例如：##1$$ 表示引用自第1条参考内容。
3. 如果没有参考内容，请明确说明。
4. 注意保持与历史对话的连贯性。
5. 如果有相关历史记忆，请结合历史信息来回答。

{memory_context}
参考内容：
{formatted_references}
{history_context}

用户问题：{question}
"""

        print(prompt)

        try:
            # 初始化 OpenAI 客户端
            client = OpenAI(
                api_key=self.openai_api_key,
                base_url=self.openai_base_url
            )

            # 创建聊天完成请求
            completion = client.chat.completions.create(
                model=self.openai_model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                stream=True,
            )

            # 处理流式响应
            model_answer = ""  # 用于存储大模型的回答
            think = ""  # 用于存储思考过程
            for chunk in completion:
                # print("原始 chunk 数据:", chunk)
                if chunk.choices[0].finish_reason == "stop":
                    # 模型回答结束后，返回检索内容
                    message = {
                        "documents": retrieved_content,
                    }
                    json_message = json.dumps(message)
                    yield f"event: message\ndata: {json_message}\n\n"
                    
                    # 如果有会话ID，将回答添加到会话历史
                    if session_id and model_answer:
                        self.session_service.add_message(session_id, "assistant", model_answer)
                    
                    # 最后发送 [DONE] 事件
                    yield "event: end\ndata: [DONE]\n\n"
                    break
                else:
                    # 实时输出消息
                    delta = chunk.choices[0].delta
                    if hasattr(delta, "content") and delta.content:
                        model_answer += delta.content  # 累加大模型的回答
                        message = {
                            "role": "assistant",
                            "content": delta.content,
                            "thinking": False,
                        }
                        json_message = json.dumps(message)
                        yield f"event: message\ndata: {json_message}\n\n"
                    elif hasattr(delta, "reasoning_content") and delta.reasoning_content:
                        think += delta.reasoning_content
                        message = {
                            "role": "assistant",
                            "content": delta.reasoning_content,
                            "thinking": True,
                        }
                        json_message = json.dumps(message)
                        yield f"event: message\ndata: {json_message}\n\n"

        except Exception as e:
            # 发生错误时返回错误信息
            error_message = {
                "role": "error",
                "content": str(e)
            }
            json_error_message = json.dumps(error_message)
            yield f"event: error\ndata: {json_error_message}\n\n" 