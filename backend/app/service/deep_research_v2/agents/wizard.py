"""
DeepResearch V2.0 - 数据极客 Agent (CodeWizard)

职责：
1. 数据清洗 - 统一不同来源的数据口径
2. 统计分析 - 计算关键指标（CAGR、同比等）
3. 预测建模 - 简单的趋势预测
4. 专业绘图 - 生成高质量数据可视化
"""

import uuid
import asyncio
import json
import base64
import io
import sys
from typing import Dict, Any, List, Optional
from datetime import datetime
from contextlib import redirect_stdout, redirect_stderr

from .base import BaseAgent
from ..state import ResearchState, ResearchPhase


class CodeWizard(BaseAgent):
    """
    数据极客 - 代码与数据分析专家

    特点：
    - 唯一有权执行Python代码的Agent
    - 安全的沙箱执行环境
    - 专业的数据分析和可视化
    """

    ANALYSIS_PROMPT = """你是一位资深的数据分析师，擅长用Python进行数据处理和可视化。

## 研究问题
{query}

## 可用数据
{data_points}

## 任务
根据上述数据，生成Python代码完成以下任务：
1. 数据清洗和标准化
2. 计算关键统计指标
3. 生成专业的可视化图表

## 代码要求（必须严格遵守）

### 0. 禁止使用反斜杠续行（最重要！）
**严禁使用反斜杠 `\\` 进行代码续行**。Python 的字典、列表、函数参数天然支持跨行书写，不需要反斜杠。

✅ 正确示例：
```python
data = {{
    "Year": [2020, 2021, 2022],
    "Value": [100, 200, 300]
}}
df = pd.DataFrame(data)
```

❌ 错误示例（绝对禁止）：
```python
data = {{ \\
    "Year": ...
}}
```

### 1. 数据精简
- **只选取最关键的5-10个数据点**，不要把所有数据都写入代码
- **相同指标去重**：如果有多个年份的同一指标，只保留有代表性的几个
- **代码总长度不超过40行**
- **禁止生成重复数据**：如 [2020, 2020, 2020...] 这种重复是错误的

### 2. 数据定义方式
必须使用"列字典"格式定义数据：
```python
data = {{
    "Year": [2018, 2020, 2022, 2024],
    "Market_Size": [604.2, 1500, 2300, 3000]
}}
df = pd.DataFrame(data)
```

**禁止**使用复杂的嵌套列表 `[[...], [...]]`。

### 3. 数据清洗
创建 DataFrame 后，**必须**执行类型转换：
```python
for col in df.columns:
    if col != 'Year':
        df[col] = pd.to_numeric(df[col], errors='coerce')
df = df.dropna()
```

### 4. 环境限制
- **禁止import语句**，已预定义: pd, np, plt, sns
- **禁止plt.rcParams**，中文字体已预设

### 5. 高级图表样式（必须遵守）
生成专业、高端的商业图表，要求：
- **图表尺寸**: `plt.figure(figsize=(12, 7), dpi=200)`
- **seaborn主题**: `sns.set_theme(style='whitegrid', palette='husl')`
- **标题**: `plt.title('标题', fontsize=18, fontweight='bold', pad=20)`
- **轴标签**: `fontsize=14`
- **刻度**: `fontsize=12`
- **配色**: 使用专业配色如 `#6366f1`（靛蓝）、`#06b6d4`（青色）、`#10b981`（翡翠绿）
- **网格线**: `plt.grid(True, linestyle='--', alpha=0.3)`
- **去除边框**: `sns.despine()`
- **折线图**: `linewidth=2.5, marker='o', markersize=8`，可加面积填充 `plt.fill_between()`
- **柱状图**: 添加数值标签
- **保存**: `plt.savefig('chart.png', dpi=200, bbox_inches='tight', facecolor='white')`

## 输出格式（严格JSON，code字段用\\n表示换行）
```json
{{
    "analysis_plan": "简要分析计划",
    "code": "sns.set_theme(style='whitegrid')\\ndata = {{'Year': [2020, 2022, 2024], 'Value': [100, 150, 200]}}\\ndf = pd.DataFrame(data)\\ndf['Value'] = pd.to_numeric(df['Value'], errors='coerce')\\nplt.figure(figsize=(12, 7), dpi=200)\\nplt.plot(df['Year'], df['Value'], linewidth=2.5, marker='o', markersize=8, color='#6366f1')\\nplt.fill_between(df['Year'], df['Value'], alpha=0.15, color='#6366f1')\\nplt.title('市场规模趋势', fontsize=18, fontweight='bold')\\nplt.xlabel('年份', fontsize=14)\\nplt.ylabel('规模（亿元）', fontsize=14)\\nplt.xticks(fontsize=12)\\nplt.yticks(fontsize=12)\\nsns.despine()\\nplt.savefig('chart.png', dpi=200, bbox_inches='tight', facecolor='white')",
    "expected_outputs": ["图表描述"]
}}
```

注意：code 字段中的换行请使用 `\\n` 字符表示，不要使用物理换行符，也**绝对不要使用续行符 `\\`**。"""

    CHART_PROMPT = """你是专业的数据可视化专家，擅长制作高端商业图表。

## 主题: {topic}
## 图表类型: {chart_type}
## 标题: {title}

## 数据
{data}

## 代码要求（重要）

### 基础要求
1. **严禁使用反斜杠 `\\` 进行代码续行**
2. **不要写import语句**，已预导入: pd, np, plt, sns
3. 数据定义使用标准字典格式: `data = {{"col1": [...], "col2": [...]}}`

### 高级样式要求（必须遵守）
1. **图表尺寸**: `plt.figure(figsize=(12, 7), dpi=200)`
2. **使用 seaborn 主题**: `sns.set_theme(style='whitegrid', palette='husl')`
3. **标题字体**: `plt.title('标题', fontsize=18, fontweight='bold', pad=20)`
4. **坐标轴标签**: `plt.xlabel('X轴', fontsize=14)` 和 `plt.ylabel('Y轴', fontsize=14)`
5. **刻度字体**: `plt.xticks(fontsize=12)` 和 `plt.yticks(fontsize=12)`
6. **添加数据标签**: 在柱状图或折线图的数据点上显示数值
7. **配色方案**: 使用渐变色或专业配色，如 `color='#6366f1'` 或 `palette='Blues_d'`
8. **网格线**: 使用浅色虚线网格 `plt.grid(True, linestyle='--', alpha=0.3)`
9. **边框优化**: `sns.despine()` 去除上右边框
10. **保存**: `plt.savefig('chart.png', dpi=200, bbox_inches='tight', facecolor='white', edgecolor='none')`

### 折线图额外要求
- 线宽 2.5: `linewidth=2.5`
- 添加数据点标记: `marker='o', markersize=8`
- 添加面积填充: `plt.fill_between(x, y, alpha=0.15)`

### 柱状图额外要求
- 圆角效果（如支持）
- 添加数值标签: `for i, v in enumerate(values): plt.text(i, v + offset, str(v), ha='center', fontsize=11)`

## 输出格式（严格JSON）
```json
{{
    "code": "sns.set_theme(style='whitegrid')\\ndata = {{'Year': [2020, 2022], 'Value': [100, 200]}}\\ndf = pd.DataFrame(data)\\nplt.figure(figsize=(12,7), dpi=200)\\nplt.bar(df['Year'], df['Value'], color='#6366f1')\\nplt.title('标题', fontsize=18, fontweight='bold')\\nplt.xlabel('年份', fontsize=14)\\nplt.ylabel('数值', fontsize=14)\\nplt.xticks(fontsize=12)\\nplt.yticks(fontsize=12)\\nsns.despine()\\nplt.savefig('chart.png', dpi=200, bbox_inches='tight', facecolor='white')",
    "chart_description": "图表说明"
}}
```

注意：code字段用 `\\n` 表示换行，**绝对不要使用续行符 `\\`**。"""

    CODE_FIX_PROMPT = """你是一位Python专家，需要修复执行失败的代码。

## 错误类型诊断

请根据错误信息判断错误类型并采取对应修复方法：

1. **如果错误是 `could not convert string to float`**：
   说明你试图将包含中文或特殊字符的列作为数值列处理。
   **修复方法**：在绘图或计算前，使用 `pd.to_numeric(df['col'], errors='coerce')` 清洗该列，并删除 NaN 值。
   不要试图直接画包含中文内容的列（除非是作为标签）。

2. **如果错误是 `SyntaxError`**：
   检查是否有多余的反斜杠或未闭合的括号。

3. **如果错误是 `KeyError`**：
   检查 DataFrame 列名是否正确，确保使用的列名与数据定义一致。

4. **如果错误是类型相关 (`TypeError`)**：
   检查数据类型是否匹配，必要时使用 `.astype()` 或 `pd.to_numeric()` 转换。

## 原始代码
{code}

## 错误信息
{error}

## 输出
{stdout}

## 要求
1. **不要写import语句**，已预导入: pd, np, plt, sns
2. 中文字体已预设
3. 使用"列字典"格式定义数据: `data = {{"col1": [...], "col2": [...]}}`
4. 创建 DataFrame 后立即转换数值列

## 输出格式
```json
{{
    "error_analysis": "错误原因分析",
    "fix_description": "具体修复说明",
    "fixed_code": "data = {{'Year': [2020, 2021], 'Value': [100, 200]}}\\ndf = pd.DataFrame(data)\\ndf['Value'] = pd.to_numeric(df['Value'], errors='coerce')\\nprint('done')"
}}
```"""

    # 词云图专用 Prompt
    WORDCLOUD_PROMPT = """你是一位数据可视化专家，擅长文本分析和词云图制作。

## 研究主题
{topic}

## 文本数据
{text_data}

## 任务
生成专业的词云图代码，展示文本中的高频关键词。

要求：
1. 使用 wordcloud 和 jieba 库
2. 中文分词处理
3. 停用词过滤（去掉"的"、"是"、"在"等常见词）
4. 专业配色方案（推荐使用渐变色）
5. 图表尺寸 (12, 8)
6. 保存图片: plt.savefig('chart.png', dpi=150, bbox_inches='tight', facecolor='white')

输出JSON：
```json
{{
    "code": "完整Python代码",
    "chart_description": "图表说明"
}}
```"""

    # 桑基图专用 Prompt（生成 ECharts 配置）
    SANKEY_PROMPT = """你是一位数据可视化专家，擅长流向图和桑基图制作。

## 研究主题
{topic}

## 流向数据
{flow_data}

## 任务
生成桑基图的 ECharts 配置，展示资金流向或产业链上下游关系。

要求：
1. 生成标准的 ECharts sankey 配置
2. 节点颜色要有区分度
3. 连线要有渐变效果
4. 包含 tooltip 显示详情

输出JSON：
```json
{{
    "echarts_option": {{ ECharts 完整配置对象 }},
    "chart_description": "图表说明"
}}
```"""

    # 关系图专用 Prompt
    NETWORK_PROMPT = """你是一位数据可视化专家，擅长关系图谱制作。

## 研究主题
{topic}

## 关系数据
{relation_data}

## 任务
生成关系图代码，展示实体之间的关联关系。

要求：
1. 使用 matplotlib 绘制网络图（或生成 ECharts graph 配置）
2. 节点大小根据重要性调整
3. 不同类型节点用不同颜色
4. 边的粗细根据关系强度调整
5. 添加节点标签
6. 保存图片: plt.savefig('chart.png', dpi=150, bbox_inches='tight', facecolor='white')

输出JSON：
```json
{{
    "code": "完整Python代码",
    "chart_description": "图表说明"
}}
```"""

    # 允许的模块白名单
    ALLOWED_MODULES = {
        'pandas', 'numpy', 'matplotlib', 'matplotlib.pyplot',
        'seaborn', 'datetime', 'math', 'statistics', 'json',
        'collections', 're',
        # 高级可视化
        'wordcloud',      # 词云图
        'jieba',          # 中文分词
    }

    # 禁止的操作（使用正则表达式匹配）
    FORBIDDEN_PATTERNS = [
        r'\bimport\s+os\b',           # import os
        r'\bimport\s+sys\b',          # import sys
        r'\bimport\s+subprocess\b',   # import subprocess
        r'\bos\.',                    # os.xxx
        r'\bsys\.',                   # sys.xxx
        r'\bsubprocess\.',            # subprocess.xxx
        r'\bopen\s*\(',               # open(
        r'\bexec\s*\(',               # exec(
        r'\beval\s*\(',               # eval(
        r'__import__',                # __import__
        r'\bimport\s+requests\b',     # import requests
        r'\brequests\.',              # requests.xxx
        r'\bimport\s+urllib\b',       # import urllib
        r'\burllib\.',                # urllib.xxx
        r'\bimport\s+socket\b',       # import socket
        r'\bsocket\.',                # socket.xxx
        r'\bimport\s+shutil\b',       # import shutil
        r'\bshutil\.',                # shutil.xxx
        r'\bimport\s+pathlib\b',      # import pathlib
        r'\bpathlib\.',               # pathlib.xxx
        r'\bimport\s+pickle\b',       # import pickle
        r'\bpickle\.',                # pickle.xxx
        r'\bimport\s+glob\b',         # import glob
        r'\bglob\.',                  # glob.xxx
        r'\bcompile\s*\(',            # compile(
        r'\b__builtins__\b',          # __builtins__
        r'\b__globals__\b',           # __globals__
        r'\b__code__\b',              # __code__
    ]

    def __init__(self, llm_api_key: str, llm_base_url: str, model: str = "qwen-max"):
        super().__init__(
            name="CodeWizard",
            role="数据极客",
            llm_api_key=llm_api_key,
            llm_base_url=llm_base_url,
            model=model
        )

    async def process(self, state: ResearchState) -> ResearchState:
        """处理入口"""
        self.logger.info(f"[CodeWizard] ========== process 开始 ==========")
        self.logger.info(f"[CodeWizard] 当前 phase: {state['phase']}, data_points: {len(state['data_points'])}, outline: {len(state['outline'])}")

        if state["phase"] != ResearchPhase.ANALYZING.value:
            # 检查是否有需要分析的数据
            if len(state["data_points"]) >= 3:
                state["phase"] = ResearchPhase.ANALYZING.value
                self.logger.info(f"[CodeWizard] 数据点足够，设置 phase 为 ANALYZING")
            else:
                self.logger.warning(f"[CodeWizard] ⚠️ 数据点不足 ({len(state['data_points'])} < 3)，跳过分析")
                return state

        self.add_message(state, "thought", {
            "agent": self.name,
            "content": f"开始数据分析，共有 {len(state['data_points'])} 个数据点..."
        })

        # 执行数据分析
        self.logger.info(f"[CodeWizard] 开始执行 _analyze_data...")
        await self._analyze_data(state)
        self.logger.info(f"[CodeWizard] _analyze_data 完成，当前 charts 数量: {len(state['charts'])}")

        # 生成图表
        self.logger.info(f"[CodeWizard] 开始执行 _generate_charts...")
        await self._generate_charts(state)
        self.logger.info(f"[CodeWizard] _generate_charts 完成，最终 charts 数量: {len(state['charts'])}")

        self.logger.info(f"[CodeWizard] ========== process 结束 ==========")
        return state

    async def _analyze_data(self, state: ResearchState) -> None:
        """分析数据"""
        if not state["data_points"]:
            self.logger.info("[CodeWizard] 没有数据点，跳过分析")
            return

        # 格式化数据点
        data_summary = []
        for dp in state["data_points"]:
            data_summary.append(f"- {dp.get('name')}: {dp.get('value')} {dp.get('unit', '')} ({dp.get('year', 'N/A')})")

        prompt = self.ANALYSIS_PROMPT.format(
            query=state["query"],
            data_points="\n".join(data_summary)
        )

        self.logger.info(f"[CodeWizard] 调用LLM生成分析代码，数据点数量: {len(state['data_points'])}")

        response = await self.call_llm(
            system_prompt="你是专业的数据分析师，擅长Python数据处理和可视化。",
            user_prompt=prompt,
            json_mode=True
        )

        # ===== 详细日志: LLM原始响应 =====
        self._save_debug_log("1_llm_response", response)
        self.logger.info(f"[CodeWizard] LLM响应长度: {len(response)}, 前200字符: {response[:200]}")

        result = self.parse_json_response(response)

        # ===== 详细日志: JSON解析结果 =====
        self._save_debug_log("2_json_parsed", str(result))
        self.logger.info(f"[CodeWizard] JSON解析结果: {type(result)}, keys: {result.keys() if isinstance(result, dict) else 'N/A'}")

        if result and result.get("code"):
            code = result["code"]

            # ===== 详细日志: 原始code字段 =====
            self._save_debug_log("3_code_raw", repr(code) if isinstance(code, str) else str(code))
            self.logger.info(f"[CodeWizard] 原始code类型: {type(code)}, 长度: {len(str(code))}")

            # 确保 code 是字符串类型
            if isinstance(code, list):
                code = '\n'.join(str(c) for c in code)
                self.logger.info(f"[CodeWizard] code是list，已转换为字符串")
            elif not isinstance(code, str):
                code = str(code)
                self.logger.info(f"[CodeWizard] code不是字符串，已转换")

            # ===== 详细日志: 清理前的code =====
            self._save_debug_log("4_code_before_clean", code)

            # 先进行基础清理（处理 \n, \[n] 等格式问题）
            cleaned_code = self._clean_code(code)

            # ===== 详细日志: 清理后的code =====
            self._save_debug_log("5_code_after_clean", cleaned_code)
            self.logger.info(f"[CodeWizard] 清理后code行数: {cleaned_code.count(chr(10)) + 1}")

            # ===== 详细日志: 语法检查 =====
            try:
                compile(cleaned_code, '<string>', 'exec')
                self.logger.info(f"[CodeWizard] ✅ 语法检查通过")
                self._save_debug_log("6_syntax_check", "PASSED")
            except SyntaxError as e:
                self.logger.error(f"[CodeWizard] ❌ 语法检查失败: {e}")
                self._save_debug_log("6_syntax_check", f"FAILED: {e}\n\nCode:\n{cleaned_code}")

            # 验证清理后的代码是否有效（过滤掉明显的垃圾代码）
            # 垃圾代码特征：太短、包含HTML片段、没有多行结构
            if len(cleaned_code) < 50 or '">\\' in cleaned_code or cleaned_code.count('\n') < 3:
                self.logger.warning(f"[CodeWizard] 检测到无效代码，跳过执行: {cleaned_code[:100]}...")
                self._save_debug_log("7_validation", f"INVALID: too short or bad format")
                return None

            # 使用清理后的代码
            code = cleaned_code

            # 发送代码事件
            self.add_message(state, "code", {
                "agent": self.name,
                "language": "python",
                "code": code,
                "purpose": result.get("analysis_plan", "数据分析")
            })

            self.logger.info(f"[CodeWizard] 开始执行代码...")

            # 执行代码（带自愈能力）
            execution_result = await self._execute_with_self_correction(
                code,
                state
            )

            # ===== 详细日志: 执行结果 =====
            self._save_debug_log("8_execution_result", str(execution_result))

            # 记录执行结果
            state["code_executions"].append({
                "id": f"exec_{uuid.uuid4().hex[:8]}",
                "code": execution_result.get("final_code", result["code"]),
                "output": execution_result.get("output", ""),
                "error": execution_result.get("error"),
                "charts": execution_result.get("charts", []),
                "retries": execution_result.get("retries", 0),
                "timestamp": datetime.now().isoformat()
            })

            # 发送执行结果
            self.add_message(state, "code_result", {
                "agent": self.name,
                "success": execution_result.get("success", False),
                "output": execution_result.get("output", "")[:500],
                "has_chart": len(execution_result.get("charts", [])) > 0,
                "retries": execution_result.get("retries", 0)
            })

            # 如果生成了图表，发送 chart SSE 事件
            charts_generated = execution_result.get("charts", [])
            if charts_generated:
                for i, chart_b64 in enumerate(charts_generated):
                    chart_entry = {
                        "id": f"chart_analysis_{uuid.uuid4().hex[:8]}",
                        "title": f"数据分析图表 {i+1}",
                        "chart_type": "generated",
                        "image_base64": chart_b64,
                        "section_id": "analysis"
                    }
                    state["charts"].append(chart_entry)

                    # 发送单个图表事件到前端
                    self.add_message(state, "chart", {
                        "agent": self.name,
                        "title": chart_entry["title"],
                        "chart_type": "generated",
                        "image_base64": chart_b64
                    })
                    self.logger.info(f"[CodeWizard] Sent chart event: {chart_entry['title']}")

    async def _execute_with_self_correction(
        self,
        code: str,
        state: ResearchState,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """
        带自愈能力的代码执行

        特点：
        - 首次执行失败后，将错误信息反馈给LLM修复
        - 最多重试 max_retries 次
        - 记录所有尝试和修复过程
        """
        current_code = code
        retries = 0

        while retries <= max_retries:
            # 执行代码
            result = await self._execute_code(current_code)

            if result.get("success"):
                # 执行成功
                return {
                    "success": True,
                    "output": result.get("output", ""),
                    "charts": result.get("charts", []),
                    "retries": retries,
                    "final_code": current_code
                }

            # 执行失败，尝试修复
            error = result.get("error", "Unknown error")
            stdout = result.get("output", "")

            if retries >= max_retries:
                self.logger.warning(f"Code execution failed after {max_retries} retries: {error}")
                return {
                    "success": False,
                    "error": error,
                    "output": stdout,
                    "charts": [],
                    "retries": retries,
                    "final_code": current_code
                }

            # 发送修复尝试消息
            self.add_message(state, "thought", {
                "agent": self.name,
                "content": f"代码执行失败（第{retries + 1}次），正在自动修复: {error[:100]}..."
            })

            self.logger.info(f"Attempting code self-correction (retry {retries + 1}/{max_retries})")

            # 调用LLM修复代码
            fixed_result = await self._fix_code(current_code, error, stdout)

            if fixed_result and isinstance(fixed_result, dict) and fixed_result.get("fixed_code"):
                fixed_code = fixed_result["fixed_code"]
                # 确保是字符串
                if isinstance(fixed_code, list):
                    fixed_code = '\n'.join(str(c) for c in fixed_code)
                elif not isinstance(fixed_code, str):
                    fixed_code = str(fixed_code)
                current_code = fixed_code
                self.logger.info(f"Code fixed: {fixed_result.get('fix_description', 'N/A')}")

                # 发送修复后的代码
                self.add_message(state, "code_fix", {
                    "agent": self.name,
                    "error_analysis": fixed_result.get("error_analysis", ""),
                    "fix_description": fixed_result.get("fix_description", ""),
                    "retry": retries + 1
                })
            else:
                self.logger.warning("Failed to get fixed code from LLM")
                break

            retries += 1

        return {
            "success": False,
            "error": "Max retries exceeded",
            "output": "",
            "charts": [],
            "retries": retries,
            "final_code": current_code
        }

    async def _fix_code(self, code: str, error: str, stdout: str) -> Optional[Dict]:
        """调用LLM修复代码"""
        prompt = self.CODE_FIX_PROMPT.format(
            code=code,
            error=error,
            stdout=stdout[:1000]  # 限制输出长度
        )

        try:
            response = await self.call_llm(
                system_prompt="你是Python代码调试专家，擅长分析错误并修复代码。",
                user_prompt=prompt,
                json_mode=True,
                temperature=0.2
            )
            return self.parse_json_response(response)
        except Exception as e:
            self.logger.error(f"Code fix LLM call failed: {e}")
            return None

    async def _generate_charts(self, state: ResearchState) -> None:
        """为需要图表的章节生成可视化"""
        # 找出需要图表的章节
        chart_sections = [s for s in state["outline"] if s.get("requires_chart")]

        # 如果没有明确标记需要图表的章节，使用前2个章节作为备选
        if not chart_sections and state["outline"]:
            chart_sections = state["outline"][:2]
            self.logger.info(f"[CodeWizard] 没有 requires_chart 章节，使用前2个章节生成图表")

        self.logger.info(f"[CodeWizard] 开始生成图表，需要图表的章节数: {len(chart_sections)}")

        for i, section in enumerate(chart_sections[:2]):  # 最多生成2个图表
            self.logger.info(f"[CodeWizard] 处理章节 {i+1}/{min(len(chart_sections), 2)}: '{section['title']}'")

            # 收集相关数据
            section_data = self._get_section_data(state, section["id"])
            self.logger.info(f"[CodeWizard] 章节 '{section['title']}' 数据量: {len(section_data)}")

            if not section_data:
                self.logger.warning(f"[CodeWizard] ⚠️ 章节 '{section['title']}' 没有数据，跳过")
                continue

            # 生成图表代码
            self.logger.info(f"[CodeWizard] 调用 LLM 生成图表代码...")
            chart_config = await self._generate_chart_code(
                topic=section["title"],
                data=section_data,
                chart_type="bar" if section.get("section_type") == "quantitative" else "line",
                title=f"{section['title']}分析"
            )

            if chart_config and chart_config.get("code"):
                chart_code = chart_config["code"]
                self._save_debug_log(f"chart_{section['id']}_raw", repr(chart_code))
                self.logger.info(f"[CodeWizard] ✅ 生成图表代码成功，长度: {len(chart_code)}")

                self.add_message(state, "code", {
                    "agent": self.name,
                    "language": "python",
                    "code": chart_code,
                    "purpose": f"生成图表: {section['title']}"
                })

                # 执行并获取图表
                self.logger.info(f"[CodeWizard] 执行图表代码...")
                result = await self._execute_code(chart_code)
                self._save_debug_log(f"chart_{section['id']}_result", str(result))

                if result.get("charts"):
                    self.logger.info(f"[CodeWizard] ✅ 图表执行成功，生成了 {len(result['charts'])} 个图表")
                    chart_entry = {
                        "id": f"chart_{uuid.uuid4().hex[:8]}",
                        "title": section["title"],
                        "chart_type": "generated",
                        "data": section_data,
                        "code": chart_config["code"],
                        "image_base64": result["charts"][0] if result["charts"] else None,
                        "section_id": section["id"]
                    }
                    state["charts"].append(chart_entry)
                    self.logger.info(f"[CodeWizard] 图表已添加到 state['charts']，当前总数: {len(state['charts'])}")

                    self.add_message(state, "chart", {
                        "agent": self.name,
                        "title": section["title"],
                        "chart_type": "generated",
                        "image_base64": result["charts"][0] if result["charts"] else None
                    })
                    self.logger.info(f"[CodeWizard] ✅ 已发送 chart SSE 事件: {section['title']}")
                else:
                    self.logger.warning(f"[CodeWizard] ⚠️ 图表执行失败或没有生成图表: success={result.get('success')}, error={result.get('error', 'N/A')[:100]}")
            else:
                self.logger.warning(f"[CodeWizard] ⚠️ LLM 没有返回有效的图表代码")

    def _get_section_data(self, state: ResearchState, section_id: str) -> List[Dict]:
        """获取章节相关数据"""
        related_facts = [f for f in state["facts"] if section_id in f.get("related_sections", [])]
        related_data = []

        for fact in related_facts:
            # 从facts中提取数据点
            if "data_points" in fact:
                related_data.extend(fact["data_points"])

        # 补充全局数据点
        for dp in state["data_points"][:10]:
            related_data.append(dp)

        return related_data

    async def _generate_chart_code(
        self,
        topic: str,
        data: List[Dict],
        chart_type: str,
        title: str
    ) -> Optional[Dict]:
        """生成图表代码"""
        data_str = json.dumps(data, ensure_ascii=False, indent=2)

        prompt = self.CHART_PROMPT.format(
            topic=topic,
            data=data_str,
            chart_type=chart_type,
            title=title
        )

        response = await self.call_llm(
            system_prompt="你是数据可视化专家。",
            user_prompt=prompt,
            json_mode=True
        )

        return self.parse_json_response(response)

    def _clean_code(self, code: str) -> str:
        """
        清理LLM生成的代码，修复常见格式问题

        完全重写版本：使用字符级处理来正确区分行分隔符和字符串内的 \\n
        这解决了 "unexpected character after line continuation character" 错误
        """
        import re

        # 移除markdown代码块标记
        code = re.sub(r'^```python\s*', '', code, flags=re.MULTILINE)
        code = re.sub(r'^```\s*$', '', code, flags=re.MULTILINE)
        code = re.sub(r'^```json\s*', '', code, flags=re.MULTILINE)
        # 移除行末的 ``` (有时 LLM 会把结束标记粘在最后一行代码后面)
        code = re.sub(r'```\s*$', '', code)

        # 如果代码已经是正常的多行格式（有真正的换行符，没有转义的 \n）
        if '\n' in code and '\\n' not in code:
            lines = code.split('\n')
            cleaned_lines = [line.rstrip() for line in lines]
            return '\n'.join(cleaned_lines).strip()

        # 处理 JSON 编码导致的转义问题
        # 先处理 JSON 转义的引号 \" -> "
        code = code.replace('\\"', '"')

        # 用一个不太可能出现的占位符
        placeholder = "___NL_PLACEHOLDER___"

        # 保护字符串字面量内的 \n
        def protect_strings(text):
            result = []
            i = 0
            while i < len(text):
                # 检测 f-string, r-string 等前缀
                if i < len(text) - 1 and text[i] in 'fFrRbBuU' and text[i+1] in '"\'':
                    quote = text[i+1]
                    result.append(text[i])
                    result.append(quote)
                    i += 2
                    # 读取直到结束引号
                    while i < len(text):
                        if text[i] == '\\' and i + 1 < len(text):
                            if text[i+1] == 'n':
                                result.append(placeholder)
                                i += 2
                            elif text[i+1] == quote:
                                result.append(text[i:i+2])
                                i += 2
                            elif text[i+1] == '\\':
                                # 双反斜杠
                                result.append(text[i:i+2])
                                i += 2
                            else:
                                result.append(text[i])
                                i += 1
                        elif text[i] == quote:
                            result.append(text[i])
                            i += 1
                            break
                        else:
                            result.append(text[i])
                            i += 1
                elif text[i] in '"\'':
                    quote = text[i]
                    result.append(quote)
                    i += 1
                    # 读取直到结束引号
                    while i < len(text):
                        if text[i] == '\\' and i + 1 < len(text):
                            if text[i+1] == 'n':
                                result.append(placeholder)
                                i += 2
                            elif text[i+1] == quote:
                                result.append(text[i:i+2])
                                i += 2
                            elif text[i+1] == '\\':
                                # 双反斜杠
                                result.append(text[i:i+2])
                                i += 2
                            else:
                                result.append(text[i])
                                i += 1
                        elif text[i] == quote:
                            result.append(text[i])
                            i += 1
                            break
                        else:
                            result.append(text[i])
                            i += 1
                else:
                    result.append(text[i])
                    i += 1
            return ''.join(result)

        protected = protect_strings(code)

        # 现在处理行分隔符
        # 先处理各种异常格式（LLM 可能产生的非标准换行标记）
        import re as re_module

        # 1. LaTeX 风格: \[10pt], \\[10pt], \[12pt] 等
        protected = re_module.sub(r'\\\\?\[\d+pt\]\s*', '\n', protected)

        # 2. 中文标记: \[换行], \\[换行], [换行] 等
        protected = re_module.sub(r'\\\\?\[换行\]\s*', '\n', protected)
        protected = protected.replace('[换行]', '\n')

        # 3. \[n] 或 \\[n] 格式
        protected = protected.replace('\\\\[n]', '\n')
        protected = protected.replace('\\[n]', '\n')

        # 4. 修复注释后面粘连代码的问题
        # 例如: "# 数据准备 data = [" 应该变成 "# 数据准备\ndata = ["
        # 检测模式: # 注释文字 后面跟着 Python 关键字/变量赋值
        protected = re_module.sub(
            r'(#[^\n]*?)\s+(import |from |def |class |if |for |while |data\s*=|df\s*=|plt\.|fig\s*=|ax\s*=)',
            r'\1\n\2',
            protected
        )

        # 5. 修复多个语句粘连在一行的问题
        # 例如: "...] plt.rcParams" 应该变成 "...]\nplt.rcParams"
        # 只在特定结束符后分割，避免破坏 "fig, ax =" 这种模式
        # 匹配: ) 或 ] 或 ' 或 " 或 True/False/None 后面跟空格和新语句
        protected = re_module.sub(
            r"([\]\)'\"]|True|False|None)\s+(plt\.|fig\s*,|fig\s*=|ax\.|df\s*=|data\s*=|global_data|china_data|line\d)",
            r'\1\n\2',
            protected
        )

        # \\\\n -> \n (四重转义)
        # \\n -> \n (双重转义)
        # \n -> 换行 (单重转义 - 这是行分隔符)
        protected = protected.replace('\\\\\\\\n', '\n')
        protected = protected.replace('\\\\n', '\n')
        protected = protected.replace('\\n', '\n')

        # 6. 修复 LLM 输出 \\n\\xxx 的问题（换行后多加了反斜杠）
        # 例如: "False\\n\\data = [" 经过上面处理后变成 "False\n\data = ["
        # 需要去掉行首的反斜杠（不是转义序列的情况）
        # 匹配: 行首的反斜杠后跟变量名赋值，如 \data = [
        protected = re_module.sub(r'^\\([a-zA-Z_])', r'\1', protected, flags=re_module.MULTILINE)
        # 也处理不在行首但在空格后的情况
        protected = re_module.sub(r'(\s)\\([a-zA-Z_][a-zA-Z0-9_]*\s*=)', r'\1\2', protected)

        # 恢复字符串内的 \n
        protected = protected.replace(placeholder, '\\n')

        # 修复方括号转义
        protected = protected.replace('\\[', '[')
        protected = protected.replace('\\]', ']')

        # 修复行末的反斜杠问题和移除不需要的语句
        lines = protected.split('\n')
        cleaned_lines = []
        for line in lines:
            stripped = line.strip()
            # 移除 import 语句（沙箱已预导入）
            if stripped.startswith('import ') or stripped.startswith('from '):
                continue
            # 移除 plt.rcParams 设置（沙箱已预设）
            if 'plt.rcParams' in stripped:
                continue
            # 移除行末的 ```
            line = re.sub(r'```\s*$', '', line)

            # ========== 核心修复：移除所有行尾的续行符（反斜杠） ==========
            # 这是"手术刀式"修复，直接把行尾的 \ 及其后的空白删掉
            # 对于 Python 字典 `data = {` 来说，后面没有 \ 也完全合法
            # （Python 支持括号内的自然换行），所以这不会破坏代码逻辑
            # 但能完美解决 "unexpected character after line continuation" 错误
            line = re.sub(r'\\\s*$', '', line)

            line = line.rstrip()
            cleaned_lines.append(line)

        result = '\n'.join(cleaned_lines).strip()
        # 最终清理：移除开头和结尾可能残留的代码块标记
        result = re.sub(r'^```\w*\s*', '', result)
        result = re.sub(r'```\s*$', '', result)
        return result.strip()

    def _save_debug_info(self, raw_code: str, cleaned_code: str, error: Exception = None):
        """保存调试信息到文件，方便排查问题"""
        import os
        from datetime import datetime

        debug_dir = "/tmp/codewizard_debug"
        os.makedirs(debug_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 保存原始代码
        has_escaped_n = '\\n' in raw_code
        has_real_newline = '\n' in raw_code
        with open(f"{debug_dir}/raw_code_{timestamp}.txt", "w") as f:
            f.write("=" * 60 + "\n")
            f.write("原始代码分析\n")
            f.write("=" * 60 + "\n")
            f.write(f"长度: {len(raw_code)} 字符\n")
            f.write(f"包含 \\n 字面量: {has_escaped_n}\n")
            f.write(f"包含真正换行: {has_real_newline}\n")
            f.write("\n--- 原始代码 (repr) ---\n")
            f.write(repr(raw_code))
            f.write("\n\n--- 原始代码 (raw) ---\n")
            f.write(raw_code)

        # 保存清理后代码
        with open(f"{debug_dir}/cleaned_code_{timestamp}.txt", "w") as f:
            f.write("=" * 60 + "\n")
            f.write("清理后代码\n")
            f.write("=" * 60 + "\n")
            f.write(f"长度: {len(cleaned_code)} 字符\n")
            f.write("\n--- 清理后代码 ---\n")
            f.write(cleaned_code)

            if error:
                f.write("\n\n" + "=" * 60 + "\n")
                f.write(f"语法错误: {error}\n")
                if hasattr(error, 'lineno') and error.lineno:
                    lines = cleaned_code.split('\n')
                    f.write(f"错误行号: {error.lineno}\n")
                    f.write("\n--- 问题代码上下文 ---\n")
                    start = max(0, error.lineno - 3)
                    end = min(len(lines), error.lineno + 2)
                    for i in range(start, end):
                        marker = ">>> " if i == error.lineno - 1 else "    "
                        f.write(f"{marker}Line {i+1}: {repr(lines[i])}\n")

        # 保存最新的调试文件路径（方便快速访问）
        with open(f"{debug_dir}/latest.txt", "w") as f:
            f.write(f"raw: {debug_dir}/raw_code_{timestamp}.txt\n")
            f.write(f"cleaned: {debug_dir}/cleaned_code_{timestamp}.txt\n")
            f.write(f"timestamp: {timestamp}\n")

        self.logger.info(f"[CodeWizard] 调试信息已保存到 {debug_dir}/")

    def _save_debug_log(self, step_name: str, content: str):
        """
        保存单步调试日志，便于追踪代码执行流程

        每次运行会创建一个带时间戳的目录，所有步骤保存在同一目录下
        """
        import os
        from datetime import datetime

        # 使用实例变量保存当前调试会话的目录
        if not hasattr(self, '_debug_session_dir'):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self._debug_session_dir = f"/tmp/codewizard_debug/session_{timestamp}"
            os.makedirs(self._debug_session_dir, exist_ok=True)
            self.logger.info(f"[CodeWizard] 调试会话目录: {self._debug_session_dir}")

        # 保存步骤日志
        file_path = f"{self._debug_session_dir}/{step_name}.txt"
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f"=== {step_name} ===\n")
            f.write(f"时间: {datetime.now().isoformat()}\n")
            f.write(f"长度: {len(content)} 字符\n")
            f.write("=" * 60 + "\n\n")
            f.write(content)

        self.logger.debug(f"[CodeWizard] 已保存: {file_path}")

    async def _execute_code(self, code: str) -> Dict[str, Any]:
        """
        安全执行Python代码

        特点：
        - 代码清理和格式修复
        - 代码安全检查
        - 隔离执行环境
        - 捕获输出和图表
        """
        self.logger.info(f"[CodeWizard] _execute_code 开始，输入类型: {type(code)}")

        # 确保 code 是字符串类型
        if isinstance(code, list):
            code = '\n'.join(str(c) for c in code)
            self.logger.info(f"[CodeWizard] 输入是list，已转换为字符串")
        elif not isinstance(code, str):
            code = str(code)
            self.logger.info(f"[CodeWizard] 输入非字符串，已转换")

        raw_code = code  # 保存原始代码用于调试
        self._save_debug_log("exec_1_input_raw", repr(raw_code))

        # 清理代码
        code = self._clean_code(code)
        self._save_debug_log("exec_2_after_clean", code)
        self.logger.info(f"[CodeWizard] 清理后代码行数: {code.count(chr(10)) + 1}, 长度: {len(code)}")

        # 语法预检查
        syntax_error = None
        try:
            compile(code, '<string>', 'exec')
            self.logger.info(f"[CodeWizard] ✅ 语法预检查: 通过")
            self._save_debug_log("exec_3_syntax", "PASSED")
        except SyntaxError as e:
            syntax_error = e
            self.logger.error(f"[CodeWizard] ❌ 语法预检查失败: {e}")
            self._save_debug_log("exec_3_syntax", f"FAILED: {e}\n\n错误行: {e.lineno}\n\n代码:\n{code}")
            # 保存调试信息
            self._save_debug_info(raw_code, code, e)

        # 安全检查
        if not self._is_code_safe(code):
            return {
                "success": False,
                "error": "Code contains forbidden operations",
                "output": "",
                "charts": []
            }

        try:
            # 在线程池中执行代码
            result = await asyncio.to_thread(self._execute_in_sandbox, code)
            return result
        except Exception as e:
            self.logger.error(f"Code execution error: {e}")
            return {
                "success": False,
                "error": str(e),
                "output": "",
                "charts": []
            }

    def _is_code_safe(self, code: str) -> bool:
        """检查代码安全性（使用正则表达式）"""
        import re

        for pattern in self.FORBIDDEN_PATTERNS:
            if re.search(pattern, code, re.IGNORECASE):
                self.logger.warning(f"Forbidden pattern detected: {pattern}")
                return False

        return True

    def _execute_in_sandbox(self, code: str) -> Dict[str, Any]:
        """
        沙箱执行代码

        注意：这是一个简化的沙箱，生产环境应使用更安全的方案
        如 Docker 容器或专门的代码执行服务
        """
        self.logger.info(f"[CodeWizard] _execute_in_sandbox 开始执行")
        self._save_debug_log("sandbox_1_code_input", code)

        import matplotlib
        matplotlib.use('Agg')  # 非交互式后端
        import matplotlib.pyplot as plt

        # 预导入所有允许的模块
        import pandas as pd
        import numpy as np
        import seaborn as sns
        import datetime
        import math
        import statistics
        import json as json_module
        import collections
        import re as re_module

        self.logger.info(f"[CodeWizard] 沙箱环境准备完成，matplotlib backend: {matplotlib.get_backend()}")

        # 白名单基础模块
        allowed_base_modules = [
            'pandas', 'numpy', 'matplotlib', 'seaborn',
            'datetime', 'math', 'statistics', 'json', 'collections', 're'
        ]

        # 保存原始的 __import__ 函数
        import builtins
        original_import = builtins.__import__

        def safe_import(name, globals=None, locals=None, fromlist=(), level=0):
            """安全的 import 函数，只允许白名单模块"""
            # 检查模块是否在白名单中
            base_module = name.split('.')[0]
            if base_module in allowed_base_modules:
                # 使用真实的 import 来处理（这样可以正确处理 fromlist）
                return original_import(name, globals, locals, fromlist, level)
            raise ImportError(f"Import of '{name}' is not allowed in sandbox")

        # 准备执行环境
        exec_globals = {
            '__builtins__': {
                '__import__': safe_import,
                'print': print,
                'len': len,
                'range': range,
                'enumerate': enumerate,
                'zip': zip,
                'map': map,
                'filter': filter,
                'sorted': sorted,
                'sum': sum,
                'min': min,
                'max': max,
                'abs': abs,
                'round': round,
                'int': int,
                'float': float,
                'str': str,
                'list': list,
                'dict': dict,
                'tuple': tuple,
                'set': set,
                'bool': bool,
                'True': True,
                'False': False,
                'None': None,
                'isinstance': isinstance,
                'type': type,
                'getattr': getattr,
                'setattr': setattr,
                'hasattr': hasattr,
                'callable': callable,
                'iter': iter,
                'next': next,
                'reversed': reversed,
                'slice': slice,
                'all': all,
                'any': any,
                'chr': chr,
                'ord': ord,
                'hex': hex,
                'bin': bin,
                'oct': oct,
                'pow': pow,
                'divmod': divmod,
                'format': format,
                'repr': repr,
                'hash': hash,
                'id': id,
                'input': lambda *args: '',  # 禁用 input
                'open': None,  # 禁用 open
            },
            # 直接提供模块引用（无需import即可使用）
            'pd': pd,
            'np': np,
            'plt': plt,
            'sns': sns,
            'pandas': pd,
            'numpy': np,
            'matplotlib': matplotlib,
            # 额外的常用模块
            'datetime': datetime,
            'math': math,
            'statistics': statistics,
            'json': json_module,
            'collections': collections,
            're': re_module,
        }

        # 捕获输出
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()
        charts = []

        try:
            # ========== 预设高级图表样式 ==========
            # 中文字体
            chinese_fonts = [
                'Heiti TC', 'STHeiti', 'PingFang HK', 'Hiragino Sans GB',
                'SimHei', 'Microsoft YaHei', 'Arial Unicode MS', 'DejaVu Sans'
            ]
            plt.rcParams['font.sans-serif'] = chinese_fonts
            plt.rcParams['axes.unicode_minus'] = False

            # 高级默认样式
            plt.rcParams['figure.figsize'] = [12, 7]
            plt.rcParams['figure.dpi'] = 200
            plt.rcParams['font.size'] = 12
            plt.rcParams['axes.titlesize'] = 18
            plt.rcParams['axes.titleweight'] = 'bold'
            plt.rcParams['axes.labelsize'] = 14
            plt.rcParams['xtick.labelsize'] = 12
            plt.rcParams['ytick.labelsize'] = 12
            plt.rcParams['legend.fontsize'] = 12
            plt.rcParams['axes.spines.top'] = False
            plt.rcParams['axes.spines.right'] = False
            plt.rcParams['axes.grid'] = True
            plt.rcParams['grid.alpha'] = 0.3
            plt.rcParams['grid.linestyle'] = '--'

            self.logger.info(f"[CodeWizard] 开始 exec()...")
            self._save_debug_log("sandbox_2_before_exec", f"即将执行代码，长度: {len(code)} 字符")

            with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                exec(code, exec_globals)

            self.logger.info(f"[CodeWizard] exec() 完成")

            # exec 之后再次强制设置字体（防止 LLM 代码里的 sns.set() 等覆盖）
            plt.rcParams['font.sans-serif'] = [
                'Heiti TC', 'STHeiti', 'PingFang HK', 'Hiragino Sans GB',
                'SimHei', 'Microsoft YaHei', 'Arial Unicode MS', 'DejaVu Sans'
            ]
            plt.rcParams['axes.unicode_minus'] = False

            # 检查是否生成了图表
            fig = plt.gcf()
            stdout_value = stdout_capture.getvalue()
            stderr_value = stderr_capture.getvalue()

            self.logger.info(f"[CodeWizard] exec() 输出: stdout={len(stdout_value)}字符, stderr={len(stderr_value)}字符")
            self._save_debug_log("sandbox_3_exec_output", f"stdout:\n{stdout_value}\n\nstderr:\n{stderr_value}")

            if fig.get_axes():
                self.logger.info(f"[CodeWizard] 检测到图表，开始捕获...")
                # 重新应用字体到当前图表的所有文本元素
                chinese_fonts = ['Heiti TC', 'STHeiti', 'PingFang HK', 'Hiragino Sans GB', 'Arial Unicode MS']
                for ax in fig.get_axes():
                    for text in ax.get_xticklabels() + ax.get_yticklabels():
                        text.set_fontfamily(chinese_fonts)
                    if ax.get_title():
                        ax.title.set_fontfamily(chinese_fonts)
                    if ax.get_xlabel():
                        ax.xaxis.label.set_fontfamily(chinese_fonts)
                    if ax.get_ylabel():
                        ax.yaxis.label.set_fontfamily(chinese_fonts)

                buf = io.BytesIO()
                fig.savefig(buf, format='png', dpi=150, bbox_inches='tight', facecolor='white')
                buf.seek(0)
                chart_b64 = base64.b64encode(buf.read()).decode('utf-8')
                charts.append(chart_b64)
                plt.close(fig)
                self.logger.info(f"[CodeWizard] 图表捕获成功，base64长度: {len(chart_b64)}")
            else:
                self.logger.info(f"[CodeWizard] 未检测到图表")

            result = {
                "success": True,
                "output": stdout_value,
                "error": stderr_value if stderr_value else None,
                "charts": charts
            }
            self._save_debug_log("sandbox_4_result", f"success=True, charts={len(charts)}, output_len={len(stdout_value)}")
            self.logger.info(f"[CodeWizard] ✅ 沙箱执行成功，图表数: {len(charts)}")
            return result

        except Exception as e:
            plt.close('all')
            stdout_value = stdout_capture.getvalue()
            error_msg = str(e)
            self.logger.error(f"[CodeWizard] ❌ 沙箱执行失败: {error_msg}")
            self._save_debug_log("sandbox_4_error", f"error: {error_msg}\n\nstdout:\n{stdout_value}\n\ntraceback:\n{repr(e)}")
            return {
                "success": False,
                "output": stdout_value,
                "error": error_msg,
                "charts": []
            }
