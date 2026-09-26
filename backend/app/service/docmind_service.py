"""DocMind 文档智能解析服务"""
import os
import time
import hashlib
from typing import List, Dict, Any, Optional
from alibabacloud_docmind_api20220711.client import Client as DocMindClient
from alibabacloud_docmind_api20220711 import models as docmind_models
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_tea_util import models as util_models

from service.embedding_service import generate_embedding
from service.milvus_service import get_milvus_service


class DocMindService:
    """DocMind 文档解析服务"""

    def __init__(self):
        self.access_key_id = os.getenv("DOCMIND_ACCESS_KEY_ID")
        self.access_key_secret = os.getenv("DOCMIND_ACCESS_KEY_SECRET")
        self.endpoint = "docmind-api.cn-hangzhou.aliyuncs.com"
        self.client = self._create_client()

    def _create_client(self) -> DocMindClient:
        """创建 DocMind 客户端"""
        config = open_api_models.Config(
            access_key_id=self.access_key_id,
            access_key_secret=self.access_key_secret,
        )
        config.endpoint = self.endpoint
        return DocMindClient(config)

    def submit_job(self, file_path: str, file_name: str) -> Optional[str]:
        """
        提交文档解析任务

        Args:
            file_path: 文件路径
            file_name: 文件名

        Returns:
            任务 ID，失败返回 None
        """
        try:
            request = docmind_models.SubmitDocParserJobAdvanceRequest(
                file_url_object=open(file_path, "rb"),
                file_name=file_name,
                file_name_extension=file_name.split('.')[-1] if '.' in file_name else None,
            )

            runtime = util_models.RuntimeOptions()
            response = self.client.submit_doc_parser_job_advance(request, runtime)

            if response.body and response.body.data:
                task_id = response.body.data.id
                print(f"任务已提交，任务ID: {task_id}")
                return task_id
            return None

        except Exception as e:
            print(f"提交任务失败: {e}")
            import traceback
            traceback.print_exc()
            return None

    def query_status(self, task_id: str) -> Optional[Dict]:
        """
        查询任务状态

        Args:
            task_id: 任务ID

        Returns:
            任务状态信息
        """
        try:
            request = docmind_models.QueryDocParserStatusRequest(id=task_id)
            response = self.client.query_doc_parser_status(request)
            if response.body and response.body.data:
                return response.body.data.to_map()
            return None
        except Exception as e:
            print(f"查询状态失败: {e}")
            return None

    def wait_for_completion(self, task_id: str, poll_interval: int = 5, max_wait: int = 300) -> bool:
        """
        等待任务完成

        Args:
            task_id: 任务ID
            poll_interval: 轮询间隔（秒）
            max_wait: 最大等待时间（秒）

        Returns:
            任务是否成功完成
        """
        print("开始轮询任务状态...")
        start_time = time.time()

        while time.time() - start_time < max_wait:
            status_data = self.query_status(task_id)
            if not status_data:
                print("查询状态失败")
                return False

            status = status_data.get('Status', '').lower()
            print(f"当前状态: {status}")

            if status == 'success':
                print("任务已成功完成")
                return True
            elif status == 'failed':
                print("任务执行失败")
                return False
            else:
                # 任务仍在处理中
                time.sleep(poll_interval)

        print("等待超时")
        return False

    def get_result(self, task_id: str, layout_num: int = 0, layout_step_size: int = 10) -> Optional[Any]:
        """
        获取文档解析结果（支持增量获取）

        Args:
            task_id: 任务ID
            layout_num: 起始布局编号
            layout_step_size: 步长

        Returns:
            解析结果
        """
        try:
            request = docmind_models.GetDocParserResultRequest(
                id=task_id,
                layout_step_size=layout_step_size,
                layout_num=layout_num
            )
            response = self.client.get_doc_parser_result(request)
            return response.body.data if response.body.data else None
        except Exception as e:
            print(f"获取结果失败: {e}")
            return None

    def collect_all_results(self, task_id: str, layout_step_size: int = 10) -> str:
        """
        收集所有解析结果

        Args:
            task_id: 任务ID
            layout_step_size: 步长

        Returns:
            完整的文本内容
        """
        all_text = ""
        layout_num = 0

        while True:
            result_data = self.get_result(task_id, layout_num, layout_step_size)
            if not result_data:
                break

            # 尝试获取 layouts
            layouts = None
            if hasattr(result_data, 'layouts'):
                layouts = result_data.layouts
            elif isinstance(result_data, dict):
                layouts = result_data.get('layouts', [])

            if not layouts:
                break

            print(f"获取到 {len(layouts)} 个布局块 (从 {layout_num} 开始)")

            # 提取文本
            for layout in layouts:
                # 优先使用 markdownContent
                if hasattr(layout, 'markdown_content') and layout.markdown_content:
                    all_text += layout.markdown_content + "\n"
                elif hasattr(layout, 'markdownContent') and layout.markdownContent:
                    all_text += layout.markdownContent + "\n"
                elif isinstance(layout, dict):
                    if layout.get('markdownContent'):
                        all_text += layout['markdownContent'] + "\n"
                    elif layout.get('text'):
                        all_text += layout['text'] + "\n"
                # 尝试 text 属性
                elif hasattr(layout, 'text') and layout.text:
                    all_text += layout.text + "\n"

            # 更新下次获取的起始位置
            layout_num += len(layouts)

            # 如果获取到的数量小于步长，说明已经获取完所有内容
            if len(layouts) < layout_step_size:
                break

        return all_text


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """
    将文本切分成块

    Args:
        text: 原始文本
        chunk_size: 每块大小
        overlap: 重叠大小

    Returns:
        文本块列表
    """
    if not text:
        return []

    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]

        # 尝试在句子边界切分
        if end < len(text):
            for sep in ['。', '！', '？', '.', '!', '?', '\n']:
                last_sep = chunk.rfind(sep)
                if last_sep > chunk_size // 2:
                    chunk = chunk[:last_sep + 1]
                    end = start + last_sep + 1
                    break

        if chunk.strip():
            chunks.append(chunk.strip())

        start = end - overlap

    return chunks


