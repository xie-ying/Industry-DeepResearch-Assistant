"""
DeepResearch V2.0 - 生成式多智能体协作网络

核心特点：
1. 5个专家Agent协作：架构师、侦探、极客、评论家、笔杆
2. 动态状态机：Plan -> Research -> Analyze -> Write -> Review -> Revise
3. 对抗式质检：毒舌评论家确保报告质量
4. 代码解释器：支持Python数据分析和可视化
5. LangGraph实现：支持循环和条件分支

使用方式：
```python
from service.deep_research_v2 import DeepResearchService

service = DeepResearchService(
    llm_api_key="your-api-key",
    llm_base_url="https://api.example.com",
    search_api_key="your-search-key"
)

async for event in service.research("中国AI芯片市场分析"):
    print(event)
```
"""

from .state import (
    ResearchState,
    ResearchPhase,
    Section,
    Fact,
    DataPoint,
    Chart,
    CriticFeedback,
    create_initial_state
)

from .graph import DeepResearchGraph, create_research_graph

from .agents import (
    ChiefArchitect,
    DeepScout,
    CodeWizard,
    CriticMaster,
    LeadWriter
)

__all__ = [
    # State
    'ResearchState',
    'ResearchPhase',
    'Section',
    'Fact',
    'DataPoint',
    'Chart',
    'CriticFeedback',
    'create_initial_state',

    # Graph
    'DeepResearchGraph',
    'create_research_graph',

    # Agents
    'ChiefArchitect',
    'DeepScout',
    'CodeWizard',
    'CriticMaster',
    'LeadWriter',
]
