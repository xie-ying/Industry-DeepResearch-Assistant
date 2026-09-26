"""
行业数据模型 - 用于 Text2SQL 查询

包含三个主要表：
1. industry_stats - 行业统计数据
2. company_data - 企业数据
3. policy_data - 政策数据
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, Float, Integer, Date
from sqlalchemy.dialects.postgresql import UUID, JSONB

from core.database import Base


class IndustryStats(Base):
    """行业统计数据表"""
    __tablename__ = "industry_stats"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    industry_name = Column(String(100), nullable=False, index=True, comment="行业名称")
    metric_name = Column(String(100), nullable=False, index=True, comment="指标名称")
    metric_value = Column(Float, nullable=False, comment="指标值")
    unit = Column(String(50), comment="单位")
    year = Column(Integer, index=True, comment="年份")
    quarter = Column(Integer, comment="季度(1-4)")
    month = Column(Integer, comment="月份(1-12)")
    region = Column(String(50), default="全国", comment="地区")
    source = Column(String(200), comment="数据来源")
    source_url = Column(Text, comment="来源链接")
    notes = Column(Text, comment="备注说明")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": str(self.id),
            "industry_name": self.industry_name,
            "metric_name": self.metric_name,
            "metric_value": self.metric_value,
            "unit": self.unit,
            "year": self.year,
            "quarter": self.quarter,
            "region": self.region,
            "source": self.source
        }


class CompanyData(Base):
    """企业数据表"""
    __tablename__ = "company_data"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_name = Column(String(200), nullable=False, index=True, comment="企业名称")
    stock_code = Column(String(20), comment="股票代码")
    industry = Column(String(100), index=True, comment="所属行业")
    sub_industry = Column(String(100), comment="细分行业")

    # 财务数据
    revenue = Column(Float, comment="营收(亿元)")
    net_profit = Column(Float, comment="净利润(亿元)")
    gross_margin = Column(Float, comment="毛利率(%)")
    market_cap = Column(Float, comment="市值(亿元)")

    # 运营数据
    employees = Column(Integer, comment="员工数")
    market_share = Column(Float, comment="市场份额(%)")

    # 时间维度
    year = Column(Integer, index=True, comment="年份")
    quarter = Column(Integer, comment="季度")

    # 元数据
    data_source = Column(String(200), comment="数据来源")
    extra_data = Column(JSONB, comment="扩展数据")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": str(self.id),
            "company_name": self.company_name,
            "stock_code": self.stock_code,
            "industry": self.industry,
            "revenue": self.revenue,
            "net_profit": self.net_profit,
            "market_share": self.market_share,
            "year": self.year
        }


class PolicyData(Base):
    """政策数据表"""
    __tablename__ = "policy_data"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    policy_name = Column(String(500), nullable=False, comment="政策名称")
    policy_number = Column(String(100), comment="政策文号")
    department = Column(String(200), nullable=False, index=True, comment="发布部门")
    level = Column(String(50), default="国家级", comment="政策级别(国家级/省级/市级)")

    # 时间
    publish_date = Column(Date, index=True, comment="发布日期")
    effective_date = Column(Date, comment="生效日期")
    expiry_date = Column(Date, comment="失效日期")

    # 内容
    category = Column(String(100), index=True, comment="政策类别")
    industry = Column(String(100), index=True, comment="相关行业")
    summary = Column(Text, comment="政策摘要")
    key_points = Column(JSONB, comment="关键要点")
    full_text_url = Column(Text, comment="全文链接")

    # 影响
    impact_level = Column(String(20), comment="影响程度(重大/一般/轻微)")
    affected_entities = Column(JSONB, comment="受影响主体")

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": str(self.id),
            "policy_name": self.policy_name,
            "department": self.department,
            "publish_date": str(self.publish_date) if self.publish_date else None,
            "category": self.category,
            "industry": self.industry,
            "summary": self.summary
        }
