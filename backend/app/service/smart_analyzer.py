"""
Smart Data Analyzer - 智能数据分析器

功能：
1. 自动识别数据类型和特征
2. 趋势分析与异常检测
3. 自动推荐可视化类型
4. 生成数据洞察
"""

import json
import logging
import re
from typing import Dict, Any, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
from collections import Counter
import statistics

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class DataType(Enum):
    """数据类型枚举"""
    NUMERIC = "numeric"
    CATEGORICAL = "categorical"
    DATETIME = "datetime"
    TEXT = "text"
    BOOLEAN = "boolean"


class ChartType(Enum):
    """图表类型枚举"""
    LINE = "line"
    BAR = "bar"
    PIE = "pie"
    SCATTER = "scatter"
    TABLE = "table"
    NONE = "none"


@dataclass
class ColumnProfile:
    """列数据画像"""
    name: str
    data_type: DataType
    non_null_count: int
    unique_count: int
    sample_values: List[Any] = field(default_factory=list)
    statistics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AnalysisResult:
    """分析结果"""
    success: bool
    insights: List[str]
    statistics: Dict[str, Any]
    visualization_hint: str
    chart_config: Optional[Dict] = None
    data_profile: Optional[Dict] = None
    error: Optional[str] = None


class SmartDataAnalyzer:
    """
    智能数据分析器

    自动分析数据特征，识别模式和趋势，
    并推荐最佳的可视化方式。
    """

    # 时间相关列名模式
    TIME_COLUMN_PATTERNS = [
        'year', 'month', 'date', 'time', 'quarter', 'week',
        'created', 'updated', 'timestamp', 'period', 'day',
        '年份', '月份', '日期', '时间', '季度'
    ]

    # 数值相关列名模式
    NUMERIC_COLUMN_PATTERNS = [
        'value', 'amount', 'count', 'total', 'sum', 'avg',
        'price', 'cost', 'revenue', 'profit', 'rate', 'ratio',
        'percent', 'share', 'growth', 'score', 'metric',
        '金额', '数量', '总计', '价格', '收入', '利润', '比例', '占比'
    ]

    # 分类相关列名模式
    CATEGORY_COLUMN_PATTERNS = [
        'name', 'type', 'category', 'class', 'group', 'status',
        'industry', 'region', 'company', 'product', 'brand',
        '名称', '类型', '分类', '行业', '地区', '公司', '产品'
    ]

    def __init__(self):
        """初始化分析器"""
        self.keywords_for_insights = [
            '增长', '下降', '上升', '减少', '稳定', '波动',
            '最高', '最低', '平均', '总计', '占比', '比例',
            'growth', 'decline', 'increase', 'decrease', 'stable'
        ]

    def analyze(
        self,
        data: Union[List[Dict], List[str], Dict],
        analysis_type: str = "auto"
    ) -> Dict[str, Any]:
        """
        执行数据分析

        Args:
            data: 待分析数据
            analysis_type: 分析类型 (auto/trend/distribution/comparison)

        Returns:
            分析结果字典
        """
        try:
            # 标准化数据格式
            normalized_data = self._normalize_data(data)

            if not normalized_data:
                return {
                    "success": False,
                    "error": "无有效数据可分析",
                    "insights": [],
                    "statistics": {},
                    "visualization_hint": "none"
                }

            # 数据画像
            profile = self._profile_data(normalized_data)

            # 根据分析类型执行分析
            if analysis_type == "auto":
                analysis_type = self._detect_analysis_type(profile, normalized_data)

            if analysis_type == "trend":
                result = self._analyze_trend(normalized_data, profile)
            elif analysis_type == "distribution":
                result = self._analyze_distribution(normalized_data, profile)
            elif analysis_type == "comparison":
                result = self._analyze_comparison(normalized_data, profile)
            else:
                result = self._analyze_general(normalized_data, profile)

            # 添加数据画像到结果
            result['data_profile'] = {
                'total_rows': len(normalized_data),
                'columns': {
                    col.name: {
                        'type': col.data_type.value,
                        'unique': col.unique_count,
                        'non_null': col.non_null_count
                    } for col in profile
                }
            }

            return result

        except Exception as e:
            logging.error(f"Analysis error: {e}")
            return {
                "success": False,
                "error": str(e),
                "insights": [],
                "statistics": {},
                "visualization_hint": "none"
            }

    def _normalize_data(self, data: Any) -> List[Dict]:
        """
        标准化数据格式

        Args:
            data: 原始数据

        Returns:
            标准化的字典列表
        """
        if isinstance(data, list):
            if not data:
                return []

            if all(isinstance(item, dict) for item in data):
                return data

            if all(isinstance(item, str) for item in data):
                # 文本列表 - 尝试提取结构化信息
                return self._extract_from_texts(data)

            # 简单值列表
            return [{"value": item, "index": i} for i, item in enumerate(data)]

        if isinstance(data, dict):
            return [data]

        return []

    def _extract_from_texts(self, texts: List[str]) -> List[Dict]:
        """从文本列表中提取结构化数据"""
        extracted = []

        # 数值提取模式
        number_pattern = re.compile(r'(\d{1,3}(?:,\d{3})*(?:\.\d+)?|\d+(?:\.\d+)?)\s*(?:元|万|亿|%|人民币|美元)?')
        year_pattern = re.compile(r'(20\d{2}|19\d{2})年?')

        for i, text in enumerate(texts):
            item = {"index": i, "text": text[:200]}

            # 提取年份
            years = year_pattern.findall(text)
            if years:
                item["year"] = int(years[0])

            # 提取数值
            numbers = number_pattern.findall(text)
            if numbers:
                try:
                    item["value"] = float(numbers[0].replace(',', ''))
                except:
                    pass

            # 提取百分比
            percent_match = re.search(r'(\d+(?:\.\d+)?)\s*%', text)
            if percent_match:
                item["percentage"] = float(percent_match.group(1))

            extracted.append(item)

        return extracted

    def _profile_data(self, data: List[Dict]) -> List[ColumnProfile]:
        """
        生成数据画像

        Args:
            data: 数据列表

        Returns:
            列画像列表
        """
        if not data:
            return []

        # 收集所有列名
        all_columns = set()
        for row in data:
            all_columns.update(row.keys())

        profiles = []
        for col_name in all_columns:
            values = [row.get(col_name) for row in data if col_name in row]
            non_null_values = [v for v in values if v is not None and v != '']

            # 检测数据类型
            data_type = self._detect_column_type(col_name, non_null_values)

            # 计算统计信息
            stats = {}
            if data_type == DataType.NUMERIC and non_null_values:
                try:
                    numeric_values = [float(v) for v in non_null_values if self._is_numeric(v)]
                    if numeric_values:
                        stats = {
                            'min': min(numeric_values),
                            'max': max(numeric_values),
                            'mean': statistics.mean(numeric_values),
                            'sum': sum(numeric_values)
                        }
                        if len(numeric_values) > 1:
                            stats['std'] = statistics.stdev(numeric_values)
                except:
                    pass

            profile = ColumnProfile(
                name=col_name,
                data_type=data_type,
                non_null_count=len(non_null_values),
                unique_count=len(set(str(v) for v in non_null_values)),
                sample_values=non_null_values[:5],
                statistics=stats
            )
            profiles.append(profile)

        return profiles

    def _detect_column_type(self, col_name: str, values: List) -> DataType:
        """检测列数据类型"""
        col_lower = col_name.lower()

        # 根据列名模式判断
        for pattern in self.TIME_COLUMN_PATTERNS:
            if pattern in col_lower:
                return DataType.DATETIME

        for pattern in self.CATEGORY_COLUMN_PATTERNS:
            if pattern in col_lower:
                return DataType.CATEGORICAL

        # 根据值判断
        if not values:
            return DataType.TEXT

        numeric_count = sum(1 for v in values if self._is_numeric(v))
        if numeric_count / len(values) > 0.8:
            return DataType.NUMERIC

        # 检查是否是分类数据 (唯一值较少)
        unique_ratio = len(set(str(v) for v in values)) / len(values)
        if unique_ratio < 0.3:
            return DataType.CATEGORICAL

        return DataType.TEXT

    def _is_numeric(self, value: Any) -> bool:
        """检查值是否为数值"""
        if isinstance(value, (int, float)):
            return True
        if isinstance(value, str):
            try:
                float(value.replace(',', ''))
                return True
            except:
                return False
        return False

    def _detect_analysis_type(self, profile: List[ColumnProfile], data: List[Dict]) -> str:
        """自动检测最佳分析类型"""
        has_time = any(p.data_type == DataType.DATETIME for p in profile)
        has_numeric = any(p.data_type == DataType.NUMERIC for p in profile)
        has_category = any(p.data_type == DataType.CATEGORICAL for p in profile)

        if has_time and has_numeric:
            return "trend"
        if has_category and has_numeric:
            return "comparison"
        if has_numeric:
            return "distribution"

        return "general"

    def _analyze_trend(self, data: List[Dict], profile: List[ColumnProfile]) -> Dict[str, Any]:
        """趋势分析"""
        insights = []
        statistics = {}

        # 找到时间列和数值列
        time_col = None
        value_col = None

        for p in profile:
            if p.data_type == DataType.DATETIME and not time_col:
                time_col = p.name
            if p.data_type == DataType.NUMERIC and not value_col:
                value_col = p.name

        if time_col and value_col:
            # 按时间排序
            sorted_data = sorted(data, key=lambda x: x.get(time_col, 0))

            values = [float(row.get(value_col, 0)) for row in sorted_data if self._is_numeric(row.get(value_col))]
            times = [row.get(time_col) for row in sorted_data]

            if len(values) >= 2:
                # 计算趋势
                first_val = values[0]
                last_val = values[-1]
                change = last_val - first_val
                change_pct = (change / first_val * 100) if first_val != 0 else 0

                trend = "上升" if change > 0 else "下降" if change < 0 else "持平"
                insights.append(f"整体呈{trend}趋势，变化幅度 {abs(change_pct):.1f}%")

                # 计算增长率
                if len(values) > 2:
                    growth_rates = [(values[i] - values[i-1]) / values[i-1] * 100
                                   for i in range(1, len(values)) if values[i-1] != 0]
                    if growth_rates:
                        avg_growth = statistics.mean(growth_rates)
                        insights.append(f"平均增长率 {avg_growth:.1f}%")

                statistics = {
                    'start_value': first_val,
                    'end_value': last_val,
                    'total_change': change,
                    'change_percent': change_pct,
                    'trend': trend,
                    'data_points': len(values)
                }

            # 生成图表配置
            chart_config = {
                "type": "line",
                "title": f"{value_col}趋势分析",
                "data": {
                    "xAxis": times,
                    "series": [{"name": value_col, "data": values}]
                }
            }

            return {
                "success": True,
                "insights": insights,
                "statistics": statistics,
                "visualization_hint": "line",
                "chart_config": chart_config
            }

        return self._analyze_general(data, profile)

    def _analyze_distribution(self, data: List[Dict], profile: List[ColumnProfile]) -> Dict[str, Any]:
        """分布分析"""
        insights = []
        statistics = {}

        # 找到数值列
        numeric_profiles = [p for p in profile if p.data_type == DataType.NUMERIC]

        if numeric_profiles:
            main_col = numeric_profiles[0]
            values = []

            for row in data:
                val = row.get(main_col.name)
                if self._is_numeric(val):
                    values.append(float(val) if isinstance(val, str) else val)

            if values:
                stats = {
                    'count': len(values),
                    'min': min(values),
                    'max': max(values),
                    'mean': statistics.mean(values) if hasattr(statistics, 'mean') else sum(values) / len(values),
                    'sum': sum(values)
                }

                if len(values) > 1:
                    import statistics as stat_module
                    stats['median'] = stat_module.median(values)
                    stats['std'] = stat_module.stdev(values)

                statistics = stats

                insights.append(f"共 {len(values)} 个数据点")
                insights.append(f"范围: {stats['min']:.2f} - {stats['max']:.2f}")
                insights.append(f"平均值: {stats['mean']:.2f}")

                # 检测异常值
                if 'std' in stats:
                    threshold = stats['mean'] + 2 * stats['std']
                    outliers = [v for v in values if v > threshold]
                    if outliers:
                        insights.append(f"发现 {len(outliers)} 个潜在异常值")

        return {
            "success": True,
            "insights": insights,
            "statistics": statistics,
            "visualization_hint": "bar"
        }

    def _analyze_comparison(self, data: List[Dict], profile: List[ColumnProfile]) -> Dict[str, Any]:
        """对比分析"""
        insights = []
        statistics = {}

        # 找到分类列和数值列
        cat_col = None
        value_col = None

        for p in profile:
            if p.data_type == DataType.CATEGORICAL and not cat_col:
                cat_col = p.name
            if p.data_type == DataType.NUMERIC and not value_col:
                value_col = p.name

        if cat_col and value_col:
            # 按分类聚合
            category_values = {}
            for row in data:
                cat = row.get(cat_col)
                val = row.get(value_col)
                if cat and self._is_numeric(val):
                    if cat not in category_values:
                        category_values[cat] = []
                    category_values[cat].append(float(val) if isinstance(val, str) else val)

            if category_values:
                # 计算各分类统计
                category_stats = {}
                for cat, vals in category_values.items():
                    category_stats[cat] = {
                        'sum': sum(vals),
                        'avg': sum(vals) / len(vals),
                        'count': len(vals)
                    }

                # 找出最大和最小
                sorted_by_sum = sorted(category_stats.items(), key=lambda x: x[1]['sum'], reverse=True)
                if sorted_by_sum:
                    top_cat = sorted_by_sum[0]
                    insights.append(f"最高: {top_cat[0]} ({top_cat[1]['sum']:.2f})")

                    if len(sorted_by_sum) > 1:
                        bottom_cat = sorted_by_sum[-1]
                        insights.append(f"最低: {bottom_cat[0]} ({bottom_cat[1]['sum']:.2f})")

                    # 计算占比
                    total = sum(s['sum'] for s in category_stats.values())
                    if total > 0:
                        top_share = top_cat[1]['sum'] / total * 100
                        insights.append(f"{top_cat[0]} 占比 {top_share:.1f}%")

                statistics = {
                    'categories': len(category_stats),
                    'category_stats': category_stats,
                    'total': total if 'total' in dir() else 0
                }

                # 决定图表类型
                viz_hint = "pie" if len(category_stats) <= 6 else "bar"

                # 生成图表配置
                chart_config = {
                    "type": viz_hint,
                    "title": f"{cat_col}对比分析",
                    "data": {
                        "series": [{
                            "name": value_col,
                            "data": [{"name": k, "value": v['sum']} for k, v in sorted_by_sum]
                        }]
                    }
                }

                return {
                    "success": True,
                    "insights": insights,
                    "statistics": statistics,
                    "visualization_hint": viz_hint,
                    "chart_config": chart_config
                }

        return self._analyze_general(data, profile)

    def _analyze_general(self, data: List[Dict], profile: List[ColumnProfile]) -> Dict[str, Any]:
        """通用分析"""
        insights = []
        statistics = {
            'total_rows': len(data),
            'total_columns': len(profile)
        }

        # 基础统计
        insights.append(f"共 {len(data)} 条数据，{len(profile)} 个字段")

        # 数值列统计
        for p in profile:
            if p.statistics:
                insights.append(f"{p.name}: 范围 {p.statistics.get('min', 'N/A')} - {p.statistics.get('max', 'N/A')}")

        # 分类列统计
        for p in profile:
            if p.data_type == DataType.CATEGORICAL:
                insights.append(f"{p.name}: {p.unique_count} 个不同值")

        return {
            "success": True,
            "insights": insights,
            "statistics": statistics,
            "visualization_hint": "table"
        }


# 工厂函数
def create_smart_analyzer() -> SmartDataAnalyzer:
    """创建智能分析器实例"""
    return SmartDataAnalyzer()
