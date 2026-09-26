"""
LLM 和 Agent 配置文件

集中管理所有 LLM 相关配置，包括：
- API 配置（密钥、基础 URL）
- 每个 Agent 节点的模型配置
- 研究流程参数

使用方式:
    from app.config.llm_config import LLMConfig, AgentConfig

    config = LLMConfig()
    print(config.default_model)
    print(config.agents.wizard.model)
"""

import os
from dataclasses import dataclass, field
from typing import Optional, Dict, Any


@dataclass
class AgentModelConfig:
    """单个 Agent 的模型配置"""
    model: str
    temperature: float = 0.7
    max_tokens: int = 8000

    def to_dict(self) -> Dict[str, Any]:
        return {
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }


@dataclass
class AgentsConfig:
    """所有 Agent 的配置"""
    # 规划师 - 分析问题，生成研究大纲
    architect: AgentModelConfig = field(default_factory=lambda: AgentModelConfig(
        model="deepseek-v3.2",
        temperature=0.7,
        max_tokens=4000
    ))

    # 侦察员 - 深度搜索（使用较快的模型）
    scout: AgentModelConfig = field(default_factory=lambda: AgentModelConfig(
        model="qwen-plus",  # 搜索阶段用快速模型
        temperature=0.5,
        max_tokens=4000
    ))

    # 数据分析师 - 数据提取和分析
    data_analyst: AgentModelConfig = field(default_factory=lambda: AgentModelConfig(
        model="deepseek-v3.2",
        temperature=0.3,
        max_tokens=8000
    ))

    # 代码极客 - 代码生成和图表绘制
    wizard: AgentModelConfig = field(default_factory=lambda: AgentModelConfig(
        model="deepseek-v3.2",
        temperature=0.3,
        max_tokens=8000
    ))

    # 审核大师 - 对抗式审核
    critic: AgentModelConfig = field(default_factory=lambda: AgentModelConfig(
        model="deepseek-v3.2",
        temperature=0.5,
        max_tokens=4000
    ))

    # 首席写手 - 报告撰写
    writer: AgentModelConfig = field(default_factory=lambda: AgentModelConfig(
        model="deepseek-v3.2",
        temperature=0.7,
        max_tokens=16000
    ))


@dataclass
class ResearchConfig:
    """研究流程配置"""
    # 最大迭代次数（审核-修订循环）
    max_iterations: int = 1

    # 每个章节最大搜索数量
    max_searches_per_section: int = 3

    # 最大图表数量
    max_charts: int = 5

    # 是否启用代码执行
    enable_code_execution: bool = True

    # 质量评分阈值（1-10分制，低于此分数需要修订）
    quality_threshold: float = 6.0


@dataclass
class LLMConfig:
    """
    LLM 配置主类

    集中管理所有配置，支持从环境变量读取
    """
    # API 配置
    api_key: str = field(default_factory=lambda: os.getenv("DASHSCOPE_API_KEY", ""))
    base_url: str = field(default_factory=lambda: os.getenv(
        "LLM_BASE_URL",
        "https://dashscope.aliyuncs.com/compatible-mode/v1"
    ))

    # 搜索 API
    search_api_key: str = field(default_factory=lambda: os.getenv("BOCHA_API_KEY", ""))

    # 默认模型（用于未单独配置的场景）
    default_model: str = "deepseek-v3.2"

    # Agent 配置
    agents: AgentsConfig = field(default_factory=AgentsConfig)

    # 研究流程配置
    research: ResearchConfig = field(default_factory=ResearchConfig)

    def get_agent_config(self, agent_name: str) -> AgentModelConfig:
        """获取指定 Agent 的配置"""
        agent_configs = {
            "architect": self.agents.architect,
            "scout": self.agents.scout,
            "data_analyst": self.agents.data_analyst,
            "wizard": self.agents.wizard,
            "critic": self.agents.critic,
            "writer": self.agents.writer,
        }
        return agent_configs.get(agent_name, AgentModelConfig(model=self.default_model))

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "api_key": self.api_key[:8] + "..." if self.api_key else "",
            "base_url": self.base_url,
            "search_api_key": self.search_api_key[:8] + "..." if self.search_api_key else "",
            "default_model": self.default_model,
            "agents": {
                "architect": self.agents.architect.to_dict(),
                "scout": self.agents.scout.to_dict(),
                "data_analyst": self.agents.data_analyst.to_dict(),
                "wizard": self.agents.wizard.to_dict(),
                "critic": self.agents.critic.to_dict(),
                "writer": self.agents.writer.to_dict(),
            },
            "research": {
                "max_iterations": self.research.max_iterations,
                "max_searches_per_section": self.research.max_searches_per_section,
                "max_charts": self.research.max_charts,
                "enable_code_execution": self.research.enable_code_execution,
                "quality_threshold": self.research.quality_threshold,
            }
        }


# 全局配置实例（单例模式）
_config_instance: Optional[LLMConfig] = None


def get_config() -> LLMConfig:
    """获取全局配置实例"""
    global _config_instance
    if _config_instance is None:
        _config_instance = LLMConfig()
    return _config_instance


def reload_config() -> LLMConfig:
    """重新加载配置"""
    global _config_instance
    _config_instance = LLMConfig()
    return _config_instance


# 便捷访问
def get_agent_model(agent_name: str) -> str:
    """快速获取指定 Agent 的模型名称"""
    return get_config().get_agent_config(agent_name).model


def get_default_model() -> str:
    """快速获取默认模型"""
    return get_config().default_model


# 用于打印配置信息
def print_config():
    """打印当前配置（用于调试）"""
    import json
    config = get_config()
    print("=" * 60)
    print("LLM Configuration")
    print("=" * 60)
    print(json.dumps(config.to_dict(), indent=2, ensure_ascii=False))
    print("=" * 60)


if __name__ == "__main__":
    # 测试配置
    print_config()
