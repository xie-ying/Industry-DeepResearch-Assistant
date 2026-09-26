"""
DeepResearch Service - 深度研究服务 (ReAct 版本)

基于 ReAct (Reasoning + Acting) 架构的智能研究系统，具备：
1. 多工具智能调度 - 根据任务自动选择最佳工具组合
2. 思维链可视化 - 完整展示推理过程
3. 混合检索 - 网络搜索 + 本地知识库 + 数据库查询
4. 智能数据分析 - 自动识别数据并生成可视化
5. 图文混排输出 - 支持文字、图表、表格混合展示
"""

import requests
import json
from openai import OpenAI
import os
import time
import re
import asyncio
import hashlib
from typing import Dict, Any, AsyncGenerator, List, Optional, Tuple
from urllib.parse import urlparse
from collections import Counter
import logging

# --- Configuration ---
SEARCH_API_KEY = os.getenv("BOCHA_API_KEY", "Bearer sk-392ef5953eaa4c43be43e6daab4e82a4")
LLM_API_KEY = os.getenv("DASHSCOPE_API_KEY", "sk-f02db5a079ab41588b1cab09ad2777a2")
LLM_BASE_URL = os.getenv("DASHSCOPE_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")

# 优化配置
MAX_CONCURRENT_SEARCHES = 3
SEARCH_CACHE_TTL = 3600
CONTENT_SIMILARITY_THRESHOLD = 0.8

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- 搜索缓存 ---
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
    current_time = time.time()
    expired_keys = [k for k, (_, t) in _search_cache.items() if current_time - t > SEARCH_CACHE_TTL]
    for k in expired_keys:
        del _search_cache[k]


def compute_content_similarity(text1: str, text2: str) -> float:
    """计算两段文本的相似度"""
    if not text1 or not text2:
        return 0.0
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())
    if not words1 or not words2:
        return 0.0
    intersection = len(words1 & words2)
    union = len(words1 | words2)
    return intersection / union if union > 0 else 0.0


def is_content_duplicate(new_content: str, existing_contents: List[str], threshold: float = CONTENT_SIMILARITY_THRESHOLD) -> bool:
    """检查内容是否与已有内容重复"""
    for existing in existing_contents:
        if compute_content_similarity(new_content, existing) >= threshold:
            return True
    return False


def serialize_event(event_data: Dict[str, Any]) -> str:
    """将事件数据序列化为JSON字符串"""
    def json_serializer(obj):
        if isinstance(obj, set):
            return list(obj)
        if isinstance(obj, Exception):
            return str(obj)
        raise TypeError(f"Type {type(obj)} not serializable")

    try:
        return json.dumps(event_data, default=json_serializer, ensure_ascii=False)
    except Exception as e:
        logging.error(f"Failed to serialize event: {e}")
        return json.dumps({"type": "error", "content": f"Serialization error: {e}"})


