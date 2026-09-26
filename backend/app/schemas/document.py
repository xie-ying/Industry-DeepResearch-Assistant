from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class DeleteDocumentsRequest(BaseModel):
    """请求模型：删除文档"""
    document_ids: List[str]


class RetrieveDocumentsRequest(BaseModel):
    """请求模型：检索文档"""
    question: str
    document_ids: Optional[List[str]] = None


class DocumentResponse(BaseModel):
    """文档基本信息响应模型"""
    id: str
    name: str
    type: str
    size: int
    status: Optional[str] = None
    run: Optional[str] = None
    progress: Optional[float] = None
    chunk_count: Optional[int] = None
    token_count: Optional[int] = None
    create_time: Optional[int] = None
    update_time: Optional[int] = None
    created_by: Optional[str] = None
    index_name: Optional[str] = None
    json_file_path: Optional[str] = None
    

class ProcessingDetails(BaseModel):
    """文档处理详情"""
    document_count: int
    es_inserted: bool
    json_file_path: str


class UploadDocumentResponse(BaseModel):
    """上传文档响应模型"""
    status: str
    message: str
    document: Optional[Dict[str, Any]] = None
    document_id: Optional[str] = None
    upload_response: Optional[Dict[str, Any]] = None
    processing_details: Optional[ProcessingDetails] = None


class DocumentListResponse(BaseModel):
    """文档列表响应模型"""
    code: int
    data: Dict[str, Any]


class DeleteDocumentsResponse(BaseModel):
    """删除文档响应模型"""
    code: int
    message: str
    data: Dict[str, Any] 