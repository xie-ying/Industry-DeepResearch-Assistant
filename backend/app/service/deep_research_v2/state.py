"""
DeepResearch V2.0 - 状态管理模块

实现全局工作记忆（Global Working Memory），所有Agent共享此状态。
使用 TypedDict 确保类型安全，与 LangGraph 完美兼容。
"""

from typing import TypedDict, List, Dict, Any, Optional, Literal
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class ResearchPhase(str, Enum):
    """研究阶段状态机"""
    INIT = "init"                    # 初始化
    PLANNING = "planning"            # 规划阶段
    RESEARCHING = "researching"      # 深度探索阶段
    ANALYZING = "analyzing"          # 数据分析阶段
    WRITING = "writing"              # 撰写阶段
    REVIEWING = "reviewing"          # 对抗审核阶段
    RE_RESEARCHING = "re_researching"  # 补充搜索阶段（审核发现缺失信息后）
    REVISING = "revising"            # 修订阶段（仅文字修改）
    COMPLETED = "completed"          # 完成


@dataclass
class Section:
    """报告章节"""
    id: str
    title: str
    description: str
    section_type: Literal["qualitative", "quantitative", "mixed"]  # 定性/定量/混合
    status: Literal["pending", "researching", "drafted", "reviewed", "final"]
    content: str = ""
    sources: List[str] = field(default_factory=list)
    subsections: List['Section'] = field(default_factory=list)
    requires_data: bool = False
    requires_chart: bool = False


@dataclass
class Fact:
    """结构化事实"""
    id: str
    content: str
    source_url: str
    source_name: str
    source_type: Literal["official", "academic", "news", "report", "self_media"]  # 来源类型
    credibility_score: float  # 可信度评分 0-1
    extracted_at: datetime
    related_sections: List[str] = field(default_factory=list)  # 关联章节ID
    verified: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DataPoint:
    """数据点"""
    id: str
    name: str
    value: Any
    unit: str
    year: Optional[int]
    source: str
    confidence: float


@dataclass
class Chart:
    """图表配置"""
    id: str
    title: str
    chart_type: Literal["line", "bar", "pie", "scatter", "table", "heatmap"]
    data: Dict[str, Any]
    code: str  # 生成图表的Python代码
    image_path: Optional[str] = None
    section_id: Optional[str] = None


@dataclass
class CriticFeedback:
    """评论家反馈"""
    id: str
    target_section: str
    issue_type: Literal["missing_source", "logic_error", "bias", "hallucination", "outdated", "incomplete"]
    severity: Literal["critical", "major", "minor"]
    description: str
    suggestion: str
    resolved: bool = False


@dataclass
class AgentLog:
    """Agent执行日志"""
    timestamp: datetime
    agent: str
    action: str
    input_summary: str
    output_summary: str
    duration_ms: int
    tokens_used: int = 0


class ResearchState(TypedDict):
    """
    LangGraph 状态定义

    这是整个研究过程的全局状态，所有Agent都在读写这个状态。
    使用 TypedDict 以获得类型提示和 LangGraph 兼容性。
    """
    # 基础信息
    query: str                              # 用户原始问题
    session_id: str                         # 会话ID
    phase: str                              # 当前阶段
    iteration: int                          # 当前迭代轮次
    max_iterations: int                     # 最大迭代次数

    # 搜索模式配置
    search_web: bool                        # 是否启用网络搜索
    search_local: bool                      # 是否启用本地知识库搜索

    # 规划输出
    outline: List[Dict[str, Any]]           # 动态大纲 (Section序列化)
    mind_map: Dict[str, Any]                # 知识图谱/思维导图
    key_entities: List[str]                 # 关键实体
    research_questions: List[str]           # 待研究的子问题
    hypotheses: List[Dict[str, Any]]        # 研究假设（假设驱动研究）
    knowledge_graph: Dict[str, Any]         # 知识图谱 {nodes: [], edges: []}

    # 知识库
    facts: List[Dict[str, Any]]             # 结构化事实库
    data_points: List[Dict[str, Any]]       # 数据点
    raw_sources: List[Dict[str, Any]]       # 原始来源（网页内容）

    # 分析输出
    charts: List[Dict[str, Any]]            # 生成的图表
    code_executions: List[Dict[str, Any]]   # 代码执行记录
    insights: List[str]                     # 数据洞察

    # 写作输出
    draft_sections: Dict[str, str]          # 章节草稿 {section_id: content}
    final_report: str                       # 最终报告
    references: List[Dict[str, Any]]        # 参考文献

    # 审核反馈
    critic_feedback: List[Dict[str, Any]]   # 评论家反馈
    unresolved_issues: int                  # 未解决问题数
    quality_score: float                    # 质量评分
    pending_search_queries: List[str]       # 待执行的补充搜索查询（审核后需要补充的）

    # 元数据
    logs: List[Dict[str, Any]]              # 执行日志
    errors: List[str]                       # 错误记录
    messages: List[Dict[str, Any]]          # Agent间消息（用于流式输出）


def create_initial_state(
    query: str,
    session_id: str,
    search_web: bool = True,
    search_local: bool = False
) -> ResearchState:
    """创建初始状态

    Args:
        query: 用户查询
        session_id: 会话ID
        search_web: 是否启用网络搜索（默认True）
        search_local: 是否启用本地知识库搜索（默认False）
    """
    return ResearchState(
        query=query,
        session_id=session_id,
        phase=ResearchPhase.INIT.value,
        iteration=0,
        max_iterations=3,
        search_web=search_web,
        search_local=search_local,
        outline=[],
        mind_map={},
        key_entities=[],
        research_questions=[],
        hypotheses=[],  # 假设驱动研究
        knowledge_graph={"nodes": [], "edges": []},  # 知识图谱
        facts=[],
        data_points=[],
        raw_sources=[],
        charts=[],
        code_executions=[],
        insights=[],
        draft_sections={},
        final_report="",
        references=[],
        critic_feedback=[],
        unresolved_issues=0,
        quality_score=0.0,
        pending_search_queries=[],
        logs=[],
        errors=[],
        messages=[]
    )


def section_to_dict(section: Section) -> Dict[str, Any]:
    """Section 序列化"""
    return {
        "id": section.id,
        "title": section.title,
        "description": section.description,
        "section_type": section.section_type,
        "status": section.status,
        "content": section.content,
        "sources": section.sources,
        "subsections": [section_to_dict(s) for s in section.subsections],
        "requires_data": section.requires_data,
        "requires_chart": section.requires_chart
    }


def fact_to_dict(fact: Fact) -> Dict[str, Any]:
    """Fact 序列化"""
    return {
        "id": fact.id,
        "content": fact.content,
        "source_url": fact.source_url,
        "source_name": fact.source_name,
        "source_type": fact.source_type,
        "credibility_score": fact.credibility_score,
        "extracted_at": fact.extracted_at.isoformat(),
        "related_sections": fact.related_sections,
        "verified": fact.verified,
        "metadata": fact.metadata
    }