# --- ResearchService Class ---
class ResearchService:
    """
    研究服务类 - ReAct 版本

    集成了：
    - ReAct 智能决策框架
    - 多工具协同调度
    - 智能数据分析
    - 可视化图表生成
    """

    def __init__(
        self,
        search_api_key: Optional[str] = None,
        llm_api_key: Optional[str] = None,
        llm_base_url: Optional[str] = None,
        db_connection_string: Optional[str] = None,
        use_react: bool = True
    ):
        """
        初始化研究服务

        Args:
            search_api_key: 搜索 API 密钥
            llm_api_key: LLM API 密钥
            llm_base_url: LLM API 基础 URL
            db_connection_string: 数据库连接字符串 (用于 Text2SQL)
            use_react: 是否使用 ReAct 模式
        """
        self.search_api_key = search_api_key or SEARCH_API_KEY
        self.llm_api_key = llm_api_key or LLM_API_KEY
        self.llm_base_url = llm_base_url or LLM_BASE_URL
        self.db_connection_string = db_connection_string
        self.use_react = use_react

        # 初始化 ReAct 组件
        if use_react:
            self._init_react_components()

    def _init_react_components(self):
        """初始化 ReAct 组件"""
        try:
            from service.react_controller import ReActController, create_default_tools
            from service.tool_executor import ToolExecutor, bind_tools_to_controller

            # 创建工具集
            tools = create_default_tools()

            # 创建 ReAct 控制器
            self.react_controller = ReActController(
                tools=tools,
                llm_api_key=self.llm_api_key,
                llm_base_url=self.llm_base_url,
                max_steps=10,
                model="qwen-max"
            )

            # 创建工具执行器
            self.tool_executor = ToolExecutor(
                search_api_key=self.search_api_key,
                llm_api_key=self.llm_api_key,
                llm_base_url=self.llm_base_url,
                db_connection_string=self.db_connection_string
            )

            # 绑定工具处理器
            bind_tools_to_controller(self.react_controller, self.tool_executor)

            logging.info("ReAct components initialized successfully")
        except Exception as e:
            logging.error(f"Failed to initialize ReAct components: {e}")
            self.use_react = False

    async def research_stream(
        self,
        query: str,
        max_iterations: int = 3,
        kb_name: Optional[str] = None,
        search_web: bool = True,
        search_local: bool = True
    ) -> AsyncGenerator[str, None]:
        """
        执行研究流程并以流式方式返回结果

        Args:
            query: 用户的研究问题
            max_iterations: 最大迭代次数
            kb_name: 本地知识库名称
            search_web: 是否搜索网络
            search_local: 是否搜索本地知识库

        Yields:
            序列化为JSON字符串的事件数据
        """
        if self.use_react:
            async for event in self._research_with_react(
                query, max_iterations, kb_name, search_web, search_local
            ):
                yield event
        else:
            async for event in self._research_classic(
                query, max_iterations, kb_name, search_web, search_local
            ):
                yield event

    async def _research_with_react(
        self,
        query: str,
        max_iterations: int,
        kb_name: Optional[str],
        search_web: bool,
        search_local: bool
    ) -> AsyncGenerator[str, None]:
        """使用 ReAct 架构执行研究"""
        yield serialize_event({
            "type": "status",
            "content": "启动 ReAct 智能研究引擎",
            "mode": "react"
        })

        # 准备初始上下文
        initial_context = {
            "kb_name": kb_name,
            "search_web": search_web,
            "search_local": search_local,
            "max_iterations": max_iterations
        }

        memory = []
        charts = []
        insights = []

        try:
            # 执行 ReAct 循环
            async for event in self.react_controller.run(query, initial_context):
                event_type = event.get("type", "")

                # 转发大部分事件到前端
                if event_type in ["react_start", "thinking_step", "thought", "action", "observation"]:
                    yield serialize_event(event)

                # 处理搜索结果
                if event_type == "search_result_item":
                    result = event.get("result", {})
                    memory.append(result)
                    yield serialize_event(event)

                # 处理图表
                if event_type == "chart":
                    charts.append(event)
                    yield serialize_event(event)

                # 处理数据洞察
                if event_type == "data_insight":
                    insights.extend(event.get("insights", []))
                    yield serialize_event(event)

                # ReAct 完成
                if event_type == "react_complete":
                    collected_data = event.get("collected_data", [])
                    if collected_data:
                        memory = collected_data

            # 生成最终报告
            if memory:
                async for report_event in self._generate_final_report(
                    query, memory, charts, insights
                ):
                    yield report_event
            else:
                yield serialize_event({
                    "type": "error",
                    "content": "未能收集到足够的研究信息"
                })

        except Exception as e:
            logging.error(f"ReAct research error: {e}")
            yield serialize_event({
                "type": "error",
                "content": f"研究过程出错: {str(e)}"
            })

    async def _research_classic(
        self,
        query: str,
        max_iterations: int,
        kb_name: Optional[str],
        search_web: bool,
        search_local: bool
    ) -> AsyncGenerator[str, None]:
        """经典研究模式 (保持向后兼容)"""
        memory = []
        processed_urls = set()
        current_subqueries = []
        all_subqueries_history = set()
        llm_system_prompt = f"你是一位专门的行业的资深研究助理。"

        sources = []
        if search_web:
            sources.append("网络")
        if search_local and kb_name:
            sources.append(f"知识库({kb_name})")

        yield serialize_event({
            "type": "status",
            "content": f"开始研究，数据源: {', '.join(sources) or '网络'}",
            "query": query
        })

        for iteration in range(max_iterations):
            yield serialize_event({"type": "status", "content": f"开始第 {iteration + 1} 次迭代"})

            # 规划子问题
            if iteration == 0:
                yield serialize_event({"type": "status", "content": "规划子问题..."})

                plan_prompt = f"""
请将以下用户的主要研究问题分解为具体的、可搜索的子问题列表。

分解要求：
1. 每个子问题应该是独立的、可直接用于搜索引擎的查询
2. 子问题应覆盖以下维度（根据问题性质选择适用的）：
   - 基本概念/定义
   - 现状/规模/数据
   - 发展趋势/变化
   - 主要参与者/案例
   - 问题/挑战
   - 解决方案/对策
   - 政策/法规
3. 生成 5-8 个子问题，确保全面但不重复
4. 子问题应简洁明确，适合搜索

请严格按照以下 JSON 格式输出：
{{
  "subqueries": [
    "子问题1",
    "子问题2",
    "子问题3"
  ]
}}

用户主要问题："{query}"
"""
                llm_response = await self._run_sync(
                    qwen_llm,
                    plan_prompt,
                    response_format={"type": "json_object"},
                    system_message_content=llm_system_prompt
                )

                if not llm_response:
                    current_subqueries = [query]
                else:
                    try:
                        plan_result = json.loads(llm_response)
                        current_subqueries = plan_result.get('subqueries', [])
                        if not current_subqueries:
                            current_subqueries = [query]
                        else:
                            yield serialize_event({"type": "subqueries", "content": current_subqueries})
                    except:
                        current_subqueries = [query]

            elif not current_subqueries:
                break

            # 过滤已搜索的子问题
            subqueries_to_search = [q for q in current_subqueries if q and q not in all_subqueries_history]

            # 执行搜索
            if subqueries_to_search:
                yield serialize_event({
                    "type": "status",
                    "content": f"并行搜索 {len(subqueries_to_search)} 个子问题..."
                })

                for sq in subqueries_to_search:
                    all_subqueries_history.add(sq)

                semaphore = asyncio.Semaphore(MAX_CONCURRENT_SEARCHES)
                search_results_list = await parallel_search_all(
                    subqueries_to_search,
                    semaphore,
                    kb_name=kb_name,
                    search_web=search_web,
                    search_local=search_local
                )

                existing_contents = [item['summary'] for item in memory]
                new_results_count = 0

                for item in search_results_list:
                    if len(item) == 3:
                        subquery, search_results, source = item
                    else:
                        subquery, search_results = item
                        source = 'web'

                    for result in search_results:
                        url = result.get('url')
                        summary = result.get('summary', '') or result.get('snippet', '')

                        if not url or not summary or url in processed_urls:
                            continue

                        if is_content_duplicate(summary, existing_contents):
                            continue

                        processed_urls.add(url)
                        existing_contents.append(summary)

                        memory.append({
                            "subquery": subquery,
                            "url": url,
                            "name": result.get('name', 'N/A'),
                            "summary": summary,
                            "snippet": result.get('snippet', ''),
                            "siteName": result.get('siteName', 'N/A'),
                            "siteIcon": result.get('siteIcon', 'N/A'),
                            "source": source
                        })
                        new_results_count += 1

                        yield serialize_event({
                            "type": "search_result_item",
                            "result": memory[-1]
                        })

                yield serialize_event({
                    "type": "status",
                    "content": f"本轮获取 {new_results_count} 条结果"
                })

            # 反思
            yield serialize_event({"type": "status", "content": "反思收集的信息..."})

            memory_context = ""
            if memory:
                context_items = []
                for item in memory[-20:]:
                    context_items.append(f"  - {item['subquery']}: {item['summary'][:200]}...")
                memory_context = "\n".join(context_items)

            reflection_prompt = f"""
评估为回答以下用户原始问题而收集的信息摘要。

用户原始问题："{query}"

目前收集到的信息摘要：
{memory_context or "当前没有收集到任何信息。"}

请评估：
1. can_answer: 这些信息是否足够回答用户的原始问题？(true/false)
2. new_subqueries: 还需要提出哪些新的子问题来填补信息空白？

请严格按照以下 JSON 格式响应：
{{
    "can_answer": boolean,
    "new_subqueries": ["新问题1", "新问题2", ...]
}}
"""
            llm_response = await self._run_sync(
                qwen_llm,
                reflection_prompt,
                response_format={"type": "json_object"},
                system_message_content=llm_system_prompt
            )

            can_answer = False
            current_subqueries = []

            if llm_response:
                try:
                    reflection_result = json.loads(llm_response)
                    can_answer = reflection_result.get('can_answer', False)
                    current_subqueries = reflection_result.get('new_subqueries', [])

                    yield serialize_event({
                        "type": "reflection",
                        "can_answer": can_answer,
                        "new_subqueries_count": len(current_subqueries)
                    })

                    if can_answer:
                        yield serialize_event({
                            "type": "status",
                            "content": "信息足够，结束迭代"
                        })
                        break

                    if current_subqueries:
                        yield serialize_event({
                            "type": "new_subqueries",
                            "content": current_subqueries
                        })
                except Exception as e:
                    logging.error(f"Reflection error: {e}")

            if iteration == max_iterations - 1:
                yield serialize_event({
                    "type": "status",
                    "content": "达到最大迭代次数"
                })

        # 生成最终报告
        if memory:
            async for report_event in self._generate_final_report(query, memory, [], []):
                yield report_event
        else:
            yield serialize_event({
                "type": "error",
                "content": "未能收集到任何信息"
            })
            yield serialize_event({
                "type": "final_answer",
                "content": "未能生成报告，因为没有收集到相关信息。"
            })

    async def _generate_final_report(
        self,
        query: str,
        memory: List[Dict],
        charts: List[Dict],
        insights: List[str]
    ) -> AsyncGenerator[str, None]:
        """生成最终研究报告"""
        yield serialize_event({"type": "status", "content": "开始生成最终报告..."})

        # 为每个内存项添加编号
        for index, item in enumerate(memory):
            item['reference_id'] = index + 1

        # 返回参考资料
        yield serialize_event({
            "type": "reference_materials",
            "content": memory
        })

        # 构建上下文
        final_memory_context = "\n\n".join([
            f"引用编号 {item['reference_id']}\n来源 URL: {item['url']}\n标题: {item.get('name', 'N/A')}\n内容摘要: {item['summary']}"
            for item in memory
        ])

        # 洞察摘要
        insights_section = ""
        if insights:
            insights_section = f"\n\n数据分析洞察:\n" + "\n".join([f"- {i}" for i in insights])

        # 图表说明
        charts_section = ""
        if charts:
            charts_section = f"\n\n已生成 {len(charts)} 个数据可视化图表，请在报告中适当引用。"

        synthesis_prompt = f"""
您是一位专业的行业研究员。请基于以下收集到的信息，为用户生成一份全面、结构清晰的中文研究报告。

用户的原始问题是："{query}"

以下是收集到的相关信息：
--- 开始收集的信息 ---
{final_memory_context}
--- 结束收集的信息 ---
{insights_section}
{charts_section}

请严格遵守以下要求撰写报告：
1. 完全基于上面提供的"收集到的信息"来撰写，不得添加外部知识。
2. 清晰、有条理地组织报告内容，直接回答用户的原始问题。
3. 在报告中必须引用信息来源。当您使用某条信息时，请用格式注明：##引用编号$$
   例如：安责险的保费规模近年来持续增长 ##2$$
4. 如果提供了"数据分析洞察"，请将分析结果自然地融入报告内容中。
5. 语言专业、客观、简洁。
6. 如果信息存在矛盾，请客观指出。
7. 如果信息不足以回答问题的某些方面，请在报告中说明。

请开始撰写您的研究报告：
"""

        yield serialize_event({"type": "thinking_start"})

        client = OpenAI(
            api_key=self.llm_api_key,
            base_url=self.llm_base_url,
        )

        reasoning_content = ""
        answer_content = ""
        is_answering = False

        try:
            stream = await self._run_sync(
                lambda: client.chat.completions.create(
                    model="deepseek-r1",
                    messages=[
                        {'role': 'system', 'content': 'You are an expert research assistant.'},
                        {'role': 'user', 'content': synthesis_prompt}
                    ],
                    stream=True
                )
            )

            async for chunk in self._process_stream(stream):
                if not getattr(chunk, 'choices', None):
                    continue

                delta = chunk.choices[0].delta

                if not hasattr(delta, 'reasoning_content'):
                    continue

                if not getattr(delta, 'reasoning_content', None) and not getattr(delta, 'content', None):
                    continue

                if not getattr(delta, 'reasoning_content', None) and not is_answering:
                    is_answering = True
                    yield serialize_event({"type": "thinking_end"})
                    yield serialize_event({"type": "answer_start"})

                if getattr(delta, 'reasoning_content', None):
                    reasoning_content += delta.reasoning_content
                    yield serialize_event({"type": "thinking", "content": delta.reasoning_content})
                elif getattr(delta, 'content', None):
                    answer_content += delta.content
                    yield serialize_event({"type": "answer", "content": delta.content})

            yield serialize_event({"type": "answer_end"})

            # 返回图表数据
            for chart in charts:
                yield serialize_event(chart)

            yield serialize_event({"type": "complete"})

        except Exception as e:
            logging.error(f"Report generation error: {e}")
            yield serialize_event({"type": "error", "content": f"报告生成出错: {str(e)}"})

    @staticmethod
    async def _run_sync(func, *args, **kwargs):
        """运行同步函数"""
        return await asyncio.to_thread(func, *args, **kwargs)

    @staticmethod
    async def _process_stream(stream):
        """处理流式响应"""
        for chunk in stream:
            yield chunk
            await asyncio.sleep(0)


