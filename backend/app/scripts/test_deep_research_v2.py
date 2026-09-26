"""
DeepResearch V2.0 端到端测试

测试完整的多智能体研究工作流程：
1. ChiefArchitect - 规划研究大纲
2. DeepScout - 执行网络搜索（Bocha API）
3. CodeWizard - 数据分析
4. LeadWriter - 撰写报告
5. CriticMaster - 审核质量

使用方法：
    python -m scripts.test_deep_research_v2
"""

import os
import sys
import asyncio
import logging
from datetime import datetime

# 确保能导入项目模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger("E2E_Test")


async def test_full_workflow():
    """测试完整的研究工作流程"""
    from service.deep_research_v2.service import DeepResearchV2Service

    print("\n" + "=" * 60)
    print("DeepResearch V2.0 端到端测试")
    print("=" * 60)

    # 检查环境变量
    dashscope_key = os.getenv("DASHSCOPE_API_KEY")
    bocha_key = os.getenv("BOCHA_API_KEY")

    if not dashscope_key:
        print("❌ 错误: 未设置 DASHSCOPE_API_KEY 环境变量")
        return False

    if not bocha_key:
        print("❌ 错误: 未设置 BOCHA_API_KEY 环境变量")
        return False

    print(f"✅ DASHSCOPE_API_KEY: {dashscope_key[:8]}...")
    print(f"✅ BOCHA_API_KEY: {bocha_key[:8]}...")

    # 创建服务
    service = DeepResearchV2Service(
        llm_api_key=dashscope_key,
        search_api_key=bocha_key,
        model="qwen-max",
        max_iterations=2  # 减少迭代次数以加速测试
    )

    # 测试查询
    query = "新能源汽车2024年市场现状与发展趋势"
    print(f"\n📝 测试查询: {query}")
    print("-" * 60)

    # 收集事件
    events = []
    phases_seen = set()
    error_count = 0

    start_time = datetime.now()

    try:
        async for sse_data in service.research(query):
            # 解析 SSE 数据
            if sse_data.startswith("data: "):
                data_str = sse_data[6:].strip()
                if data_str == "[DONE]":
                    print("\n✅ 收到结束标记 [DONE]")
                    break

                import json
                try:
                    event = json.loads(data_str)
                    events.append(event)

                    event_type = event.get("type", "unknown")

                    # 记录阶段
                    if event_type == "phase":
                        phase = event.get("phase", "")
                        phases_seen.add(phase)
                        print(f"\n🔄 阶段: {phase} - {event.get('content', '')}")

                    # 记录大纲
                    elif event_type == "outline":
                        outline = event.get("outline", [])
                        print(f"\n📋 大纲生成: {len(outline)} 个章节")
                        for i, section in enumerate(outline[:3], 1):
                            title = section.get("title", "未知")
                            print(f"   {i}. {title}")
                        if len(outline) > 3:
                            print(f"   ... 还有 {len(outline) - 3} 个章节")

                    # 记录搜索结果
                    elif event_type == "search_result":
                        section_id = event.get("section_id", "")
                        sources_count = event.get("sources_count", 0)
                        print(f"   🔍 搜索完成: {section_id} ({sources_count} 个来源)")

                    # 记录数据分析
                    elif event_type == "analysis_result":
                        data_points = event.get("data_points", [])
                        charts = event.get("charts", [])
                        print(f"   📊 数据分析: {len(data_points)} 个数据点, {len(charts)} 个图表")

                    # 记录报告写作
                    elif event_type == "section_written":
                        section_id = event.get("section_id", "")
                        print(f"   ✍️ 章节完成: {section_id}")

                    # 记录审核结果
                    elif event_type == "review_result":
                        score = event.get("score", 0)
                        passed = event.get("passed", False)
                        print(f"   🔍 审核结果: 分数 {score}, {'通过' if passed else '需修订'}")

                    # 记录最终报告
                    elif event_type == "research_complete":
                        report = event.get("final_report", "")
                        quality = event.get("quality_score", 0)
                        facts = event.get("facts_count", 0)
                        charts = event.get("charts_count", 0)
                        refs = len(event.get("references", []))
                        print(f"\n📄 最终报告:")
                        print(f"   - 质量分数: {quality}")
                        print(f"   - 事实数量: {facts}")
                        print(f"   - 图表数量: {charts}")
                        print(f"   - 参考来源: {refs}")
                        print(f"   - 报告长度: {len(report)} 字符")

                    # 记录错误
                    elif event_type == "error":
                        error_count += 1
                        print(f"   ❌ 错误: {event.get('content', '')}")

                    # 状态更新
                    elif event_type == "status":
                        print(f"   ℹ️ {event.get('content', '')}")

                except json.JSONDecodeError:
                    pass

    except Exception as e:
        print(f"\n❌ 执行异常: {e}")
        import traceback
        traceback.print_exc()
        return False

    # 统计结果
    elapsed = (datetime.now() - start_time).total_seconds()

    print("\n" + "=" * 60)
    print("测试结果统计")
    print("=" * 60)
    print(f"⏱️ 总耗时: {elapsed:.1f} 秒")
    print(f"📨 事件总数: {len(events)}")
    print(f"🔄 完成阶段: {', '.join(sorted(phases_seen))}")
    print(f"❌ 错误数量: {error_count}")

    # 验证关键阶段
    expected_phases = {"planning", "researching", "analyzing", "writing", "reviewing"}
    missing_phases = expected_phases - phases_seen

    if missing_phases:
        print(f"\n⚠️ 缺失阶段: {', '.join(missing_phases)}")
        return False

    # 检查是否有最终报告
    has_final_report = any(e.get("type") == "research_complete" for e in events)

    if has_final_report and error_count == 0:
        print("\n" + "=" * 60)
        print("✅ 端到端测试通过!")
        print("=" * 60)
        return True
    else:
        print("\n" + "=" * 60)
        print("❌ 测试失败")
        if not has_final_report:
            print("   - 未生成最终报告")
        if error_count > 0:
            print(f"   - 有 {error_count} 个错误")
        print("=" * 60)
        return False


