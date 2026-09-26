from typing import Dict, Any, Optional, Literal
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from starlette.status import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_500_INTERNAL_SERVER_ERROR
import logging

from service import ResearchService, ServiceConfig
from service.dr_g import serialize_event  # 导入序列化函数
from core.redis_client import cache  # 导入 Redis 缓存

# V2 导入
from service.deep_research_v2.service import DeepResearchV2Service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ResearchRouter")

# 取消标志 key 前缀
CANCEL_KEY_PREFIX = "research:cancel:"

# 创建路由实例
router = APIRouter(prefix="/research", tags=["research"])

# 请求模型
class ResearchRequest(BaseModel):
    """深度研究请求模型"""
    query: str
    session_id: Optional[str] = None  # 会话 ID（用于检查点保存）
    max_iterations: Optional[int] = 3
    kb_name: Optional[str] = None  # 本地知识库名称
    search_web: Optional[bool] = None  # 是否搜索网络 (兼容旧版)
    search_local: Optional[bool] = None  # 是否搜索本地知识库 (兼容旧版)
    search_modes: Optional[list] = None  # 搜索模式: ['web', 'local'] (新版)
    version: Optional[Literal["v1", "v2"]] = "v2"  # 版本选择 (v2: 多智能体架构，推荐)

    class Config:
        json_schema_extra = {
            "example": {
                "query": "中国安责险的市场现状和未来发展趋势是什么？请提供具体数据支持。",
                "session_id": None,
                "max_iterations": 3,
                "kb_name": None,
                "search_modes": ["web", "local"],
                "version": "v2"
            }
        }

    def get_search_web(self) -> bool:
        """获取是否搜索网络"""
        if self.search_modes is not None:
            return 'web' in self.search_modes
        return self.search_web if self.search_web is not None else True

    def get_search_local(self) -> bool:
        """获取是否搜索本地知识库"""
        if self.search_modes is not None:
            return 'local' in self.search_modes
        return self.search_local if self.search_local is not None else False

# 获取服务实例
def get_research_service():
    """获取研究服务实例"""
    config = ServiceConfig.get_api_config()
    research_service = ResearchService(
        search_api_key=config.get('bochaai_api_key'),
        llm_api_key=config.get('dashscope_api_key'),
        llm_base_url=config.get('dashscope_base_url')
    )
    return {"research_service": research_service}


def get_research_service_v2():
    """获取 V2 研究服务实例（使用配置文件中的模型设置）"""
    # 直接创建服务，配置从 llm_config.py 读取
    return DeepResearchV2Service()

@router.post("/stream", status_code=HTTP_200_OK)
async def stream_research(
    request: ResearchRequest,
    services: Dict[str, Any] = Depends(get_research_service)
):
    """
    深度研究接口 - 流式输出

    对用户的研究问题执行全面的深度研究，包括问题分解、网络搜索、信息整合、数据分析和报告生成。
    使用 Server-Sent Events (SSE) 格式流式返回整个研究过程和结果。

    支持两个版本：
    - v1: 传统 ReAct 架构
    - v2: 多智能体协作网络（推荐）

    Args:
        request: 包含研究问题和配置的请求体

    Returns:
        流式响应，包含研究过程和结果的 SSE 格式数据
    """
    # 根据版本选择服务
    if request.version == "v2":
        search_web = request.get_search_web()
        search_local = request.get_search_local()
        logger.info(f"Using DeepResearch V2 for query: {request.query[:50]}... (session_id: {request.session_id}, search_web={search_web}, search_local={search_local})")
        service_v2 = get_research_service_v2()

        async def generate_sse_v2():
            try:
                async for event in service_v2.research(
                    query=request.query,
                    session_id=request.session_id,
                    kb_name=request.kb_name,
                    search_web=search_web,
                    search_local=search_local
                ):
                    yield event
            except Exception as e:
                logger.error(f"V2 Research error: {e}")
                error_event = serialize_event({"type": "error", "content": str(e)})
                yield f"data: {error_event}\n\n"

        return StreamingResponse(
            generate_sse_v2(),
            media_type="text/event-stream"
        )

    # V1 原有逻辑
    research_service = services["research_service"]

    async def generate_sse():
        try:
            async for event in research_service.research_stream(
                query=request.query,
                max_iterations=request.max_iterations,
                kb_name=request.kb_name,
                search_web=request.search_web,
                search_local=request.search_local
            ):
                # 将事件转换为 SSE 格式
                yield f"data: {event}\n\n"
        except Exception as e:
            # 使用serialize_event进行错误处理，确保JSON格式正确
            error_event = serialize_event({"type": "error", "content": str(e)})
            yield f"data: {error_event}\n\n"

    return StreamingResponse(
        generate_sse(),
        media_type="text/event-stream"
    )

