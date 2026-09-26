"""
行业配置 - 定义各行业的搜索关键词
"""
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class IndustryConfig:
    """行业配置"""
    id: str
    name: str
    description: str
    news_keywords: List[str]
    bidding_keywords: List[str]
    research_keywords: List[str]


# 预定义的行业配置
INDUSTRY_CONFIGS: Dict[str, IndustryConfig] = {
    "smart_transportation": IndustryConfig(
        id="smart_transportation",
        name="智慧交通",
        description="智能交通系统、车路协同、自动驾驶等领域",
        news_keywords=[
            "智慧交通 政策",
            "智慧交通 市场",
            "交通运输部 通知",
            "智能网联汽车",
            "自动驾驶 政策",
            "新能源汽车 政策",
            "交通大数据",
            "车路协同",
        ],
        bidding_keywords=[
            "智慧交通",
            "智能交通",
            "交通信息化",
            "车路协同",
            "自动驾驶",
            "智能网联",
        ],
        research_keywords=["智慧交通", "智能交通", "车路协同", "自动驾驶"],
    ),
    "finance": IndustryConfig(
        id="finance",
        name="金融科技",
        description="银行、保险、证券、支付等金融领域",
        news_keywords=[
            "金融科技 政策",
            "数字人民币",
            "银行数字化转型",
            "保险科技",
            "证券 金融科技",
            "支付 监管",
            "金融大数据",
            "智能风控",
        ],
        bidding_keywords=[
            "银行",
            "金融",
            "保险",
            "证券",
            "支付平台",
            "风控系统",
            "信贷系统",
            "银行核心系统",
        ],
        research_keywords=["金融科技", "数字金融", "银行数字化", "智能风控"],
    ),
    "healthcare": IndustryConfig(
        id="healthcare",
        name="医疗健康",
        description="医疗信息化、智慧医院、医药研发等领域",
        news_keywords=[
            "医疗信息化 政策",
            "智慧医院",
            "医保 政策",
            "药品集采",
            "医疗大数据",
            "互联网医疗",
            "AI医疗",
            "医药研发",
        ],
        bidding_keywords=[
            "医院信息化",
            "智慧医疗",
            "HIS系统",
            "医疗设备",
            "医药采购",
            "医保系统",
        ],
        research_keywords=["医疗信息化", "智慧医疗", "医药研发", "互联网医疗"],
    ),
    "energy": IndustryConfig(
        id="energy",
        name="能源电力",
        description="新能源、电力系统、储能等领域",
        news_keywords=[
            "新能源 政策",
            "碳中和",
            "光伏 市场",
            "风电 政策",
            "储能 市场",
            "电力市场化",
            "智能电网",
            "充电桩",
        ],
        bidding_keywords=[
            "新能源项目",
            "光伏电站",
            "风电项目",
            "储能系统",
            "智能电网",
            "充电设施",
        ],
        research_keywords=["新能源", "碳中和", "储能", "智能电网"],
    ),
}

# 默认行业
DEFAULT_INDUSTRY_ID = "smart_transportation"


def get_industry_config(industry_id: Optional[str] = None) -> IndustryConfig:
    """
    获取行业配置

    Args:
        industry_id: 行业ID，如果为空则返回默认行业

    Returns:
        行业配置
    """
    if not industry_id:
        industry_id = DEFAULT_INDUSTRY_ID

    config = INDUSTRY_CONFIGS.get(industry_id)
    if not config:
        logger.warning(f"[industry_config] 未找到行业配置: {industry_id}, 使用默认行业")
        config = INDUSTRY_CONFIGS[DEFAULT_INDUSTRY_ID]

    logger.info(f"[industry_config] 获取行业配置: {config.name} ({config.id})")
    return config


def get_all_industries() -> List[Dict]:
    """
    获取所有行业列表

    Returns:
        行业列表
    """
    return [
        {
            "id": config.id,
            "name": config.name,
            "description": config.description,
        }
        for config in INDUSTRY_CONFIGS.values()
    ]