# --- Helper Functions ---

async def parallel_search_all(
    subqueries: List[str],
    semaphore: asyncio.Semaphore,
    kb_name: Optional[str] = None,
    search_web: bool = True,
    search_local: bool = True
) -> List[Tuple[str, List, str]]:
    """并行搜索网络和本地知识库"""
    all_results = []

    async def search_web_with_semaphore(query: str) -> Tuple[str, List, str]:
        async with semaphore:
            cached = get_cached_search(query)
            if cached is not None:
                return (query, cached, 'web')
            results = await asyncio.to_thread(websearch, query)
            set_cached_search(query, results)
            await asyncio.sleep(0.5)
            return (query, results, 'web')

    async def search_local_with_semaphore(query: str) -> Tuple[str, List, str]:
        async with semaphore:
            results = await search_local_knowledge(query, kb_name, top_k=3)
            return (query, results, 'local')

    tasks = []
    for q in subqueries:
        if not q:
            continue
        if search_web:
            tasks.append(search_web_with_semaphore(q))
        if search_local and kb_name:
            tasks.append(search_local_with_semaphore(q))

    results = await asyncio.gather(*tasks, return_exceptions=True)

    for r in results:
        if isinstance(r, Exception):
            logging.error(f"Search error: {r}")
        else:
            all_results.append(r)

    return all_results