@router.get("/stream", status_code=HTTP_200_OK)
async def stream_research_get(
    query: str = Query(..., description="研究问题", example="中国安责险的市场现状和未来发展趋势是什么？"),
    max_iterations: int = Query(3, description="最大迭代次数", ge=1, le=5),
    kb_name: Optional[str] = Query(None, description="本地知识库名称"),
    search_web: bool = Query(True, description="是否搜索网络"),
    search_local: bool = Query(True, description="是否搜索本地知识库"),
    version: str = Query("v1", description="版本: v1 或 v2"),
    services: Dict[str, Any] = Depends(get_research_service)
):
    """
    深度研究接口 - GET方式流式输出

    对用户的研究问题执行全面的深度研究，包括问题分解、网络搜索、信息整合、数据分析和报告生成。
    使用 Server-Sent Events (SSE) 格式流式返回整个研究过程和结果。

    支持两个版本：
    - v1: 传统 ReAct 架构
    - v2: 多智能体协作网络（推荐）

    Args:
        query: 研究问题
        max_iterations: 最大迭代次数（范围：1-5）
        version: 版本选择 (v1 或 v2)

    Returns:
        流式响应，包含研究过程和结果的 SSE 格式数据
    """
    # 根据版本选择服务
    if version == "v2":
        logger.info(f"Using DeepResearch V2 (GET) for query: {query[:50]}...")
        service_v2 = get_research_service_v2()

        async def generate_sse_v2():
            try:
                async for event in service_v2.research(
                    query=query,
                    kb_name=kb_name
                ):
                    yield event
            except Exception as e:
                logger.error(f"V2 Research error: {e}")
                error_event = serialize_event({"type": "error", "content": str(e)})
                yield f"data: {error_event}\n\n"

        return StreamingResponse(
            generate_sse_v2(),
            media_type="text/event-stream"
        )

    # V1 原有逻辑
    research_service = services["research_service"]

    async def generate_sse():
        try:
            async for event in research_service.research_stream(
                query=query,
                max_iterations=max_iterations,
                kb_name=kb_name,
                search_web=search_web,
                search_local=search_local
            ):
                # 将事件转换为 SSE 格式
                yield f"data: {event}\n\n"
        except Exception as e:
            # 使用serialize_event进行错误处理，确保JSON格式正确
            error_event = serialize_event({"type": "error", "content": str(e)})
            yield f"data: {error_event}\n\n"

    return StreamingResponse(
        generate_sse(),
        media_type="text/event-stream"
    )


