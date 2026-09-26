"""
Text2SQL Service - 自然语言转 SQL 查询服务

功能：
1. 将自然语言问题转换为 SQL 查询
2. 安全验证 SQL 语句
3. 执行查询并返回结构化数据
4. 自动推荐可视化类型
"""

import json
import logging
import re
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from openai import OpenAI

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class QueryIntent(Enum):
    """查询意图类型"""
    STATS = "stats"  # 统计查询
    TREND = "trend"  # 趋势分析
    COMPARISON = "comparison"  # 对比分析
    DETAIL = "detail"  # 详情查询


@dataclass
class SQLResult:
    """SQL 查询结果"""
    success: bool
    sql: str
    explanation: str
    data: List[Dict]
    columns: List[str]
    visualization_hint: str
    error: Optional[str] = None


class Text2SQLService:
    """
    Text2SQL 服务

    将自然语言问题转换为 SQL 查询，支持：
    - 自动 Schema 推断
    - SQL 安全验证
    - 查询结果格式化
    - 可视化推荐
    """

    # 安全配置
    ALLOWED_KEYWORDS = [
        'SELECT', 'FROM', 'WHERE', 'GROUP BY', 'ORDER BY', 'LIMIT',
        'JOIN', 'LEFT JOIN', 'RIGHT JOIN', 'INNER JOIN', 'ON',
        'AND', 'OR', 'NOT', 'IN', 'LIKE', 'BETWEEN',
        'AS', 'DISTINCT', 'HAVING', 'UNION',
        'COUNT', 'SUM', 'AVG', 'MAX', 'MIN',
        'YEAR', 'MONTH', 'DATE', 'CAST', 'COALESCE',
        'ASC', 'DESC', 'NULLS', 'FIRST', 'LAST',
        'CASE', 'WHEN', 'THEN', 'ELSE', 'END',
        'IS', 'NULL', 'TRUE', 'FALSE'
    ]

    FORBIDDEN_KEYWORDS = [
        'DROP', 'DELETE', 'UPDATE', 'INSERT', 'TRUNCATE',
        'ALTER', 'CREATE', 'GRANT', 'REVOKE',
        'EXEC', 'EXECUTE', 'XP_', 'SP_',
        '--', '/*', '*/', ';--', 'UNION ALL SELECT',
        'INFORMATION_SCHEMA', 'SYS.', 'SYSOBJECTS',
        'WAITFOR', 'DELAY', 'BENCHMARK', 'SLEEP'
    ]

    # 数据库 Schema 定义
    SCHEMA_DEFINITION = """
可查询的数据表：

1. industry_stats (行业统计数据表)
   - id: UUID, 主键
   - industry_name: VARCHAR(100), 行业名称 (当前数据: 智慧交通)
   - metric_name: VARCHAR(100), 指标名称 (如: 市场规模、同比增长率、智能公交市场规模、智慧高速市场规模、车路协同市场规模、智慧停车市场规模、交通大脑市场规模、固定资产投资、研发投入、从业人员数量、企业数量、专利申请数、营收)
   - metric_value: FLOAT, 指标值
   - unit: VARCHAR(50), 单位 (如: 亿元、%、万人、家、件)
   - year: INTEGER, 年份 (2023-2025)
   - quarter: INTEGER, 季度 (1-4, 可为空表示年度数据)
   - month: INTEGER, 月份 (1-12, 可为空)
   - region: VARCHAR(50), 地区 (如: 全国、华东地区、华南地区、华北地区)
   - source: VARCHAR(200), 数据来源
   - created_at: TIMESTAMP, 创建时间

2. company_data (企业数据表)
   - id: UUID, 主键
   - company_name: VARCHAR(200), 企业名称 (如: 海康威视、大华股份、千方科技、易华录、银江技术、金溢科技、万集科技、皖通科技、中远海科、四维图新、蘑菇车联、希迪智驾)
   - stock_code: VARCHAR(20), 股票代码 (如: 002415.SZ、002236.SZ、未上市)
   - industry: VARCHAR(100), 所属行业 (当前数据: 智慧交通)
   - sub_industry: VARCHAR(100), 细分行业 (如: 智能监控、交通信息化、数据存储、智慧城市、ETC、高速公路信息化、港口信息化、高精地图、车路协同、自动驾驶)
   - revenue: FLOAT, 营收 (亿元)
   - net_profit: FLOAT, 净利润 (亿元)
   - gross_margin: FLOAT, 毛利率 (%)
   - market_cap: FLOAT, 市值 (亿元)
   - employees: INTEGER, 员工数
   - market_share: FLOAT, 市场份额 (%)
   - year: INTEGER, 年份
   - quarter: INTEGER, 季度

3. policy_data (政策数据表)
   - id: UUID, 主键
   - policy_name: VARCHAR(500), 政策名称 (如: 交通强国建设纲要、智能汽车创新发展战略、数字交通发展规划纲要、北京市自动驾驶汽车条例)
   - policy_number: VARCHAR(100), 政策文号
   - department: VARCHAR(200), 发布部门 (如: 中共中央、国务院、交通运输部、工业和信息化部、住建部)
   - level: VARCHAR(50), 政策级别 (国家级/省级/市级)
   - publish_date: DATE, 发布日期
   - effective_date: DATE, 生效日期
   - category: VARCHAR(100), 政策类别 (如: 发展规划、发展战略、技术规范、指导意见、实施方案、试点通知、行动计划、地方法规)
   - industry: VARCHAR(100), 相关行业 (当前数据: 智慧交通)
   - summary: TEXT, 政策摘要
   - impact_level: VARCHAR(20), 影响程度 (重大/一般/轻微)

当前数据库示例数据:
- 智慧交通2024年市场规模: 3200亿元
- 智慧交通2025年市场规模预测: 3680亿元
- 智慧交通2024年同比增长率: 12.3%
- 海康威视2024年Q3营收: 893.5亿元，市场份额15.2%
- 大华股份2024年Q3营收: 328.6亿元
- 千方科技2024年Q3营收: 85.2亿元
- 智慧高速市场规模2024年: 720亿元
- 车路协同市场规模2024年: 450亿元
"""

    TEXT2SQL_PROMPT = """你是一个专业的 SQL 专家。请根据用户的自然语言问题生成安全的 PostgreSQL 查询语句。

{schema}

用户问题: {question}
查询意图: {intent}

生成要求:
1. 只生成 SELECT 查询，禁止任何修改操作 (UPDATE/DELETE/INSERT/DROP等)
2. 使用标准 PostgreSQL 语法
3. 结果限制在 100 条以内
4. 合理使用聚合函数和 GROUP BY
5. 对于趋势分析，使用 ORDER BY year, quarter
6. 对于对比分析，确保数据可比较

请严格按照以下 JSON 格式返回:
{{
    "sql": "生成的SQL语句",
    "explanation": "SQL查询的解释说明",
    "expected_columns": ["列名1", "列名2"],
    "visualization_hint": "推荐的可视化类型 (line/bar/pie/table/none)",
    "confidence": 0.95
}}

注意:
- 如果问题无法转换为有效SQL，返回 sql 为空字符串并在 explanation 中说明原因
- visualization_hint 选择依据:
  - line: 时间序列/趋势数据
  - bar: 分类比较数据
  - pie: 占比/构成数据
  - table: 详细列表数据
  - none: 单一数值或无法可视化
"""

    def __init__(
        self,
        llm_api_key: str,
        llm_base_url: str,
        db_connection_string: Optional[str] = None,
        model: str = "qwen-max"
    ):
        """
        初始化 Text2SQL 服务

        Args:
            llm_api_key: LLM API 密钥
            llm_base_url: LLM API 基础 URL
            db_connection_string: 数据库连接字符串
            model: 使用的模型
        """
        self.llm_api_key = llm_api_key
        self.llm_base_url = llm_base_url
        self.db_connection_string = db_connection_string
        self.model = model
        self.client = OpenAI(api_key=llm_api_key, base_url=llm_base_url)
        self.db_engine = None

        # 初始化数据库连接
        if db_connection_string:
            self._init_db_connection()

    def _init_db_connection(self):
        """初始化数据库连接"""
        try:
            from sqlalchemy import create_engine
            self.db_engine = create_engine(
                self.db_connection_string,
                pool_size=5,
                max_overflow=10,
                pool_pre_ping=True
            )
            logging.info("Database connection initialized")
        except Exception as e:
            logging.error(f"Failed to initialize database connection: {e}")
            self.db_engine = None

    def validate_sql(self, sql: str) -> Tuple[bool, str]:
        """
        验证 SQL 安全性

        Args:
            sql: SQL 语句

        Returns:
            (是否安全, 错误信息)
        """
        if not sql or not sql.strip():
            return False, "SQL 语句为空"

        sql_upper = sql.upper().strip()

        # 检查禁止关键词
        for keyword in self.FORBIDDEN_KEYWORDS:
            if keyword in sql_upper:
                return False, f"SQL 包含禁止的关键词: {keyword}"

        # 检查是否以 SELECT 开头
        if not sql_upper.startswith('SELECT'):
            return False, "SQL 必须以 SELECT 开头"

        # 检查是否包含多条语句
        if ';' in sql[:-1]:  # 允许末尾的分号
            return False, "不允许多条 SQL 语句"

        # 检查注释
        if '--' in sql or '/*' in sql:
            return False, "SQL 中不允许注释"

        return True, ""

    def _extract_json_from_response(self, content: str) -> Dict[str, Any]:
        """
        从 LLM 响应中提取 JSON

        支持多种格式:
        1. 纯 JSON
        2. Markdown 代码块 ```json ... ```
        3. 文本中包含的 JSON

        Args:
            content: LLM 响应内容

        Returns:
            解析后的 JSON 字典
        """
        if not content:
            raise ValueError("响应内容为空")

        content = content.strip()

        # 尝试直接解析
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass

        # 尝试从 markdown 代码块中提取
        code_block_match = re.search(r'```(?:json)?\s*\n?([\s\S]*?)\n?```', content)
        if code_block_match:
            try:
                return json.loads(code_block_match.group(1).strip())
            except json.JSONDecodeError:
                pass

        # 尝试找到 JSON 对象
        json_match = re.search(r'\{[\s\S]*\}', content)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass

        raise ValueError(f"无法从响应中提取有效的 JSON: {content[:200]}...")

    async def generate_sql(self, question: str, intent: str = "stats") -> Dict[str, Any]:
        """
        使用 LLM 生成 SQL

        Args:
            question: 自然语言问题
            intent: 查询意图

        Returns:
            生成结果
        """
        prompt = self.TEXT2SQL_PROMPT.format(
            schema=self.SCHEMA_DEFINITION,
            question=question,
            intent=intent
        )

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个专业的 SQL 专家，擅长将自然语言转换为安全的 SQL 查询。请只返回 JSON 格式的响应，不要添加任何额外文字。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1
            )

            content = response.choices[0].message.content
            logging.info(f"LLM response: {content[:500] if content else 'None'}...")

            if not content:
                return {
                    "sql": "",
                    "explanation": "LLM 返回空响应",
                    "expected_columns": [],
                    "visualization_hint": "none",
                    "confidence": 0.0
                }

            result = self._extract_json_from_response(content)

            return {
                "sql": result.get("sql", ""),
                "explanation": result.get("explanation", ""),
                "expected_columns": result.get("expected_columns", []),
                "visualization_hint": result.get("visualization_hint", "table"),
                "confidence": result.get("confidence", 0.5)
            }

        except ValueError as e:
            logging.error(f"Failed to extract JSON from response: {e}")
            return {
                "sql": "",
                "explanation": str(e),
                "expected_columns": [],
                "visualization_hint": "none",
                "confidence": 0.0
            }
        except json.JSONDecodeError as e:
            logging.error(f"Failed to parse LLM response: {e}")
            return {
                "sql": "",
                "explanation": f"解析响应失败: {e}",
                "expected_columns": [],
                "visualization_hint": "none",
                "confidence": 0.0
            }
        except Exception as e:
            logging.error(f"Error generating SQL: {e}")
            return {
                "sql": "",
                "explanation": f"生成 SQL 失败: {e}",
                "expected_columns": [],
                "visualization_hint": "none",
                "confidence": 0.0
            }

    def execute_sql(self, sql: str) -> Tuple[List[Dict], List[str], Optional[str]]:
        """
        安全执行 SQL 查询

        Args:
            sql: SQL 语句

        Returns:
            (数据列表, 列名列表, 错误信息)
        """
        # 验证 SQL
        is_valid, error_msg = self.validate_sql(sql)
        if not is_valid:
            return [], [], error_msg

        if not self.db_engine:
            # 返回模拟数据用于演示
            return self._get_mock_data(sql)

        try:
            from sqlalchemy import text
            with self.db_engine.connect() as conn:
                result = conn.execute(text(sql))
                columns = list(result.keys())
                data = [dict(zip(columns, row)) for row in result.fetchall()]
                return data, columns, None
        except Exception as e:
            logging.error(f"SQL execution error: {e}")
            return [], [], str(e)

    def _get_mock_data(self, sql: str) -> Tuple[List[Dict], List[str], Optional[str]]:
        """
        返回模拟数据（用于演示和测试）

        Args:
            sql: SQL 语句

        Returns:
            (数据列表, 列名列表, 错误信息)
        """
        sql_lower = sql.lower()

        # 根据 SQL 内容返回不同的模拟数据
        if 'industry_stats' in sql_lower:
            if 'year' in sql_lower and ('group by' in sql_lower or 'order by' in sql_lower):
                # 时间序列数据
                data = [
                    {"year": 2020, "metric_value": 136.7, "industry_name": "新能源汽车", "unit": "万辆"},
                    {"year": 2021, "metric_value": 352.1, "industry_name": "新能源汽车", "unit": "万辆"},
                    {"year": 2022, "metric_value": 688.7, "industry_name": "新能源汽车", "unit": "万辆"},
                    {"year": 2023, "metric_value": 949.5, "industry_name": "新能源汽车", "unit": "万辆"},
                    {"year": 2024, "metric_value": 1200.0, "industry_name": "新能源汽车", "unit": "万辆"},
                ]
                columns = ["year", "metric_value", "industry_name", "unit"]
            else:
                data = [
                    {"industry_name": "新能源汽车", "metric_name": "销量", "metric_value": 949.5, "unit": "万辆", "year": 2023},
                    {"industry_name": "新能源汽车", "metric_name": "市场渗透率", "metric_value": 35.8, "unit": "%", "year": 2023},
                    {"industry_name": "新能源汽车", "metric_name": "出口量", "metric_value": 120.3, "unit": "万辆", "year": 2023},
                    {"industry_name": "动力电池", "metric_name": "装车量", "metric_value": 387.7, "unit": "GWh", "year": 2023},
                    {"industry_name": "充电桩", "metric_name": "保有量", "metric_value": 859.6, "unit": "万台", "year": 2023},
                ]
                columns = ["industry_name", "metric_name", "metric_value", "unit", "year"]

        elif 'company_data' in sql_lower:
            data = [
                {"company_name": "比亚迪", "industry": "新能源汽车", "revenue": 6023.15, "net_profit": 300.41, "market_share": 35.0, "year": 2023},
                {"company_name": "特斯拉中国", "industry": "新能源汽车", "revenue": 2100.0, "market_share": 15.5, "year": 2023},
                {"company_name": "理想汽车", "industry": "新能源汽车", "revenue": 1238.5, "net_profit": 118.1, "market_share": 5.0, "year": 2023},
                {"company_name": "蔚来汽车", "industry": "新能源汽车", "revenue": 556.18, "net_profit": -207.2, "market_share": 3.5, "year": 2023},
                {"company_name": "宁德时代", "industry": "动力电池", "revenue": 4009.17, "net_profit": 441.21, "market_share": 43.11, "year": 2023},
            ]
            columns = ["company_name", "industry", "revenue", "net_profit", "market_share", "year"]

        elif 'policy_data' in sql_lower:
            data = [
                {"policy_name": "关于延续和优化新能源汽车车辆购置税减免政策的公告", "department": "财政部", "publish_date": "2023-06-21", "industry": "新能源汽车", "impact_level": "重大"},
                {"policy_name": "新能源汽车产业发展规划(2021-2035年)", "department": "国务院办公厅", "publish_date": "2020-11-02", "industry": "新能源汽车", "impact_level": "重大"},
                {"policy_name": "关于进一步构建高质量充电基础设施体系的指导意见", "department": "国务院办公厅", "publish_date": "2023-06-19", "industry": "充电桩", "impact_level": "重大"},
            ]
            columns = ["policy_name", "department", "publish_date", "industry", "impact_level"]

        else:
            data = [{"message": "模拟数据", "value": 100}]
            columns = ["message", "value"]

        return data, columns, None

    async def query(self, question: str, intent: str = "stats") -> Dict[str, Any]:
        """
        执行 Text2SQL 查询的主入口

        Args:
            question: 自然语言问题
            intent: 查询意图

        Returns:
            查询结果
        """
        # 1. 生成 SQL
        generation_result = await self.generate_sql(question, intent)

        sql = generation_result.get("sql", "")
        if not sql:
            return {
                "success": False,
                "error": generation_result.get("explanation", "无法生成有效的 SQL"),
                "sql": "",
                "data": [],
                "columns": [],
                "visualization_hint": "none"
            }

        # 2. 验证 SQL
        is_valid, error_msg = self.validate_sql(sql)
        if not is_valid:
            return {
                "success": False,
                "error": f"SQL 验证失败: {error_msg}",
                "sql": sql,
                "data": [],
                "columns": [],
                "visualization_hint": "none"
            }

        # 3. 执行查询
        data, columns, exec_error = self.execute_sql(sql)
        if exec_error:
            return {
                "success": False,
                "error": f"查询执行失败: {exec_error}",
                "sql": sql,
                "data": [],
                "columns": columns,
                "visualization_hint": "none"
            }

        # 4. 返回结果
        return {
            "success": True,
            "sql": sql,
            "explanation": generation_result.get("explanation", ""),
            "data": data,
            "columns": columns,
            "visualization_hint": generation_result.get("visualization_hint", "table"),
            "confidence": generation_result.get("confidence", 0.5),
            "row_count": len(data)
        }


# 工厂函数
def create_text2sql_service(
    llm_api_key: str,
    llm_base_url: str,
    db_connection_string: Optional[str] = None
) -> Text2SQLService:
    """创建 Text2SQL 服务实例"""
    return Text2SQLService(
        llm_api_key=llm_api_key,
        llm_base_url=llm_base_url,
        db_connection_string=db_connection_string
    )