async def search_local_knowledge(query: str, kb_name: str, top_k: int = 5) -> List[Dict]:
    """搜索本地知识库"""
    try:
        from service.retrieval_service import retrieve_from_knowledge_base
        results = await asyncio.to_thread(
            retrieve_from_knowledge_base,
            kb_name=kb_name,
            question=query,
            top_k=top_k
        )

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
        logging.error(f"Local knowledge search error: {e}")
        return []


def websearch(query, count=5):
    """执行网络搜索"""
    url = "https://api.bochaai.com/v1/web-search"
    payload = json.dumps({
        "query": query,
        "summary": True,
        "count": count,
        "page": 1
    })
    headers = {
        'Authorization': SEARCH_API_KEY,
        'Content-Type': 'application/json'
    }

    try:
        response = requests.post(url, headers=headers, data=payload, timeout=25)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        logging.error(f"Web search error for '{query}': {e}")
        return []

    webpages_data = data.get('data', {}).get('webPages', {})
    value_list = webpages_data.get('value')

    if value_list is None or not isinstance(value_list, list):
        return []

    return [
        item for item in value_list
        if item.get('url') and (item.get('snippet') or item.get('summary'))
    ]


def qwen_llm(prompt, model="qwen-max", response_format=None, system_message_content="You are a helpful assistant."):
    """调用 Qwen LLM"""
    logging.info(f"Calling Qwen LLM: {prompt[:100]}...")
    try:
        client = OpenAI(api_key=LLM_API_KEY, base_url=LLM_BASE_URL)

        completion_args = {
            "model": model,
            "messages": [
                {'role': 'system', 'content': system_message_content},
                {'role': 'user', 'content': prompt}
            ],
            "temperature": 0.2,
        }
        if response_format:
            completion_args["response_format"] = response_format

        completion = client.chat.completions.create(**completion_args)
        return completion.choices[0].message.content
    except Exception as e:
        logging.error(f"Error calling Qwen LLM: {e}")
        return None