async def test_individual_agents():
    """单独测试各个 Agent"""
    print("\n" + "=" * 60)
    print("Agent 单元测试")
    print("=" * 60)

    dashscope_key = os.getenv("DASHSCOPE_API_KEY", "")
    bocha_key = os.getenv("BOCHA_API_KEY", "")
    llm_base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"

    if not dashscope_key or not bocha_key:
        print("❌ 缺少必要的环境变量")
        return False

    # 测试 ChiefArchitect
    print("\n1. 测试 ChiefArchitect (规划)")
    try:
        from service.deep_research_v2.agents import ChiefArchitect
        from service.deep_research_v2.state import create_initial_state

        architect = ChiefArchitect(dashscope_key, llm_base_url, "qwen-max")
        state = create_initial_state("新能源汽车发展趋势", "test-session-1")

        result = await architect.process(state)
        outline = result.get("outline", [])

        if outline and len(outline) > 0:
            print(f"   ✅ 成功生成 {len(outline)} 个章节的大纲")
        else:
            print("   ❌ 大纲生成失败")
            return False

    except Exception as e:
        print(f"   ❌ ChiefArchitect 测试失败: {e}")
        return False

    # 测试 DeepScout
    print("\n2. 测试 DeepScout (搜索)")
    try:
        from service.deep_research_v2.agents import DeepScout

        scout = DeepScout(dashscope_key, llm_base_url, bocha_key, "qwen-plus")

        # 使用上一步的结果
        result["phase"] = "researching"
        result = await scout.process(result)
        facts = result.get("facts", [])
        references = result.get("references", [])

        if facts or references:
            print(f"   ✅ 搜索完成: {len(facts)} 个事实, {len(references)} 个来源")
        else:
            print("   ⚠️ 搜索完成但无结果（可能是 API 问题）")

    except Exception as e:
        print(f"   ❌ DeepScout 测试失败: {e}")
        return False

    # 测试 CodeWizard
    print("\n3. 测试 CodeWizard (分析)")
    try:
        from service.deep_research_v2.agents import CodeWizard

        wizard = CodeWizard(dashscope_key, llm_base_url, "qwen-max")
        result["phase"] = "analyzing"
        result = await wizard.process(result)

        insights = result.get("insights", [])
        data_points = result.get("data_points", [])

        print(f"   ✅ 分析完成: {len(insights)} 个洞察, {len(data_points)} 个数据点")

    except Exception as e:
        print(f"   ❌ CodeWizard 测试失败: {e}")
        return False

    print("\n✅ Agent 单元测试全部通过!")
    return True


async def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("DeepResearch V2.0 端到端测试套件")
    print("时间:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("=" * 60)

    # 先运行单元测试
    unit_passed = await test_individual_agents()

    if not unit_passed:
        print("\n⚠️ 单元测试失败，跳过端到端测试")
        return

    # 运行端到端测试
    e2e_passed = await test_full_workflow()

    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    print(f"Agent 单元测试: {'✅ 通过' if unit_passed else '❌ 失败'}")
    print(f"端到端测试: {'✅ 通过' if e2e_passed else '❌ 失败'}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
