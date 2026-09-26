from fastapi import APIRouter, Depends, HTTPException
from starlette.status import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_500_INTERNAL_SERVER_ERROR

from service import WebSearchService, ServiceConfig
from schemas import WebSearchRequest, WebSearchResponse

# Create router instance
router = APIRouter(prefix="/search", tags=["search"])

# Get WebSearchService instance
def get_web_search_service():
    config = ServiceConfig.get_api_config()
    api_key = config.get('serper_api_key', None)
    return WebSearchService(api_key=api_key)

@router.post("/web", status_code=HTTP_200_OK, response_model=WebSearchResponse)
async def web_search(
    request: WebSearchRequest,
    search_service: WebSearchService = Depends(get_web_search_service)
):
    """
    执行Web搜索，返回搜索结果。
    
    Args:
        request: 包含搜索参数的请求体
        
    Returns:
        搜索结果响应
    """
    try:
        # 调用搜索服务
        search_results = search_service.search(
            query=request.query,
            gl=request.gl,
            hl=request.hl,
            autocorrect=request.autocorrect,
            page=request.page,
            search_type=request.search_type
        )
        
        # 检查是否有错误
        if "error" in search_results and search_results["error"]:
            return {
                "success": False,
                "message": search_results.get("message", "Search failed"),
                "query": request.query,
                "results": []
            }
        
        # 提取并格式化搜索结果
        formatted_results = search_service.extract_search_results(search_results)
        
        # 构建响应
        return {
            "success": True,
            "query": request.query,
            "results": formatted_results,
            "raw_results": search_results
        }
        
    except Exception as e:
        # 处理异常
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error performing web search: {str(e)}"
        ) 