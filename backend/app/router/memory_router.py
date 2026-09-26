"""长期记忆管理路由"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from datetime import datetime

from core.database import get_db
from models.chat import LongTermMemory, ChatSession, ChatMessage
from models.user import User
from router.auth_router import get_current_user_required
from service.memory_service import get_memory_service

router = APIRouter(prefix="/memories", tags=["长期记忆"])


# ========== Schemas ==========

class MemoryResponse(BaseModel):
    """记忆响应"""
    id: str = Field(..., description="记忆ID")
    session_id: Optional[str] = Field(None, description="关联会话ID")
    summary: str = Field(..., description="记忆摘要")
    key_insights: Optional[dict] = Field(None, description="关键洞察")
    token_count: Optional[int] = Field(None, description="Token数量")
    created_at: datetime = Field(..., description="创建时间")

    class Config:
        from_attributes = True


class MemoryListResponse(BaseModel):
    """记忆列表响应"""
    memories: List[MemoryResponse] = Field(default_factory=list, description="记忆列表")
    total: int = Field(0, description="总数")


class MemorySearchRequest(BaseModel):
    """记忆搜索请求"""
    query: str = Field(..., description="搜索查询")
    top_k: int = Field(5, ge=1, le=20, description="返回结果数量")


class MemorySearchResult(BaseModel):
    """记忆搜索结果"""
    id: str
    session_id: Optional[str]
    memory_type: str
    content: str
    score: float


class CreateMemoryRequest(BaseModel):
    """创建记忆请求"""
    session_id: str = Field(..., description="要总结的会话ID")


# ========== Routes ==========

@router.get("", response_model=MemoryListResponse)
async def get_memories(
    limit: int = 20,
    offset: int = 0,
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db),
):
    """获取用户的长期记忆列表"""
    memories = db.query(LongTermMemory).filter(
        LongTermMemory.user_id == current_user.id
    ).order_by(LongTermMemory.created_at.desc()).offset(offset).limit(limit).all()

    total = db.query(LongTermMemory).filter(
        LongTermMemory.user_id == current_user.id
    ).count()

    return MemoryListResponse(
        memories=[
            MemoryResponse(
                id=str(mem.id),
                session_id=str(mem.session_id) if mem.session_id else None,
                summary=mem.summary,
                key_insights=mem.key_insights,
                token_count=mem.token_count,
                created_at=mem.created_at,
            )
            for mem in memories
        ],
        total=total,
    )


@router.get("/{memory_id}", response_model=MemoryResponse)
async def get_memory(
    memory_id: str,
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db),
):
    """获取单个记忆详情"""
    try:
        mem_uuid = UUID(memory_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的记忆ID格式"
        )

    memory = db.query(LongTermMemory).filter(
        LongTermMemory.id == mem_uuid,
        LongTermMemory.user_id == current_user.id
    ).first()

    if not memory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="记忆不存在"
        )

    return MemoryResponse(
        id=str(memory.id),
        session_id=str(memory.session_id) if memory.session_id else None,
        summary=memory.summary,
        key_insights=memory.key_insights,
        token_count=memory.token_count,
        created_at=memory.created_at,
    )


@router.post("/search", response_model=List[MemorySearchResult])
async def search_memories(
    request: MemorySearchRequest,
    current_user: User = Depends(get_current_user_required),
):
    """搜索相关记忆"""
    memory_service = get_memory_service()
    results = memory_service.retrieve_memories(
        user_id=str(current_user.id),
        query=request.query,
        top_k=request.top_k
    )

    return [
        MemorySearchResult(
            id=r.get("id", ""),
            session_id=r.get("session_id"),
            memory_type=r.get("memory_type", "unknown"),
            content=r.get("content", ""),
            score=r.get("score", 0.0),
        )
        for r in results
    ]


@router.post("/create", response_model=MemoryResponse)
async def create_memory_from_session(
    request: CreateMemoryRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db),
):
    """从会话创建长期记忆"""
    try:
        session_uuid = UUID(request.session_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的会话ID格式"
        )

    # 验证会话存在且属于当前用户
    session = db.query(ChatSession).filter(
        ChatSession.id == session_uuid,
        ChatSession.user_id == current_user.id
    ).first()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会话不存在"
        )

    # 获取会话消息
    messages = db.query(ChatMessage).filter(
        ChatMessage.session_id == session_uuid
    ).order_by(ChatMessage.created_at.asc()).all()

    if not messages:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="会话没有消息"
        )

    # 创建记忆
    memory_service = get_memory_service()
    memory = memory_service.create_memory(
        db=db,
        user_id=str(current_user.id),
        session_id=str(session_uuid),
        messages=messages
    )

    if not memory:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建记忆失败"
        )

    return MemoryResponse(
        id=str(memory.id),
        session_id=str(memory.session_id) if memory.session_id else None,
        summary=memory.summary,
        key_insights=memory.key_insights,
        token_count=memory.token_count,
        created_at=memory.created_at,
    )


@router.delete("/{memory_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_memory(
    memory_id: str,
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db),
):
    """删除长期记忆"""
    memory_service = get_memory_service()
    success = memory_service.delete_memory(
        db=db,
        memory_id=memory_id,
        user_id=str(current_user.id)
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="记忆不存在"
        )

    return None


@router.get("/context/{query}", response_model=dict)
async def get_memory_context(
    query: str,
    current_user: User = Depends(get_current_user_required),
):
    """获取与查询相关的记忆上下文"""
    memory_service = get_memory_service()
    context = memory_service.build_memory_context(
        user_id=str(current_user.id),
        current_query=query,
        max_memories=3
    )

    return {"context": context}
