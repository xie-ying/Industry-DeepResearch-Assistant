"""
Chart Generator - 图表配置生成器

生成 ECharts 兼容的图表配置，支持：
1. 折线图 (Line Chart)
2. 柱状图 (Bar Chart)
3. 饼图 (Pie Chart)
4. 散点图 (Scatter Chart)
5. 数据表格 (Table)
"""

import json
import logging
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from enum import Enum

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class ChartType(Enum):
    """图表类型"""
    LINE = "line"
    BAR = "bar"
    PIE = "pie"
    SCATTER = "scatter"
    TABLE = "table"


@dataclass
class ChartConfig:
    """图表配置"""
    chart_type: str
    title: str
    data: Dict[str, Any]
    options: Dict[str, Any]
    width: str = "100%"
    height: str = "400px"


class ChartGenerator:
    """
    图表配置生成器

    生成符合 ECharts 规范的图表配置，
    前端可直接使用这些配置渲染图表。
    """

    # 默认颜色方案
    DEFAULT_COLORS = [
        '#5470c6', '#91cc75', '#fac858', '#ee6666',
        '#73c0de', '#3ba272', '#fc8452', '#9a60b4',
        '#ea7ccc', '#48b8d0'
    ]

    # 主题配置
    THEME_CONFIG = {
        'textStyle': {
            'fontFamily': 'PingFang SC, Microsoft YaHei, sans-serif'
        },
        'animation': True,
        'animationDuration': 500
    }

    def __init__(self, theme: str = "default"):
        """
        初始化图表生成器

        Args:
            theme: 主题名称
        """
        self.theme = theme
        self.colors = self.DEFAULT_COLORS

    def generate(
        self,
        data: Union[Dict, List],
        chart_type: str,
        title: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        生成图表配置

        Args:
            data: 图表数据
            chart_type: 图表类型
            title: 图表标题
            **kwargs: 其他配置选项

        Returns:
            ECharts 配置对象
        """
        chart_type = chart_type.lower()

        if chart_type == ChartType.LINE.value:
            return self.generate_line_chart(data, title, **kwargs)
        elif chart_type == ChartType.BAR.value:
            return self.generate_bar_chart(data, title, **kwargs)
        elif chart_type == ChartType.PIE.value:
            return self.generate_pie_chart(data, title, **kwargs)
        elif chart_type == ChartType.SCATTER.value:
            return self.generate_scatter_chart(data, title, **kwargs)
        elif chart_type == ChartType.TABLE.value:
            return self.generate_table(data, title, **kwargs)
        else:
            logging.warning(f"Unknown chart type: {chart_type}, falling back to bar chart")
            return self.generate_bar_chart(data, title, **kwargs)

    def generate_line_chart(
        self,
        data: Union[Dict, List],
        title: str,
        subtitle: str = "",
        smooth: bool = True,
        area: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        生成折线图配置

        Args:
            data: 数据 {xAxis: [], series: [{name, data}]}
            title: 标题
            subtitle: 副标题
            smooth: 是否平滑曲线
            area: 是否显示面积

        Returns:
            ECharts 配置
        """
        x_data, series_data = self._parse_series_data(data)

        # 处理系列配置
        series = []
        for i, s in enumerate(series_data):
            series_config = {
                "name": s.get("name", f"系列{i+1}"),
                "type": "line",
                "data": s.get("data", []),
                "smooth": smooth,
                "emphasis": {
                    "focus": "series"
                }
            }
            if area:
                series_config["areaStyle"] = {"opacity": 0.3}

            series.append(series_config)

        config = {
            "type": "line",
            "title": title,
            "echarts_option": {
                "title": {
                    "text": title,
                    "subtext": subtitle,
                    "left": "center"
                },
                "tooltip": {
                    "trigger": "axis",
                    "axisPointer": {
                        "type": "cross"
                    }
                },
                "legend": {
                    "data": [s["name"] for s in series],
                    "bottom": 0
                },
                "grid": {
                    "left": "3%",
                    "right": "4%",
                    "bottom": "10%",
                    "containLabel": True
                },
                "xAxis": {
                    "type": "category",
                    "boundaryGap": False,
                    "data": x_data
                },
                "yAxis": {
                    "type": "value"
                },
                "series": series,
                "color": self.colors
            }
        }

        return config

    def generate_bar_chart(
        self,
        data: Union[Dict, List],
        title: str,
        subtitle: str = "",
        horizontal: bool = False,
        stacked: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        生成柱状图配置

        Args:
            data: 数据
            title: 标题
            subtitle: 副标题
            horizontal: 是否水平柱状图
            stacked: 是否堆叠

        Returns:
            ECharts 配置
        """
        x_data, series_data = self._parse_series_data(data)

        # 处理系列配置
        series = []
        for i, s in enumerate(series_data):
            series_config = {
                "name": s.get("name", f"系列{i+1}"),
                "type": "bar",
                "data": s.get("data", []),
                "emphasis": {
                    "focus": "series"
                },
                "itemStyle": {
                    "borderRadius": [4, 4, 0, 0] if not horizontal else [0, 4, 4, 0]
                }
            }
            if stacked:
                series_config["stack"] = "total"

            series.append(series_config)

        # 构建轴配置
        category_axis = {
            "type": "category",
            "data": x_data
        }
        value_axis = {
            "type": "value"
        }

        config = {
            "type": "bar",
            "title": title,
            "echarts_option": {
                "title": {
                    "text": title,
                    "subtext": subtitle,
                    "left": "center"
                },
                "tooltip": {
                    "trigger": "axis",
                    "axisPointer": {
                        "type": "shadow"
                    }
                },
                "legend": {
                    "data": [s["name"] for s in series],
                    "bottom": 0
                },
                "grid": {
                    "left": "3%",
                    "right": "4%",
                    "bottom": "10%",
                    "containLabel": True
                },
                "xAxis": value_axis if horizontal else category_axis,
                "yAxis": category_axis if horizontal else value_axis,
                "series": series,
                "color": self.colors
            }
        }

        return config

    def generate_pie_chart(
        self,
        data: Union[Dict, List],
        title: str,
        subtitle: str = "",
        radius: str = "60%",
        rose: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        生成饼图配置

        Args:
            data: 数据 [{name, value}]
            title: 标题
            subtitle: 副标题
            radius: 半径
            rose: 是否玫瑰图

        Returns:
            ECharts 配置
        """
        pie_data = self._parse_pie_data(data)

        series_config = {
            "name": title,
            "type": "pie",
            "radius": radius,
            "data": pie_data,
            "emphasis": {
                "itemStyle": {
                    "shadowBlur": 10,
                    "shadowOffsetX": 0,
                    "shadowColor": "rgba(0, 0, 0, 0.5)"
                }
            },
            "label": {
                "formatter": "{b}: {d}%"
            }
        }

        if rose:
            series_config["roseType"] = "area"
            series_config["radius"] = ["20%", "70%"]

        config = {
            "type": "pie",
            "title": title,
            "echarts_option": {
                "title": {
                    "text": title,
                    "subtext": subtitle,
                    "left": "center"
                },
                "tooltip": {
                    "trigger": "item",
                    "formatter": "{b}: {c} ({d}%)"
                },
                "legend": {
                    "orient": "vertical",
                    "left": "left",
                    "top": "middle"
                },
                "series": [series_config],
                "color": self.colors
            }
        }

        return config

    def generate_scatter_chart(
        self,
        data: Union[Dict, List],
        title: str,
        subtitle: str = "",
        x_name: str = "X",
        y_name: str = "Y",
        **kwargs
    ) -> Dict[str, Any]:
        """
        生成散点图配置

        Args:
            data: 数据 [[x, y], ...]
            title: 标题
            subtitle: 副标题
            x_name: X轴名称
            y_name: Y轴名称

        Returns:
            ECharts 配置
        """
        scatter_data = self._parse_scatter_data(data)

        config = {
            "type": "scatter",
            "title": title,
            "echarts_option": {
                "title": {
                    "text": title,
                    "subtext": subtitle,
                    "left": "center"
                },
                "tooltip": {
                    "trigger": "item",
                    "formatter": f"{x_name}: {{c[0]}}<br/>{y_name}: {{c[1]}}"
                },
                "xAxis": {
                    "type": "value",
                    "name": x_name
                },
                "yAxis": {
                    "type": "value",
                    "name": y_name
                },
                "series": [{
                    "type": "scatter",
                    "data": scatter_data,
                    "symbolSize": 10
                }],
                "color": self.colors
            }
        }

        return config

    def generate_table(
        self,
        data: Union[Dict, List],
        title: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        生成表格配置

        Args:
            data: 数据
            title: 标题

        Returns:
            表格配置
        """
        if isinstance(data, dict):
            if 'data' in data:
                rows = data['data']
            else:
                rows = [data]
        elif isinstance(data, list):
            rows = data
        else:
            rows = []

        # 提取列
        columns = []
        if rows and isinstance(rows[0], dict):
            columns = list(rows[0].keys())

        config = {
            "type": "table",
            "title": title,
            "columns": [{"key": col, "label": col} for col in columns],
            "data": rows,
            "pagination": len(rows) > 10,
            "pageSize": 10
        }

        return config

    def _parse_series_data(self, data: Union[Dict, List]) -> tuple:
        """解析系列数据格式"""
        x_data = []
        series_data = []

        if isinstance(data, dict):
            # 格式: {xAxis: [], series: [{name, data}]}
            x_data = data.get('xAxis', [])
            series_data = data.get('series', [])

            # 如果没有 series，尝试其他格式
            if not series_data:
                # 格式: {category1: value1, category2: value2}
                x_data = list(data.keys())
                series_data = [{"name": "数值", "data": list(data.values())}]

        elif isinstance(data, list):
            if data and isinstance(data[0], dict):
                # 格式: [{name, value}, ...]
                x_data = [item.get('name', f'项目{i}') for i, item in enumerate(data)]
                series_data = [{"name": "数值", "data": [item.get('value', 0) for item in data]}]
            else:
                # 格式: [value1, value2, ...]
                x_data = [f'项目{i+1}' for i in range(len(data))]
                series_data = [{"name": "数值", "data": data}]

        return x_data, series_data

    def _parse_pie_data(self, data: Union[Dict, List]) -> List[Dict]:
        """解析饼图数据格式"""
        pie_data = []

        if isinstance(data, dict):
            if 'series' in data and data['series']:
                # 格式: {series: [{data: [{name, value}]}]}
                series = data['series'][0]
                pie_data = series.get('data', [])
            else:
                # 格式: {category1: value1, category2: value2}
                for k, v in data.items():
                    if k not in ['xAxis', 'series', 'type', 'title']:
                        pie_data.append({"name": k, "value": v})

        elif isinstance(data, list):
            if data and isinstance(data[0], dict):
                pie_data = data
            else:
                # 格式: [value1, value2, ...]
                pie_data = [{"name": f"项目{i+1}", "value": v} for i, v in enumerate(data)]

        return pie_data

    def _parse_scatter_data(self, data: Union[Dict, List]) -> List[List]:
        """解析散点图数据格式"""
        scatter_data = []

        if isinstance(data, list):
            for item in data:
                if isinstance(item, (list, tuple)) and len(item) >= 2:
                    scatter_data.append([item[0], item[1]])
                elif isinstance(item, dict):
                    x = item.get('x', item.get('value', 0))
                    y = item.get('y', item.get('count', 0))
                    scatter_data.append([x, y])

        return scatter_data

    def merge_configs(self, *configs) -> Dict[str, Any]:
        """合并多个图表配置"""
        # 实现配置合并逻辑
        pass


# 工厂函数
def create_chart_generator(theme: str = "default") -> ChartGenerator:
    """创建图表生成器实例"""
    return ChartGenerator(theme=theme)
