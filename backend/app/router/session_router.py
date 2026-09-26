"""会话管理路由"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from core.database import get_db
from models.chat import ChatSession, ChatMessage
from models.user import User
from router.auth_router import get_current_user_required, get_current_user
from schemas.chat import (
    SessionCreate,
    SessionUpdate,
    SessionResponse,
    SessionWithMessagesResponse,
    MessageCreate,
    MessageResponse,
)

router = APIRouter(prefix="/sessions", tags=["会话管理"])


def session_to_response(session: ChatSession, message_count: int = 0) -> SessionResponse:
    """将会话模型转换为响应"""
    return SessionResponse(
        id=str(session.id),
        title=session.title or "新对话",
        session_type=session.session_type or "chat",
        created_at=session.created_at,
        updated_at=session.updated_at,
        message_count=message_count,
    )


def message_to_response(message: ChatMessage) -> MessageResponse:
    """将消息模型转换为响应"""
    return MessageResponse(
        id=str(message.id),
        session_id=str(message.session_id),
        role=message.role,
        content=message.content,
        thinking=message.thinking,
        references_data=message.references_data,
        image_results=message.image_results,
        created_at=message.created_at,
    )


@router.get("", response_model=List[SessionResponse])
async def get_sessions(
    limit: int = Query(50, ge=1, le=100, description="返回数量限制"),
    offset: int = Query(0, ge=0, description="偏移量"),
    session_type: Optional[str] = Query(None, description="会话类型筛选"),
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db),
):
    """获取用户的会话列表"""
    query = db.query(ChatSession).filter(ChatSession.user_id == current_user.id)

    if session_type:
        query = query.filter(ChatSession.session_type == session_type)

    # 按更新时间倒序
    sessions = query.order_by(ChatSession.updated_at.desc()).offset(offset).limit(limit).all()

    # 获取每个会话的消息数量
    result = []
    for session in sessions:
        message_count = db.query(func.count(ChatMessage.id)).filter(
            ChatMessage.session_id == session.id
        ).scalar()
        result.append(session_to_response(session, message_count))

    return result


@router.post("", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    session_data: SessionCreate,
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db),
):
    """创建新会话"""
    session = ChatSession(
        user_id=current_user.id,
        title=session_data.title or "新对话",
        session_type=session_data.session_type,
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    return session_to_response(session, 0)


@router.get("/{session_id}", response_model=SessionWithMessagesResponse)
async def get_session(
    session_id: str,
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db),
):
    """获取会话详情（包含消息）"""
    try:
        session_uuid = UUID(session_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的会话ID格式"
        )

    session = db.query(ChatSession).filter(
        ChatSession.id == session_uuid,
        ChatSession.user_id == current_user.id
    ).first()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会话不存在"
        )

    # 获取消息列表
    messages = db.query(ChatMessage).filter(
        ChatMessage.session_id == session.id
    ).order_by(ChatMessage.created_at.asc()).all()

    return SessionWithMessagesResponse(
        id=str(session.id),
        title=session.title or "新对话",
        session_type=session.session_type or "chat",
        created_at=session.created_at,
        updated_at=session.updated_at,
        message_count=len(messages),
        messages=[message_to_response(m) for m in messages],
    )


@router.put("/{session_id}", response_model=SessionResponse)
async def update_session(
    session_id: str,
    session_data: SessionUpdate,
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db),
):
    """更新会话标题"""
    try:
        session_uuid = UUID(session_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的会话ID格式"
        )

    session = db.query(ChatSession).filter(
        ChatSession.id == session_uuid,
        ChatSession.user_id == current_user.id
    ).first()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会话不存在"
        )

    session.title = session_data.title
    db.commit()
    db.refresh(session)

    message_count = db.query(func.count(ChatMessage.id)).filter(
        ChatMessage.session_id == session.id
    ).scalar()

    return session_to_response(session, message_count)


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: str,
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db),
):
    """删除会话"""
    try:
        session_uuid = UUID(session_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的会话ID格式"
        )

    session = db.query(ChatSession).filter(
        ChatSession.id == session_uuid,
        ChatSession.user_id == current_user.id
    ).first()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会话不存在"
        )

    db.delete(session)
    db.commit()
    return None


@router.get("/{session_id}/messages", response_model=List[MessageResponse])
async def get_messages(
    session_id: str,
    limit: int = Query(100, ge=1, le=500, description="返回数量限制"),
    offset: int = Query(0, ge=0, description="偏移量"),
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db),
):
    """获取会话的消息列表"""
    try:
        session_uuid = UUID(session_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的会话ID格式"
        )

    # 验证会话所有权
    session = db.query(ChatSession).filter(
        ChatSession.id == session_uuid,
        ChatSession.user_id == current_user.id
    ).first()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会话不存在"
        )

    messages = db.query(ChatMessage).filter(
        ChatMessage.session_id == session_uuid
    ).order_by(ChatMessage.created_at.asc()).offset(offset).limit(limit).all()

    return [message_to_response(m) for m in messages]


@router.post("/{session_id}/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def add_message(
    session_id: str,
    message_data: MessageCreate,
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db),
):
    """向会话添加消息"""
    try:
        session_uuid = UUID(session_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的会话ID格式"
        )

    # 验证会话所有权
    session = db.query(ChatSession).filter(
        ChatSession.id == session_uuid,
        ChatSession.user_id == current_user.id
    ).first()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会话不存在"
        )

    # 创建消息
    message = ChatMessage(
        session_id=session_uuid,
        role=message_data.role,
        content=message_data.content,
        thinking=message_data.thinking,
        references_data=message_data.references_data,
        image_results=message_data.image_results,
    )
    db.add(message)

    # 更新会话的 updated_at
    from datetime import datetime
    session.updated_at = datetime.utcnow()

    # 如果是第一条用户消息，自动生成标题
    if message_data.role == "user" and session.title == "新对话":
        # 取消息前20个字符作为标题
        session.title = message_data.content[:20] + ("..." if len(message_data.content) > 20 else "")

    db.commit()
    db.refresh(message)

    return message_to_response(message)
