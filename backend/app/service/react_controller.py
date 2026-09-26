"""
ReAct Controller - Reasoning + Acting 循环决策框架

实现了业界领先的 ReAct 范式，优化版流程：
1. Plan (规划) - LLM 分解问题，生成多个搜索子查询
2. Execute (执行) - 并行执行所有搜索任务
3. Reflect (反思) - 评估信息是否充足，决定是否补充搜索
4. Synthesize (综合) - 整合信息，生成最终报告

核心优化：
- 子查询由 LLM 智能生成，而非简单使用原始问题
- 支持并行执行多个搜索，大幅提升效率
- 迭代式深入，直到信息充足
"""

import json
import logging
import asyncio
import re
from typing import Dict, Any, List, Optional, AsyncGenerator, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
from openai import OpenAI

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')


class ToolType(Enum):
    """工具类型枚举"""
    WEB_SEARCH = "web_search"
    KNOWLEDGE_SEARCH = "knowledge_search"
    TEXT2SQL = "text2sql"
    DATA_ANALYZER = "data_analyzer"
    CHART_GENERATOR = "chart_generator"
    STOCK_QUERY = "stock_query"
    BIDDING_SEARCH = "bidding_search"
    FINISH = "finish"


@dataclass
class Tool:
    """工具定义"""
    name: str
    description: str
    parameters: Dict[str, str]
    handler: Optional[Callable] = None

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters
        }


@dataclass
class Action:
    """动作定义"""
    tool: str
    params: Dict[str, Any]

    @classmethod
    def from_dict(cls, data: Dict) -> 'Action':
        return cls(
            tool=data.get('tool', ''),
            params=data.get('params', {})
        )


@dataclass
class Thought:
    """思考结果"""
    reasoning: str  # 推理过程
    should_finish: bool  # 是否应该结束
    next_action: Optional[Action] = None  # 下一步动作
    confidence: float = 0.0  # 置信度


@dataclass
class Observation:
    """观察结果"""
    tool: str
    success: bool
    result: Any
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SubQuery:
    """子查询定义"""
    query: str  # 搜索关键词
    purpose: str  # 查询目的
    tool: str  # 使用的工具 (web_search / knowledge_search)
    priority: int = 1  # 优先级 1-3


@dataclass
class ResearchPlan:
    """研究计划"""
    understanding: str  # 对问题的理解
    sub_queries: List[SubQuery]  # 子查询列表
    strategy: str  # 研究策略说明
    expected_aspects: List[str]  # 预期覆盖的方面


@dataclass
class ReActStep:
    """ReAct 单步记录"""
    step: int
    thought: Thought
    action: Optional[Action]
    observation: Optional[Observation]