@router.get("/test-wizard", status_code=HTTP_200_OK)
async def test_wizard_endpoint():
    """
    测试 CodeWizard 数据分析功能（绕过搜索阶段）

    使用模拟数据直接测试图表生成功能。
    """
    from service.deep_research_v2.agents.wizard import CodeWizard
    from service.deep_research_v2.state import ResearchState, ResearchPhase, create_initial_state
    from config.llm_config import get_config

    # 使用配置创建 CodeWizard 实例
    llm_config = get_config()
    wizard = CodeWizard(
        llm_api_key=llm_config.api_key,
        llm_base_url=llm_config.base_url,
        model=llm_config.agents.wizard.model
    )

    # 使用 create_initial_state 创建完整的状态
    mock_state = create_initial_state("中国GDP增长率分析", "test-session")

    # 设置分析阶段
    mock_state["phase"] = ResearchPhase.ANALYZING.value

    # 添加测试大纲
    mock_state["outline"] = [
        {"id": "sec_1", "title": "GDP增长趋势", "requires_chart": True, "section_type": "quantitative", "description": "分析中国近年GDP增长趋势"}
    ]

    # 添加测试数据点
    mock_state["data_points"] = [
        {"name": "2020年GDP增长率", "value": 2.3, "unit": "%"},
        {"name": "2021年GDP增长率", "value": 8.1, "unit": "%"},
        {"name": "2022年GDP增长率", "value": 3.0, "unit": "%"},
        {"name": "2023年GDP增长率", "value": 5.2, "unit": "%"},
        {"name": "2024年GDP增长率", "value": 5.0, "unit": "%"}
    ]

    # 添加测试事实
    mock_state["facts"] = [
        {
            "id": "fact_1",
            "content": "2020年中国GDP增长率为2.3%，是新冠疫情影响下的低谷",
            "source_url": "http://example.com",
            "source_name": "国家统计局",
            "related_sections": ["sec_1"]
        },
        {
            "id": "fact_2",
            "content": "2021年中国GDP强劲反弹，增长率达到8.1%",
            "source_url": "http://example.com",
            "source_name": "国家统计局",
            "related_sections": ["sec_1"]
        }
    ]

    try:
        # 执行数据分析
        result_state = await wizard.process(mock_state)

        charts = result_state.get("charts", [])
        return {
            "success": True,
            "charts_count": len(charts),
            "charts": [
                {
                    "title": c.get("title", ""),
                    "type": c.get("type", ""),
                    "has_image": bool(c.get("image_base64")),
                    "image_length": len(c.get("image_base64", "")) if c.get("image_base64") else 0
                }
                for c in charts
            ],
            "errors": result_state.get("errors", [])
        }
    except Exception as e:
        logger.error(f"Test wizard error: {e}")
        import traceback
        return {
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }


