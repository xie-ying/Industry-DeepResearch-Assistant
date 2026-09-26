"""数据库探索路由 - PostgreSQL 可视化 + Text2SQL"""
import os
from typing import List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from core.database import get_db
from models.user import User
from router.auth_router import get_current_user_required
from service.database_explorer import DatabaseExplorer
from service.text2sql_service import Text2SQLService
from config.llm_config import get_config

router = APIRouter(prefix="/database", tags=["数据库探索"])


# ========== Schemas ==========

class TableInfo(BaseModel):
    """表信息"""
    name: str
    size: str
    column_count: int
    row_count: int


class ColumnInfo(BaseModel):
    """列信息"""
    name: str
    type: str
    max_length: Optional[int] = None
    nullable: bool
    default: Optional[str] = None


class IndexInfo(BaseModel):
    """索引信息"""
    name: str
    definition: str


class TableSchema(BaseModel):
    """表结构"""
    table_name: str
    columns: List[ColumnInfo]
    primary_keys: List[str]
    indexes: List[IndexInfo]


class TableDataResponse(BaseModel):
    """表数据响应"""
    table_name: str
    columns: List[str]
    rows: List[dict]
    total: int
    limit: int
    offset: int


class QueryRequest(BaseModel):
    """查询请求"""
    sql: str = Field(..., description="SQL 查询语句（仅支持 SELECT）")
    limit: int = Field(100, ge=1, le=1000, description="结果限制")


class QueryResponse(BaseModel):
    """查询响应"""
    columns: List[str]
    rows: List[dict]
    row_count: int


class Text2SQLRequest(BaseModel):
    """Text2SQL 请求"""
    question: str = Field(..., description="自然语言问题")
    intent: str = Field("stats", description="查询意图: stats/trend/comparison/detail")


class Text2SQLResponse(BaseModel):
    """Text2SQL 响应"""
    success: bool
    sql: str = ""
    explanation: str = ""
    data: List[dict] = []
    columns: List[str] = []
    visualization_hint: str = "table"
    confidence: Optional[float] = None
    row_count: int = 0
    error: Optional[str] = None


# ========== Routes ==========

@router.get("/tables", response_model=List[TableInfo])
async def get_tables(
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db),
):
    """获取当前数据库的所有表"""
    explorer = DatabaseExplorer(db)
    try:
        tables = explorer.get_tables()
        return [TableInfo(**t) for t in tables]
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取表列表失败: {str(e)}"
        )


@router.get("/tables/{table_name}/schema", response_model=TableSchema)
async def get_table_schema(
    table_name: str,
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db),
):
    """获取表结构"""
    explorer = DatabaseExplorer(db)
    try:
        schema = explorer.get_table_schema(table_name)
        return TableSchema(
            table_name=schema["table_name"],
            columns=[ColumnInfo(**c) for c in schema["columns"]],
            primary_keys=schema["primary_keys"],
            indexes=[IndexInfo(**i) for i in schema["indexes"]],
        )
    except ValueError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取表结构失败: {str(e)}"
        )


@router.get("/tables/{table_name}/data", response_model=TableDataResponse)
async def get_table_data(
    table_name: str,
    limit: int = 100,
    offset: int = 0,
    order_by: Optional[str] = None,
    order_dir: str = "asc",
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db),
):
    """获取表数据（分页）"""
    if limit > 1000:
        limit = 1000

    explorer = DatabaseExplorer(db)
    try:
        data = explorer.get_table_data(table_name, limit, offset, order_by, order_dir)
        return TableDataResponse(**data)
    except ValueError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取表数据失败: {str(e)}"
        )


@router.post("/query", response_model=QueryResponse)
async def execute_query(
    request: QueryRequest,
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db),
):
    """执行只读 SQL 查询（仅支持 SELECT）"""
    explorer = DatabaseExplorer(db)
    try:
        result = explorer.execute_query(request.sql, request.limit)
        return QueryResponse(**result)
    except ValueError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查询执行失败: {str(e)}"
        )


@router.post("/text2sql", response_model=Text2SQLResponse)
async def text2sql_query(
    request: Text2SQLRequest,
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db),
):
    """
    自然语言转 SQL 查询

    将用户的自然语言问题转换为 SQL 并执行，返回结构化结果和可视化建议
    """
    try:
        # 获取 LLM 配置
        config = get_config()

        # 构建数据库连接字符串
        db_url = os.getenv("DATABASE_URL", "")
        if not db_url:
            # 从单独的环境变量构建
            pg_host = os.getenv("POSTGRES_HOST", "localhost")
            pg_port = os.getenv("POSTGRES_PORT", "5432")
            pg_user = os.getenv("POSTGRES_USER", "postgres")
            pg_pass = os.getenv("POSTGRES_PASSWORD", "")
            pg_db = os.getenv("POSTGRES_DB", "industry_assistant")
            if pg_host and pg_user and pg_db:
                db_url = f"postgresql://{pg_user}:{pg_pass}@{pg_host}:{pg_port}/{pg_db}"

        # 创建 Text2SQL 服务 (使用 qwen-plus 更稳定的 JSON 输出)
        service = Text2SQLService(
            llm_api_key=config.api_key,
            llm_base_url=config.base_url,
            db_connection_string=db_url if db_url else None,
            model="qwen-plus"  # 使用 qwen-plus 替代 deepseek，更稳定的 JSON 输出
        )

        # 执行查询
        result = await service.query(request.question, request.intent)

        return Text2SQLResponse(
            success=result.get("success", False),
            sql=result.get("sql", ""),
            explanation=result.get("explanation", ""),
            data=result.get("data", []),
            columns=result.get("columns", []),
            visualization_hint=result.get("visualization_hint", "table"),
            confidence=result.get("confidence"),
            row_count=result.get("row_count", 0),
            error=result.get("error")
        )

    except Exception as e:
        return Text2SQLResponse(
            success=False,
            error=f"Text2SQL 服务异常: {str(e)}"
        )
