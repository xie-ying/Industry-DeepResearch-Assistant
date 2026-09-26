"""
Tool Executor - 工具执行器

实现 ReAct 框架中各种工具的具体执行逻辑，包括：
1. Web Search - 网络搜索
2. Knowledge Search - 本地知识库搜索
3. Text2SQL - 自然语言转 SQL
4. Data Analyzer - 智能数据分析
5. Chart Generator - 图表配置生成
"""

import json
import logging
import asyncio
import hashlib
import time
import re
from typing import Dict, Any, List, Optional, Callable, Tuple
from collections import Counter
import requests
from openai import OpenAI

from .react_controller import ReActContext, ToolType, Tool

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- 缓存配置 ---
SEARCH_CACHE_TTL = 3600  # 搜索缓存过期时间(秒)
_search_cache: Dict[str, Tuple[List, float]] = {}


def get_query_hash(query: str) -> str:
    """生成查询的哈希值用于缓存"""
    return hashlib.md5(query.strip().lower().encode()).hexdigest()


def get_cached_search(query: str) -> Optional[List]:
    """获取缓存的搜索结果"""
    query_hash = get_query_hash(query)
    if query_hash in _search_cache:
        results, timestamp = _search_cache[query_hash]
        if time.time() - timestamp < SEARCH_CACHE_TTL:
            logging.info(f"Cache hit for query: {query[:50]}...")
            return results
        else:
            del _search_cache[query_hash]
    return None


def set_cached_search(query: str, results: List):
    """缓存搜索结果"""
    query_hash = get_query_hash(query)
    _search_cache[query_hash] = (results, time.time())
    # 清理过期缓存
    current_time = time.time()
    expired_keys = [k for k, (_, t) in _search_cache.items() if current_time - t > SEARCH_CACHE_TTL]
    for k in expired_keys:
        del _search_cache[k]