class ReActContext:
    """ReAct 上下文管理"""

    def __init__(self, query: str):
        self.query = query
        self.steps: List[ReActStep] = []
        self.observations: List[Observation] = []
        self.collected_data: List[Dict] = []  # 收集的数据
        self.insights: List[str] = []  # 发现的洞察
        self.charts: List[Dict] = []  # 生成的图表
        self.metadata: Dict[str, Any] = {}
        self.plan: Optional[ResearchPlan] = None  # 研究计划
        self.executed_queries: List[str] = []  # 已执行的查询
        self.iteration: int = 0  # 当前迭代轮次

    def add_step(self, step: ReActStep):
        self.steps.append(step)

    def add_observation(self, obs: Observation):
        self.observations.append(obs)

        # 如果是搜索结果，加入收集的数据
        if obs.tool in [ToolType.WEB_SEARCH.value, ToolType.KNOWLEDGE_SEARCH.value]:
            if obs.success and isinstance(obs.result, list):
                self.collected_data.extend(obs.result)

        # 如果是数据分析结果，记录洞察
        if obs.tool == ToolType.DATA_ANALYZER.value and obs.success:
            if isinstance(obs.result, dict) and 'insights' in obs.result:
                self.insights.extend(obs.result['insights'])

        # 如果是图表，记录
        if obs.tool == ToolType.CHART_GENERATOR.value and obs.success:
            self.charts.append(obs.result)

    def get_history_summary(self, max_items: int = 10) -> str:
        """获取历史摘要"""
        if not self.steps:
            return "尚未执行任何步骤。"

        summary_parts = []
        for step in self.steps[-max_items:]:
            step_summary = f"步骤 {step.step}:\n"
            step_summary += f"  思考: {step.thought.reasoning[:200]}...\n"
            if step.action:
                step_summary += f"  动作: {step.action.tool}({json.dumps(step.action.params, ensure_ascii=False)[:100]})\n"
            if step.observation:
                result_str = str(step.observation.result)[:200] if step.observation.result else "无结果"
                step_summary += f"  观察: {'成功' if step.observation.success else '失败'} - {result_str}\n"
            summary_parts.append(step_summary)

        return "\n".join(summary_parts)

    def get_collected_data_summary(self, max_items: int = 20) -> str:
        """获取收集数据摘要"""
        if not self.collected_data:
            return "尚未收集到数据。"

        summaries = []
        for i, item in enumerate(self.collected_data[:max_items]):
            if isinstance(item, dict):
                title = item.get('name', item.get('title', 'N/A'))
                content = item.get('summary', item.get('content', ''))[:150]
                source = item.get('source', 'unknown')
                summaries.append(f"[{i+1}] ({source}) {title}: {content}...")
            else:
                summaries.append(f"[{i+1}] {str(item)[:200]}...")

        return "\n".join(summaries)


