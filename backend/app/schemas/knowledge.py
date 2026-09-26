"""知识库相关 Schema"""
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


# ============ 知识库 Schema ============

class KnowledgeBaseCreate(BaseModel):
    """创建知识库请求"""
    name: str = Field(..., min_length=1, max_length=255, description="知识库名称")
    description: Optional[str] = Field(None, description="知识库描述")


class KnowledgeBaseUpdate(BaseModel):
    """更新知识库请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="知识库名称")
    description: Optional[str] = Field(None, description="知识库描述")


class KnowledgeBaseResponse(BaseModel):
    """知识库响应"""
    id: str = Field(..., description="知识库ID")
    name: str = Field(..., description="知识库名称")
    description: Optional[str] = Field(None, description="知识库描述")
    document_count: int = Field(0, description="文档数量")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True


# ============ 文档 Schema ============

class DocumentResponse(BaseModel):
    """文档响应"""
    id: str = Field(..., description="文档ID")
    knowledge_base_id: str = Field(..., description="知识库ID")
    filename: str = Field(..., description="文件名")
    file_type: Optional[str] = Field(None, description="文件类型")
    file_size: Optional[int] = Field(None, description="文件大小(字节)")
    status: str = Field(..., description="处理状态: pending, processing, completed, failed")
    chunk_count: int = Field(0, description="切片数量")
    error_message: Optional[str] = Field(None, description="错误信息")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True


class DocumentUploadResponse(BaseModel):
    """文档上传响应"""
    status: str = Field(default="success", description="API状态")
    id: str = Field(..., description="文档ID")
    filename: str = Field(..., description="文件名")
    process_status: str = Field(..., description="处理状态")
    message: str = Field(..., description="消息")


class KnowledgeBaseWithDocuments(KnowledgeBaseResponse):
    """带文档列表的知识库响应"""
    documents: List[DocumentResponse] = Field(default_factory=list, description="文档列表")