@router.post("/cancel/{session_id}", status_code=HTTP_200_OK)
async def cancel_research(session_id: str):
    """
    取消正在进行的研究任务

    Args:
        session_id: 会话ID

    Returns:
        取消确认信息
    """
    try:
        # 设置取消标志到 Redis，有效期 5 分钟
        cancel_key = f"{CANCEL_KEY_PREFIX}{session_id}"
        cache.set(cancel_key, {"cancelled": True}, expire=300)
        logger.info(f"Research cancelled for session: {session_id}")
        return {"success": True, "message": "Research cancellation requested"}
    except Exception as e:
        logger.error(f"Failed to cancel research: {e}")
        raise HTTPException(status_code=HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


def is_research_cancelled(session_id: str) -> bool:
    """
    检查研究任务是否已被取消

    Args:
        session_id: 会话ID

    Returns:
        是否已取消
    """
    cancel_key = f"{CANCEL_KEY_PREFIX}{session_id}"
    result = cache.get(cancel_key)
    return result is not None and result.get("cancelled", False)


def clear_cancel_flag(session_id: str):
    """
    清除取消标志（研究开始时调用）

    Args:
        session_id: 会话ID
    """
    cancel_key = f"{CANCEL_KEY_PREFIX}{session_id}"
    cache.delete(cancel_key)


# ============ 检查点 API ============

@router.get("/checkpoint/{session_id}", status_code=HTTP_200_OK)
async def get_checkpoint(session_id: str):
    """
    获取研究检查点信息

    Args:
        session_id: 会话ID

    Returns:
        检查点信息（不含完整状态）
    """
    try:
        from service.checkpoint_service import get_checkpoint_service
        checkpoint_service = get_checkpoint_service()
        info = checkpoint_service.get_checkpoint_info(session_id)
        if info:
            return {"success": True, "checkpoint": info}
        return {"success": False, "message": "No checkpoint found"}
    except Exception as e:
        logger.error(f"Failed to get checkpoint: {e}")
        raise HTTPException(status_code=HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/checkpoint/{session_id}/full", status_code=HTTP_200_OK)
async def get_full_checkpoint(session_id: str):
    """
    获取完整的研究检查点（包含 UI 状态和报告）

    用于恢复未完成的研究状态到前端

    Args:
        session_id: 会话ID

    Returns:
        完整检查点数据，包含:
        - state_json: 后端研究状态
        - ui_state_json: 前端 UI 状态（研究步骤、图表等）
        - final_report: 最终报告内容
    """
    try:
        from service.checkpoint_service import get_checkpoint_service
        checkpoint_service = get_checkpoint_service()
        full_data = checkpoint_service.load_full_checkpoint(session_id)
        if full_data:
            return {"success": True, "checkpoint": full_data}
        return {"success": False, "message": "No checkpoint found"}
    except Exception as e:
        logger.error(f"Failed to get full checkpoint: {e}")
        raise HTTPException(status_code=HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/checkpoints", status_code=HTTP_200_OK)
async def list_checkpoints(
    status: Optional[str] = Query(None, description="过滤状态: running/paused/completed/failed"),
    limit: int = Query(20, ge=1, le=100, description="返回数量限制")
):
    """
    列出研究检查点

    Args:
        status: 状态过滤
        limit: 返回数量限制

    Returns:
        检查点列表
    """
    try:
        from service.checkpoint_service import get_checkpoint_service
        checkpoint_service = get_checkpoint_service()
        checkpoints = checkpoint_service.list_checkpoints(status=status, limit=limit)
        return {"success": True, "checkpoints": checkpoints, "total": len(checkpoints)}
    except Exception as e:
        logger.error(f"Failed to list checkpoints: {e}")
        raise HTTPException(status_code=HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete("/checkpoint/{session_id}", status_code=HTTP_200_OK)
async def delete_checkpoint(session_id: str):
    """
    删除研究检查点

    Args:
        session_id: 会话ID

    Returns:
        删除结果
    """
    try:
        from service.checkpoint_service import get_checkpoint_service
        checkpoint_service = get_checkpoint_service()
        success = checkpoint_service.delete_checkpoint(session_id)
        if success:
            return {"success": True, "message": "Checkpoint deleted"}
        return {"success": False, "message": "Checkpoint not found"}
    except Exception as e:
        logger.error(f"Failed to delete checkpoint: {e}")
        raise HTTPException(status_code=HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/resume/{session_id}", status_code=HTTP_200_OK)
async def resume_research(session_id: str):
    """
    恢复研究任务（从检查点）

    Args:
        session_id: 会话ID

    Returns:
        流式响应，从检查点继续研究
    """
    try:
        from service.checkpoint_service import get_checkpoint_service
        checkpoint_service = get_checkpoint_service()
        info = checkpoint_service.get_checkpoint_info(session_id)

        if not info:
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail="No checkpoint found for this session"
            )

        if info.get("status") == "completed":
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail="Research already completed"
            )

        # 使用 V2 服务恢复
        service_v2 = get_research_service_v2()

        async def generate_sse():
            try:
                async for event in service_v2.research(
                    query=info.get("query", ""),
                    session_id=session_id,
                    resume=True
                ):
                    yield event
            except Exception as e:
                logger.error(f"Resume research error: {e}")
                error_event = serialize_event({"type": "error", "content": str(e)})
                yield f"data: {error_event}\n\n"

        return StreamingResponse(
            generate_sse(),
            media_type="text/event-stream"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to resume research: {e}")
        raise HTTPException(status_code=HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))