class ReActController:
    """
    ReAct 控制器 - 核心推理引擎

    优化版流程：Plan -> Execute (并行) -> Reflect -> Synthesize
    """

    # ========== Plan 阶段 Prompt ==========
    PLAN_PROMPT = """你是一个专业的行业研究助手。请分析用户问题，制定研究计划并生成多个搜索子查询。

## 用户问题
{query}

## 任务要求
1. 深入理解用户问题的核心需求
2. 将问题分解为多个可搜索的子问题
3. 为每个子问题生成精准的搜索关键词
4. 确保子查询覆盖问题的各个方面

## 响应格式
请严格按照以下 JSON 格式响应：
```json
{{
    "understanding": "对用户问题的理解和分析",
    "sub_queries": [
        {{
            "query": "搜索关键词1（精准、具体）",
            "purpose": "这个查询的目的",
            "tool": "web_search",
            "priority": 1
        }},
        {{
            "query": "搜索关键词2",
            "purpose": "这个查询的目的",
            "tool": "web_search",
            "priority": 1
        }},
        {{
            "query": "搜索关键词3",
            "purpose": "这个查询的目的",
            "tool": "knowledge_search",
            "priority": 2
        }}
    ],
    "strategy": "整体研究策略说明",
    "expected_aspects": ["方面1", "方面2", "方面3"]
}}
```

## 子查询生成原则
1. 每个 query 必须是具体的搜索关键词，不能是问句
2. 生成 3-6 个不同角度的子查询
3. 关键词要精准，避免过于宽泛
4. 优先级：1=核心必需，2=重要补充，3=扩展了解
5. tool 选择：web_search 用于网络搜索，knowledge_search 用于本地知识库

## 示例
用户问题："新能源汽车市场现状和发展趋势"
好的子查询：
- "2024年中国新能源汽车销量数据"
- "新能源汽车市场份额排名"
- "新能源汽车行业政策补贴"
- "电动汽车技术发展趋势"
- "新能源汽车企业竞争格局"

请开始分析："""

    # ========== Reflect 阶段 Prompt ==========
    REFLECT_PROMPT = """你是一个专业的研究助手。请评估当前收集的信息是否足够回答用户问题。

## 用户原始问题
{query}

## 研究计划预期覆盖的方面
{expected_aspects}

## 已收集的信息摘要
{collected_summary}

## 已执行的搜索查询
{executed_queries}

## 任务要求
评估当前信息的完整性，决定是否需要补充搜索。

## 响应格式
```json
{{
    "coverage_analysis": "对信息覆盖度的分析",
    "missing_aspects": ["缺失的方面1", "缺失的方面2"],
    "is_sufficient": true或false,
    "additional_queries": [
        {{
            "query": "补充搜索关键词",
            "purpose": "补充搜索的目的",
            "tool": "web_search"
        }}
    ],
    "confidence": 0.8
}}
```

注意：
- 如果信息已足够，设置 is_sufficient 为 true，additional_queries 为空数组
- 如果需要补充，生成 1-3 个精准的补充查询
- 最多进行 2 轮补充搜索，避免无限循环

请开始评估："""

    # ========== 传统 ReAct Prompt (备用) ==========
    REACT_PROMPT_TEMPLATE = """你是一个专业的行业研究助手，使用 ReAct 框架进行智能研究。

## 当前研究任务
{query}

## 可用工具
{tools_description}

## 执行历史
{history}

## 已收集的数据摘要
{data_summary}

## 响应格式
```json
{{
    "thought": "你的思考过程",
    "should_finish": false,
    "action": {{
        "tool": "工具名称",
        "params": {{
            "query": "具体参数值"
        }}
    }},
    "confidence": 0.8
}}
```

请开始推理："""

    TOOLS_DESCRIPTION_TEMPLATE = """
{tools_list}

工具参数说明：
- web_search: query(搜索关键词), count(结果数量,默认5)
- knowledge_search: query(搜索问题), kb_name(知识库名称), top_k(结果数量)
- text2sql: question(自然语言问题), intent(查询意图: stats/trend/comparison/detail)
- data_analyzer: data(待分析数据,可选), analysis_type(分析类型: auto/trend/distribution/comparison)
- chart_generator: data(图表数据), chart_type(图表类型: line/bar/pie/scatter), title(图表标题)
- finish: summary(研究总结)
"""

    def __init__(
        self,
        tools: List[Tool],
        llm_api_key: str,
        llm_base_url: str,
        max_steps: int = 10,
        model: str = "qwen-max"
    ):
        """
        初始化 ReAct 控制器

        Args:
            tools: 可用工具列表
            llm_api_key: LLM API 密钥
            llm_base_url: LLM API 基础 URL
            max_steps: 最大执行步骤数
            model: 使用的模型名称
        """
        self.tools = {t.name: t for t in tools}
        self.llm_api_key = llm_api_key
        self.llm_base_url = llm_base_url
        self.max_steps = max_steps
        self.model = model
        self.client = OpenAI(api_key=llm_api_key, base_url=llm_base_url)

    def _format_tools_description(self) -> str:
        """格式化工具描述"""
        tools_list = []
        for name, tool in self.tools.items():
            params_str = ", ".join([f"{k}({v})" for k, v in tool.parameters.items()])
            tools_list.append(f"- {name}: {tool.description}\n  参数: {params_str}")

        return self.TOOLS_DESCRIPTION_TEMPLATE.format(
            tools_list="\n".join(tools_list)
        )

    def _build_prompt(self, context: ReActContext) -> str:
        """构建 ReAct 提示词"""
        return self.REACT_PROMPT_TEMPLATE.format(
            query=context.query,
            tools_description=self._format_tools_description(),
            history=context.get_history_summary(),
            data_summary=context.get_collected_data_summary()
        )

    async def _think(self, context: ReActContext) -> Thought:
        """
        执行思考步骤 - 调用 LLM 进行推理

        Args:
            context: 当前上下文

        Returns:
            Thought 对象，包含推理结果和下一步动作
        """
        prompt = self._build_prompt(context)

        try:
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个专业的行业研究助手，擅长使用各种工具进行深度研究。请严格按照 JSON 格式响应，所有工具调用必须提供完整的params参数。"},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.2  # 降低温度以获得更稳定的输出
            )

            content = response.choices[0].message.content
            logging.info(f"ReAct thinking response: {content[:500]}...")

            # 解析响应
            result = json.loads(content)

            action = None
            if result.get('action'):
                tool_name = result['action'].get('tool', '')
                params = result['action'].get('params', {})

                # 验证和修复 params
                params = self._validate_and_fix_params(tool_name, params, result.get('thought', ''), context)

                action = Action(
                    tool=tool_name,
                    params=params
                )

            return Thought(
                reasoning=result.get('thought', ''),
                should_finish=result.get('should_finish', False),
                next_action=action,
                confidence=result.get('confidence', 0.5)
            )

        except json.JSONDecodeError as e:
            logging.error(f"Failed to parse LLM response as JSON: {e}")
            return Thought(
                reasoning=f"解析响应失败: {e}",
                should_finish=False,
                confidence=0.0
            )
        except Exception as e:
            logging.error(f"Error during thinking: {e}")
            return Thought(
                reasoning=f"思考过程出错: {e}",
                should_finish=True,
                confidence=0.0
            )

    def _validate_and_fix_params(self, tool_name: str, params: Dict, thought: str, context: ReActContext) -> Dict:
        """
        验证并修复工具参数

        如果 LLM 生成了空的 params，尝试从 thought 或 context 中提取参数
        """
        if tool_name == ToolType.WEB_SEARCH.value:
            if not params.get('query'):
                # 尝试从 thought 中提取搜索关键词
                extracted_query = self._extract_search_query_from_thought(thought, context)
                if extracted_query:
                    params['query'] = extracted_query
                    logging.info(f"Extracted query from thought: {extracted_query}")
                else:
                    # 使用原始问题作为备选
                    params['query'] = context.query
                    logging.warning(f"Using context query as fallback: {context.query}")
            if not params.get('count'):
                params['count'] = 5

        elif tool_name == ToolType.KNOWLEDGE_SEARCH.value:
            if not params.get('query'):
                params['query'] = context.query
                logging.warning(f"Using context query for knowledge_search: {context.query}")
            if not params.get('top_k'):
                params['top_k'] = 5

        elif tool_name == ToolType.FINISH.value:
            if not params.get('summary'):
                params['summary'] = f"完成对 '{context.query}' 的研究"

        return params

    def _extract_search_query_from_thought(self, thought: str, context: ReActContext) -> Optional[str]:
        """
        从思考内容中提取搜索关键词

        尝试从 thought 文本中识别用户意图的搜索词
        """
        # 常见的搜索意图表达模式
        patterns = [
            r'搜索[「"\'【](.+?)[」"\'】]',
            r'查找[「"\'【](.+?)[」"\'】]',
            r'搜索关于(.+?)的',
            r'查询(.+?)的信息',
            r'了解(.+?)的',
            r'获取(.+?)的',
        ]

        for pattern in patterns:
            match = re.search(pattern, thought)
            if match:
                return match.group(1).strip()

        # 如果没有匹配到，返回 None，让调用者使用备选方案
        return None

    async def _execute_action(self, action: Action, context: ReActContext) -> Observation:
        """
        执行动作 - 调用相应的工具

        Args:
            action: 要执行的动作
            context: 当前上下文

        Returns:
            Observation 对象，包含执行结果
        """
        tool = self.tools.get(action.tool)

        if not tool:
            return Observation(
                tool=action.tool,
                success=False,
                result=None,
                error=f"未知工具: {action.tool}"
            )

        if not tool.handler:
            return Observation(
                tool=action.tool,
                success=False,
                result=None,
                error=f"工具 {action.tool} 未配置处理器"
            )

        try:
            # 执行工具
            result = await tool.handler(action.params, context)

            return Observation(
                tool=action.tool,
                success=True,
                result=result,
                metadata={"params": action.params}
            )

        except Exception as e:
            logging.error(f"Error executing tool {action.tool}: {e}")
            return Observation(
                tool=action.tool,
                success=False,
                result=None,
                error=str(e)
            )

    # ========== Plan 阶段：生成研究计划和子查询 ==========
    async def _generate_plan(self, context: ReActContext) -> ResearchPlan:
        """
        生成研究计划，包含多个子查询

        Args:
            context: ReAct 上下文

        Returns:
            ResearchPlan 对象
        """
        prompt = self.PLAN_PROMPT.format(query=context.query)

        try:
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个专业的研究规划师，擅长将复杂问题分解为可执行的搜索任务。请严格按照 JSON 格式响应。"},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.3
            )

            content = response.choices[0].message.content
            logging.info(f"Plan generation response: {content[:500]}...")

            result = json.loads(content)

            # 解析子查询
            sub_queries = []
            for sq in result.get('sub_queries', []):
                sub_queries.append(SubQuery(
                    query=sq.get('query', ''),
                    purpose=sq.get('purpose', ''),
                    tool=sq.get('tool', 'web_search'),
                    priority=sq.get('priority', 1)
                ))

            # 如果没有生成子查询，使用原始问题创建默认子查询
            if not sub_queries:
                sub_queries = [
                    SubQuery(query=context.query, purpose="原始问题搜索", tool="web_search", priority=1),
                    SubQuery(query=f"{context.query} 最新动态", purpose="获取最新信息", tool="web_search", priority=1),
                    SubQuery(query=f"{context.query} 分析报告", purpose="获取分析报告", tool="web_search", priority=2),
                ]

            return ResearchPlan(
                understanding=result.get('understanding', ''),
                sub_queries=sub_queries,
                strategy=result.get('strategy', ''),
                expected_aspects=result.get('expected_aspects', [])
            )

        except Exception as e:
            logging.error(f"Error generating plan: {e}")
            # 返回默认计划
            return ResearchPlan(
                understanding=f"研究问题: {context.query}",
                sub_queries=[
                    SubQuery(query=context.query, purpose="主要搜索", tool="web_search", priority=1),
                ],
                strategy="直接搜索",
                expected_aspects=["基本信息"]
            )

    # ========== Execute 阶段：并行执行多个搜索 ==========
    async def _execute_queries_parallel(
        self,
        queries: List[SubQuery],
        context: ReActContext
    ) -> List[Tuple[SubQuery, Observation]]:
        """
        并行执行多个搜索查询

        Args:
            queries: 子查询列表
            context: ReAct 上下文

        Returns:
            (SubQuery, Observation) 元组列表
        """
        async def execute_single_query(sq: SubQuery) -> Tuple[SubQuery, Observation]:
            action = Action(
                tool=sq.tool,
                params={"query": sq.query, "count": 5}
            )
            observation = await self._execute_action(action, context)
            return (sq, observation)

        # 并行执行所有查询
        tasks = [execute_single_query(sq) for sq in queries]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理结果
        valid_results = []
        for result in results:
            if isinstance(result, Exception):
                logging.error(f"Query execution error: {result}")
                continue
            valid_results.append(result)

        return valid_results

    # ========== Reflect 阶段：评估信息是否充足 ==========
    async def _reflect(self, context: ReActContext) -> Dict[str, Any]:
        """
        反思阶段：评估收集的信息是否足够

        Args:
            context: ReAct 上下文

        Returns:
            包含评估结果的字典
        """
        expected_aspects = context.plan.expected_aspects if context.plan else []

        prompt = self.REFLECT_PROMPT.format(
            query=context.query,
            expected_aspects=", ".join(expected_aspects) if expected_aspects else "未指定",
            collected_summary=context.get_collected_data_summary(),
            executed_queries=", ".join(context.executed_queries) if context.executed_queries else "无"
        )

        try:
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个专业的研究评估师，擅长评估信息完整性。请严格按照 JSON 格式响应。"},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.2
            )

            content = response.choices[0].message.content
            logging.info(f"Reflect response: {content[:500]}...")

            result = json.loads(content)

            # 解析补充查询
            additional_queries = []
            for aq in result.get('additional_queries', []):
                additional_queries.append(SubQuery(
                    query=aq.get('query', ''),
                    purpose=aq.get('purpose', ''),
                    tool=aq.get('tool', 'web_search'),
                    priority=2
                ))

            return {
                "coverage_analysis": result.get('coverage_analysis', ''),
                "missing_aspects": result.get('missing_aspects', []),
                "is_sufficient": result.get('is_sufficient', True),
                "additional_queries": additional_queries,
                "confidence": result.get('confidence', 0.5)
            }

        except Exception as e:
            logging.error(f"Error during reflection: {e}")
            return {
                "coverage_analysis": "评估出错",
                "missing_aspects": [],
                "is_sufficient": True,  # 出错时默认结束
                "additional_queries": [],
                "confidence": 0.0
            }

    # ========== 主运行循环：优化版 ==========
    async def run(
        self,
        query: str,
        initial_context: Optional[Dict] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        执行优化版 ReAct 循环: Plan -> Execute (并行) -> Reflect -> Synthesize

        Args:
            query: 用户查询
            initial_context: 初始上下文数据

        Yields:
            包含事件类型和数据的字典
        """
        context = ReActContext(query)
        if initial_context:
            context.metadata.update(initial_context)

        max_iterations = 3  # 最多3轮迭代
        step = 0

        yield {"type": "react_start", "query": query, "mode": "optimized"}

        # ========== Phase 1: Plan ==========
        yield {"type": "status", "content": "正在分析问题，生成研究计划..."}

        plan = await self._generate_plan(context)
        context.plan = plan

        yield {
            "type": "thought",
            "step": 1,
            "content": f"**问题理解**: {plan.understanding}\n\n**研究策略**: {plan.strategy}",
            "confidence": 0.9
        }

        yield {
            "type": "plan",
            "understanding": plan.understanding,
            "strategy": plan.strategy,
            "sub_queries": [{"query": sq.query, "purpose": sq.purpose, "tool": sq.tool} for sq in plan.sub_queries],
            "expected_aspects": plan.expected_aspects
        }

        # ========== Phase 2 & 3: Execute & Reflect Loop ==========
        while context.iteration < max_iterations:
            context.iteration += 1
            step += 1

            # 获取当前要执行的查询
            if context.iteration == 1:
                # 第一轮：执行计划中的所有查询
                queries_to_execute = [sq for sq in plan.sub_queries if sq.priority <= 2]
            else:
                # 后续轮次：执行反思阶段生成的补充查询
                queries_to_execute = context.metadata.get('additional_queries', [])

            if not queries_to_execute:
                break

            # 显示即将执行的搜索
            yield {
                "type": "action",
                "step": step,
                "tool": "parallel_search",
                "params": {"queries": [sq.query for sq in queries_to_execute]}
            }

            yield {"type": "status", "content": f"正在并行执行 {len(queries_to_execute)} 个搜索..."}

            # 并行执行搜索
            results = await self._execute_queries_parallel(queries_to_execute, context)

            # 处理结果
            total_results = 0
            for sq, obs in results:
                context.executed_queries.append(sq.query)
                context.add_observation(obs)

                if obs.success and isinstance(obs.result, list):
                    total_results += len(obs.result)
                    # 流式返回搜索结果
                    for item in obs.result:
                        yield {"type": "search_result_item", "result": item}

            yield {
                "type": "observation",
                "step": step,
                "tool": "parallel_search",
                "success": True,
                "result": f"并行搜索完成，共获取 {total_results} 条结果",
                "queries_executed": [sq.query for sq, _ in results]
            }

            # 如果是最后一轮或没有收集到数据，跳过反思
            if context.iteration >= max_iterations or not context.collected_data:
                break

            # ========== Reflect ==========
            step += 1
            yield {"type": "status", "content": "正在评估信息完整性..."}

            reflect_result = await self._reflect(context)

            yield {
                "type": "thought",
                "step": step,
                "content": f"**信息评估**: {reflect_result['coverage_analysis']}",
                "confidence": reflect_result['confidence']
            }

            # 如果信息充足，结束循环
            if reflect_result['is_sufficient']:
                yield {"type": "status", "content": "信息收集完成"}
                break

            # 如果有缺失方面，准备补充搜索
            if reflect_result['additional_queries']:
                context.metadata['additional_queries'] = reflect_result['additional_queries']
                yield {
                    "type": "status",
                    "content": f"发现信息缺口，将补充搜索: {', '.join([q.query for q in reflect_result['additional_queries']])}"
                }
            else:
                break

        # ========== Phase 4: Complete ==========
        yield {"type": "status", "content": "研究完成，准备生成报告"}

        yield {
            "type": "react_complete",
            "total_steps": step,
            "total_iterations": context.iteration,
            "collected_data": context.collected_data,
            "executed_queries": context.executed_queries,
            "insights": context.insights,
            "charts": context.charts
        }

    def register_tool(self, tool: Tool):
        """注册新工具"""
        self.tools[tool.name] = tool

    def update_tool_handler(self, tool_name: str, handler: Callable):
        """更新工具处理器"""
        if tool_name in self.tools:
            self.tools[tool_name].handler = handler


def create_default_tools() -> List[Tool]:
    """创建默认工具集"""
    return [
        Tool(
            name=ToolType.WEB_SEARCH.value,
            description="搜索互联网获取最新信息，适用于查找实时数据、新闻、市场信息等",
            parameters={
                "query": "搜索关键词",
                "count": "返回结果数量(默认5)"
            }
        ),
        Tool(
            name=ToolType.KNOWLEDGE_SEARCH.value,
            description="搜索本地知识库获取专业文档，适用于查找内部资料、专业报告等",
            parameters={
                "query": "搜索问题",
                "kb_name": "知识库名称",
                "top_k": "返回结果数量"
            }
        ),
        Tool(
            name=ToolType.TEXT2SQL.value,
            description="将自然语言转换为SQL查询数据库，获取结构化数据",
            parameters={
                "question": "自然语言问题",
                "intent": "查询意图(stats/trend/comparison/detail)"
            }
        ),
        Tool(
            name=ToolType.DATA_ANALYZER.value,
            description="分析数据并识别模式、趋势、异常等，自动推荐可视化方式",
            parameters={
                "data": "待分析数据(可选，默认使用已收集数据)",
                "analysis_type": "分析类型(auto/trend/distribution/comparison)"
            }
        ),
        Tool(
            name=ToolType.CHART_GENERATOR.value,
            description="根据数据生成可视化图表配置，支持折线图、柱状图、饼图等",
            parameters={
                "data": "图表数据",
                "chart_type": "图表类型(line/bar/pie/scatter)",
                "title": "图表标题"
            }
        ),
        Tool(
            name=ToolType.STOCK_QUERY.value,
            description="查询股票实时行情信息，获取股票价格、涨跌幅、成交量等数据",
            parameters={
                "stock_code": "股票代码(如sh601009/sz000001，6开头为上证，0/3开头为深证)",
                "keyword": "股票名称或代码关键词(当不确定完整代码时使用)"
            }
        ),
        Tool(
            name=ToolType.BIDDING_SEARCH.value,
            description="搜索招投标信息，获取招标公告、中标信息、采购公告等",
            parameters={
                "keyword": "搜索关键词(必填)",
                "category": "项目类别(招标/中标/采购)",
                "region": "地区筛选",
                "page": "页码(默认1)"
            }
        ),
        Tool(
            name=ToolType.FINISH.value,
            description="完成研究任务，开始生成最终研究报告",
            parameters={
                "summary": "研究总结"
            }
        )
    ]