class ToolExecutor:
    """
    工具执行器 - 统一管理和执行各类工具

    Features:
    - 统一的工具执行接口
    - 内置缓存机制
    - 错误处理和重试
    - 支持自定义工具扩展
    """

    def __init__(
        self,
        search_api_key: str,
        llm_api_key: str,
        llm_base_url: str,
        db_connection_string: Optional[str] = None
    ):
        """
        初始化工具执行器

        Args:
            search_api_key: 搜索 API 密钥
            llm_api_key: LLM API 密钥
            llm_base_url: LLM API 基础 URL
            db_connection_string: 数据库连接字符串 (用于 Text2SQL)
        """
        self.search_api_key = search_api_key
        self.llm_api_key = llm_api_key
        self.llm_base_url = llm_base_url
        self.db_connection_string = db_connection_string
        self.llm_client = OpenAI(api_key=llm_api_key, base_url=llm_base_url)

        # 注册工具处理器
        self.handlers: Dict[str, Callable] = {
            ToolType.WEB_SEARCH.value: self.execute_web_search,
            ToolType.KNOWLEDGE_SEARCH.value: self.execute_knowledge_search,
            ToolType.TEXT2SQL.value: self.execute_text2sql,
            ToolType.DATA_ANALYZER.value: self.execute_data_analyzer,
            ToolType.CHART_GENERATOR.value: self.execute_chart_generator,
            ToolType.STOCK_QUERY.value: self.execute_stock_query,
            ToolType.BIDDING_SEARCH.value: self.execute_bidding_search,
            ToolType.FINISH.value: self.execute_finish,
        }

    def get_handler(self, tool_name: str) -> Optional[Callable]:
        """获取工具处理器"""
        return self.handlers.get(tool_name)

    async def execute(self, tool_name: str, params: Dict[str, Any], context: ReActContext) -> Any:
        """
        执行指定工具

        Args:
            tool_name: 工具名称
            params: 工具参数
            context: ReAct 上下文

        Returns:
            工具执行结果
        """
        handler = self.handlers.get(tool_name)
        if not handler:
            raise ValueError(f"Unknown tool: {tool_name}")

        return await handler(params, context)

    # ========== Web Search ==========
    async def execute_web_search(self, params: Dict[str, Any], context: ReActContext) -> List[Dict]:
        """
        执行网络搜索

        Args:
            params: {"query": str, "count": int}
            context: ReAct 上下文

        Returns:
            搜索结果列表
        """
        query = params.get('query', '')
        count = params.get('count', 5)

        # 如果 query 为空，尝试从上下文的原始查询中提取关键词作为备选
        if not query:
            logging.warning(f"web_search called with empty query, using context query as fallback")
            # 使用用户原始问题作为搜索关键词
            query = context.query
            if not query:
                logging.error("No query available for web_search")
                return []
            logging.info(f"Using fallback query: {query}")

        # 检查缓存
        cached = get_cached_search(query)
        if cached is not None:
            return cached

        # 执行搜索
        results = await asyncio.to_thread(self._websearch_sync, query, count)

        # 缓存结果
        set_cached_search(query, results)

        return results

    def _websearch_sync(self, query: str, count: int = 5) -> List[Dict]:
        """同步执行网络搜索"""
        url = "https://api.bochaai.com/v1/web-search"
        payload = json.dumps({
            "query": query,
            "summary": True,
            "count": count,
            "page": 1
        })
        headers = {
            'Authorization': self.search_api_key,
            'Content-Type': 'application/json'
        }

        try:
            response = requests.post(url, headers=headers, data=payload, timeout=25)
            response.raise_for_status()
            data = response.json()

            webpages_data = data.get('data', {}).get('webPages', {})
            value_list = webpages_data.get('value', [])

            if not isinstance(value_list, list):
                return []

            # 过滤和格式化结果
            results = []
            for item in value_list:
                if item.get('url') and (item.get('snippet') or item.get('summary')):
                    results.append({
                        'url': item.get('url'),
                        'name': item.get('name', 'N/A'),
                        'summary': item.get('summary', '') or item.get('snippet', ''),
                        'snippet': item.get('snippet', ''),
                        'siteName': item.get('siteName', 'N/A'),
                        'siteIcon': item.get('siteIcon', ''),
                        'source': 'web'
                    })

            return results

        except Exception as e:
            logging.error(f"Web search error for '{query}': {e}")
            return []

    # ========== Knowledge Search ==========
    async def execute_knowledge_search(self, params: Dict[str, Any], context: ReActContext) -> List[Dict]:
        """
        执行本地知识库搜索

        Args:
            params: {"query": str, "kb_name": str, "top_k": int}
            context: ReAct 上下文

        Returns:
            搜索结果列表
        """
        query = params.get('query', '')
        kb_name = params.get('kb_name', context.metadata.get('kb_name', ''))
        top_k = params.get('top_k', 5)

        if not query or not kb_name:
            return []

        try:
            from service.retrieval_service import retrieve_from_knowledge_base
            results = await asyncio.to_thread(
                retrieve_from_knowledge_base,
                kb_name=kb_name,
                question=query,
                top_k=top_k
            )

            # 转换为统一格式
            formatted_results = []
            for r in results:
                formatted_results.append({
                    'url': f"local://{kb_name}/{r.get('document_id', 'unknown')}",
                    'name': r.get('document_name', 'N/A'),
                    'summary': r.get('content_with_weight', ''),
                    'snippet': r.get('content_with_weight', '')[:200] if r.get('content_with_weight') else '',
                    'siteName': f"知识库: {kb_name}",
                    'siteIcon': '',
                    'source': 'local'
                })

            return formatted_results

        except Exception as e:
            logging.error(f"Knowledge search error: {e}")
            return []

    # ========== Text2SQL ==========
    async def execute_text2sql(self, params: Dict[str, Any], context: ReActContext) -> Dict[str, Any]:
        """
        执行 Text2SQL 查询

        Args:
            params: {"question": str, "intent": str}
            context: ReAct 上下文

        Returns:
            查询结果
        """
        question = params.get('question', '')
        intent = params.get('intent', 'stats')

        if not question:
            return {"success": False, "error": "问题不能为空"}

        # 动态导入 Text2SQL 服务
        try:
            from service.text2sql_service import Text2SQLService
            text2sql = Text2SQLService(
                llm_api_key=self.llm_api_key,
                llm_base_url=self.llm_base_url,
                db_connection_string=self.db_connection_string
            )
            result = await text2sql.query(question, intent)
            return result
        except ImportError:
            logging.warning("Text2SQL service not available")
            return {
                "success": False,
                "error": "Text2SQL 服务尚未配置",
                "data": []
            }
        except Exception as e:
            logging.error(f"Text2SQL error: {e}")
            return {
                "success": False,
                "error": str(e),
                "data": []
            }

    # ========== Data Analyzer ==========
    async def execute_data_analyzer(self, params: Dict[str, Any], context: ReActContext) -> Dict[str, Any]:
        """
        执行智能数据分析

        Args:
            params: {"data": list, "analysis_type": str}
            context: ReAct 上下文

        Returns:
            分析结果，包含统计数据和洞察
        """
        # 如果没有提供数据，使用上下文中收集的数据
        data = params.get('data') or context.collected_data
        analysis_type = params.get('analysis_type', 'auto')

        if not data:
            return {
                "success": False,
                "error": "没有可分析的数据",
                "insights": [],
                "statistics": {}
            }

        # 动态导入智能分析器
        try:
            from service.smart_analyzer import SmartDataAnalyzer
            analyzer = SmartDataAnalyzer()
            result = await asyncio.to_thread(analyzer.analyze, data, analysis_type)
            return result
        except ImportError:
            # 如果智能分析器不可用，使用简化版本
            return await self._simple_data_analysis(data)

    async def _simple_data_analysis(self, data: List) -> Dict[str, Any]:
        """简化版数据分析"""
        # 提取文本内容
        texts = []
        for item in data:
            if isinstance(item, dict):
                texts.append(item.get('summary', '') or item.get('content', ''))
            else:
                texts.append(str(item))

        full_text = " ".join(texts)

        # 提取数值
        numbers = []
        percentages = []

        # 货币数值
        currency_pattern = re.compile(r'(\d{1,3}(?:,\d{3})*(?:\.\d+)?|\d+(?:\.\d+)?)\s*(?:元|万|亿|人民币|美元)')
        currency_values = currency_pattern.findall(full_text)
        numbers.extend([float(val.replace(',', '')) for val in currency_values if val])

        # 百分比
        percentage_pattern = re.compile(r'(\d+(?:\.\d+)?)\s*%')
        perc_values = percentage_pattern.findall(full_text)
        percentages.extend([float(p) for p in perc_values])

        # 关键词统计
        keywords = Counter()
        relevant_keywords = ['保险', '保费', '赔付', '风险', '市场', '增长', '下降', '趋势', '规模', '占比']
        for keyword in relevant_keywords:
            count = full_text.lower().count(keyword.lower())
            if count > 0:
                keywords[keyword] = count

        # 生成洞察
        insights = []
        statistics = {}

        if numbers:
            statistics['numbers'] = {
                'count': len(numbers),
                'avg': round(sum(numbers) / len(numbers), 2),
                'min': round(min(numbers), 2),
                'max': round(max(numbers), 2)
            }
            insights.append(f"发现 {len(numbers)} 个数值数据，平均值 {statistics['numbers']['avg']}")

        if percentages:
            statistics['percentages'] = {
                'count': len(percentages),
                'avg': round(sum(percentages) / len(percentages), 2),
                'min': round(min(percentages), 2),
                'max': round(max(percentages), 2)
            }
            insights.append(f"发现 {len(percentages)} 个百分比数据，范围 {statistics['percentages']['min']}% - {statistics['percentages']['max']}%")

        if keywords:
            top_keywords = keywords.most_common(5)
            statistics['keywords'] = dict(top_keywords)
            insights.append(f"高频关键词: {', '.join([f'{k}({v})' for k, v in top_keywords])}")

        # 推荐可视化类型
        visualization_hint = "table"
        if len(numbers) >= 3:
            visualization_hint = "bar"
        if percentages and len(percentages) >= 2:
            visualization_hint = "pie"

        return {
            "success": True,
            "insights": insights,
            "statistics": statistics,
            "visualization_hint": visualization_hint,
            "data_points": len(data)
        }

    # ========== Chart Generator ==========
    async def execute_chart_generator(self, params: Dict[str, Any], context: ReActContext) -> Dict[str, Any]:
        """
        生成图表配置

        Args:
            params: {"data": dict/list, "chart_type": str, "title": str}
            context: ReAct 上下文

        Returns:
            ECharts 兼容的图表配置
        """
        data = params.get('data', {})
        chart_type = params.get('chart_type', 'bar')
        title = params.get('title', '数据分析图表')

        try:
            from service.chart_generator import ChartGenerator
            generator = ChartGenerator()
            config = generator.generate(data, chart_type, title)
            return config
        except ImportError:
            # 如果图表生成器不可用，使用简化版本
            return self._simple_chart_config(data, chart_type, title)

    def _simple_chart_config(self, data: Any, chart_type: str, title: str) -> Dict[str, Any]:
        """简化版图表配置生成"""
        # 准备数据
        x_data = []
        y_data = []

        if isinstance(data, dict):
            x_data = list(data.keys())
            y_data = list(data.values())
        elif isinstance(data, list):
            if all(isinstance(item, dict) for item in data):
                # [{name: x, value: y}, ...]
                x_data = [item.get('name', f'项目{i}') for i, item in enumerate(data)]
                y_data = [item.get('value', 0) for item in data]
            else:
                # [value1, value2, ...]
                x_data = [f'项目{i+1}' for i in range(len(data))]
                y_data = data

        # 生成基础配置
        base_config = {
            "type": chart_type,
            "title": title,
            "data": {
                "xAxis": x_data,
                "series": [{"name": "数值", "data": y_data}]
            },
            "options": {
                "tooltip": {"trigger": "axis" if chart_type == "line" else "item"},
                "legend": {"show": True},
                "grid": {"left": "3%", "right": "4%", "bottom": "3%", "containLabel": True}
            }
        }

        # 根据图表类型调整
        if chart_type == "pie":
            base_config["data"] = {
                "series": [{
                    "name": title,
                    "data": [{"name": x, "value": y} for x, y in zip(x_data, y_data)]
                }]
            }
            base_config["options"]["tooltip"] = {"trigger": "item"}

        return base_config

    # ========== Stock Query ==========
    async def execute_stock_query(self, params: Dict[str, Any], context: ReActContext) -> Dict[str, Any]:
        """
        执行股票查询

        Args:
            params: {"stock_code": str} 或 {"keyword": str}
            context: ReAct 上下文

        Returns:
            股票信息
        """
        stock_code = params.get('stock_code', '')
        keyword = params.get('keyword', '')

        try:
            from service.stock_service import get_stock_service
            stock_service = get_stock_service()

            if stock_code:
                result = await stock_service.get_stock_by_code(stock_code)
            elif keyword:
                result = await stock_service.search_stock(keyword)
            else:
                return {
                    "success": False,
                    "error": "请提供股票代码或关键词",
                    "data": None
                }

            if result.get("success"):
                # 将结果添加到上下文
                context.collected_data.append({
                    "source": "stock_api",
                    "type": "stock_info",
                    "data": result.get("data") or result.get("results", [])
                })

            return result

        except ImportError:
            logging.warning("Stock service not available")
            return {
                "success": False,
                "error": "股票查询服务尚未配置",
                "data": None
            }
        except Exception as e:
            logging.error(f"Stock query error: {e}")
            return {
                "success": False,
                "error": str(e),
                "data": None
            }

    # ========== Bidding Search ==========
    async def execute_bidding_search(self, params: Dict[str, Any], context: ReActContext) -> Dict[str, Any]:
        """
        执行招投标信息搜索

        Args:
            params: {"keyword": str, "category": str, "region": str, "page": int}
            context: ReAct 上下文

        Returns:
            招投标信息列表
        """
        keyword = params.get('keyword', '')
        category = params.get('category')  # 招标/中标/采购
        region = params.get('region')  # 地区
        page = params.get('page', 1)

        if not keyword:
            return {
                "success": False,
                "error": "请提供搜索关键词",
                "results": [],
                "total": 0
            }

        try:
            from service.bidding_service import get_bidding_service
            bidding_service = get_bidding_service()

            result = await bidding_service.search_bids(
                keyword=keyword,
                category=category,
                region=region,
                page=page
            )

            if result.get("success"):
                # 将结果添加到上下文
                context.collected_data.append({
                    "source": "bidding_api",
                    "type": "bidding_info",
                    "data": result.get("results", [])
                })

            return result

        except ImportError:
            logging.warning("Bidding service not available")
            return {
                "success": False,
                "error": "招投标查询服务尚未配置",
                "results": [],
                "total": 0
            }
        except Exception as e:
            logging.error(f"Bidding search error: {e}")
            return {
                "success": False,
                "error": str(e),
                "results": [],
                "total": 0
            }

    # ========== Finish ==========
    async def execute_finish(self, params: Dict[str, Any], context: ReActContext) -> Dict[str, Any]:
        """
        完成研究，返回总结

        Args:
            params: {"summary": str}
            context: ReAct 上下文

        Returns:
            完成状态
        """
        summary = params.get('summary', '')

        return {
            "status": "finished",
            "summary": summary,
            "total_data_collected": len(context.collected_data),
            "total_insights": len(context.insights),
            "total_charts": len(context.charts)
        }


def create_tool_executor(
    search_api_key: str,
    llm_api_key: str,
    llm_base_url: str,
    db_connection_string: Optional[str] = None
) -> ToolExecutor:
    """
    创建工具执行器的工厂函数

    Args:
        search_api_key: 搜索 API 密钥
        llm_api_key: LLM API 密钥
        llm_base_url: LLM API 基础 URL
        db_connection_string: 数据库连接字符串

    Returns:
        配置好的 ToolExecutor 实例
    """
    return ToolExecutor(
        search_api_key=search_api_key,
        llm_api_key=llm_api_key,
        llm_base_url=llm_base_url,
        db_connection_string=db_connection_string
    )


def bind_tools_to_controller(controller, executor: ToolExecutor):
    """
    将工具执行器绑定到 ReAct 控制器

    Args:
        controller: ReActController 实例
        executor: ToolExecutor 实例
    """
    for tool_name, handler in executor.handlers.items():
        controller.update_tool_handler(tool_name, handler)