def process_document_with_docmind(
    file_path: str,
    file_name: str,
    index_name: str,
    chunk_size: int = 500
) -> Dict[str, Any]:
    """
    使用 DocMind 处理文档

    Args:
        file_path: 文件路径
        file_name: 文件名
        index_name: ES 索引名
        chunk_size: 切片大小

    Returns:
        处理结果
    """
    result = {
        "success": False,
        "message": "",
        "document_count": 0,
    }

    try:
        print(f"开始处理文档: {file_name}")

        # 1. 初始化服务并提交任务
        service = DocMindService()
        task_id = service.submit_job(file_path, file_name)

        if not task_id:
            result["message"] = "文档提交失败"
            print(result["message"])
            return result

        # 2. 等待任务完成
        if not service.wait_for_completion(task_id):
            result["message"] = "文档解析任务失败或超时"
            print(result["message"])
            return result

        # 3. 收集解析结果
        print("开始收集解析结果...")
        text = service.collect_all_results(task_id)

        if not text or not text.strip():
            result["message"] = "文档内容为空"
            print(result["message"])
            return result

        print(f"解析到文本长度: {len(text)}")

        # 4. 文本切分
        chunks = chunk_text(text, chunk_size=chunk_size)

        if not chunks:
            result["message"] = "文档切分失败"
            print(result["message"])
            return result

        print(f"文档切分完成，共 {len(chunks)} 个切片")

        # 5. 生成向量嵌入
        print("开始生成向量嵌入...")
        embeddings = generate_embedding(chunks)

        if not embeddings:
            result["message"] = "向量生成失败: 返回为空"
            print(result["message"])
            return result

        if len(embeddings) != len(chunks):
            result["message"] = f"向量生成失败: 数量不匹配 ({len(embeddings)} vs {len(chunks)})"
            print(result["message"])
            return result

        print(f"向量生成完成，维度: {len(embeddings[0])}")

        # 6. 构建 Milvus 文档
        doc_id = hashlib.md5(file_name.encode()).hexdigest()
        documents = []

        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            chunk_id = hashlib.md5(f"{file_name}_{i}_{chunk[:50]}".encode()).hexdigest()

            doc = {
                "id": chunk_id,
                "doc_id": doc_id,
                "kb_id": index_name,
                "filename": file_name,
                "content": chunk,
                "chunk_index": i,
                "vector": embedding,
            }
            documents.append(doc)

        # 7. 插入 Milvus
        print(f"开始插入 Milvus，集合: {index_name}")
        milvus = get_milvus_service()
        milvus.insert_documents(index_name, documents)

        result["success"] = True
        result["message"] = f"成功处理 {len(documents)} 个切片"
        result["document_count"] = len(documents)

        print(f"文档处理完成: {result['message']}")

    except Exception as e:
        result["message"] = f"处理失败: {str(e)}"
        print(f"文档处理异常: {e}")
        import traceback
        traceback.print_exc()

    return result
