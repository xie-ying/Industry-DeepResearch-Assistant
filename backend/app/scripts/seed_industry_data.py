"""
行业数据库初始化脚本 - 智慧交通行业示例数据
"""
import sys
import os
from datetime import date

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import SessionLocal, engine, Base
from models.industry_data import IndustryStats, CompanyData, PolicyData


def seed_industry_stats(db):
    """插入行业统计数据"""
    stats_data = [
        # 市场规模数据
        {"industry_name": "智慧交通", "metric_name": "市场规模", "metric_value": 2850, "unit": "亿元", "year": 2023, "quarter": None, "region": "全国", "source": "中国智能交通协会"},
        {"industry_name": "智慧交通", "metric_name": "市场规模", "metric_value": 3200, "unit": "亿元", "year": 2024, "quarter": None, "region": "全国", "source": "中国智能交通协会"},
        {"industry_name": "智慧交通", "metric_name": "市场规模预测", "metric_value": 3680, "unit": "亿元", "year": 2025, "quarter": None, "region": "全国", "source": "中国智能交通协会"},

        # 增长率
        {"industry_name": "智慧交通", "metric_name": "同比增长率", "metric_value": 12.3, "unit": "%", "year": 2024, "quarter": None, "region": "全国", "source": "国家统计局"},
        {"industry_name": "智慧交通", "metric_name": "同比增长率", "metric_value": 15.0, "unit": "%", "year": 2025, "quarter": None, "region": "全国", "source": "国家统计局"},

        # 细分市场
        {"industry_name": "智慧交通", "metric_name": "智能公交市场规模", "metric_value": 580, "unit": "亿元", "year": 2024, "quarter": None, "region": "全国", "source": "艾瑞咨询"},
        {"industry_name": "智慧交通", "metric_name": "智慧高速市场规模", "metric_value": 720, "unit": "亿元", "year": 2024, "quarter": None, "region": "全国", "source": "艾瑞咨询"},
        {"industry_name": "智慧交通", "metric_name": "车路协同市场规模", "metric_value": 450, "unit": "亿元", "year": 2024, "quarter": None, "region": "全国", "source": "艾瑞咨询"},
        {"industry_name": "智慧交通", "metric_name": "智慧停车市场规模", "metric_value": 380, "unit": "亿元", "year": 2024, "quarter": None, "region": "全国", "source": "艾瑞咨询"},
        {"industry_name": "智慧交通", "metric_name": "交通大脑市场规模", "metric_value": 520, "unit": "亿元", "year": 2024, "quarter": None, "region": "全国", "source": "艾瑞咨询"},

        # 投资数据
        {"industry_name": "智慧交通", "metric_name": "固定资产投资", "metric_value": 1850, "unit": "亿元", "year": 2024, "quarter": None, "region": "全国", "source": "交通运输部"},
        {"industry_name": "智慧交通", "metric_name": "研发投入", "metric_value": 320, "unit": "亿元", "year": 2024, "quarter": None, "region": "全国", "source": "工信部"},

        # 区域数据
        {"industry_name": "智慧交通", "metric_name": "市场规模", "metric_value": 680, "unit": "亿元", "year": 2024, "quarter": None, "region": "华东地区", "source": "中国智能交通协会"},
        {"industry_name": "智慧交通", "metric_name": "市场规模", "metric_value": 520, "unit": "亿元", "year": 2024, "quarter": None, "region": "华南地区", "source": "中国智能交通协会"},
        {"industry_name": "智慧交通", "metric_name": "市场规模", "metric_value": 480, "unit": "亿元", "year": 2024, "quarter": None, "region": "华北地区", "source": "中国智能交通协会"},

        # 季度数据
        {"industry_name": "智慧交通", "metric_name": "营收", "metric_value": 720, "unit": "亿元", "year": 2024, "quarter": 1, "region": "全国", "source": "行业协会"},
        {"industry_name": "智慧交通", "metric_name": "营收", "metric_value": 780, "unit": "亿元", "year": 2024, "quarter": 2, "region": "全国", "source": "行业协会"},
        {"industry_name": "智慧交通", "metric_name": "营收", "metric_value": 850, "unit": "亿元", "year": 2024, "quarter": 3, "region": "全国", "source": "行业协会"},
        {"industry_name": "智慧交通", "metric_name": "营收", "metric_value": 850, "unit": "亿元", "year": 2024, "quarter": 4, "region": "全国", "source": "行业协会"},

        # 其他指标
        {"industry_name": "智慧交通", "metric_name": "从业人员数量", "metric_value": 85, "unit": "万人", "year": 2024, "quarter": None, "region": "全国", "source": "人社部"},
        {"industry_name": "智慧交通", "metric_name": "企业数量", "metric_value": 3200, "unit": "家", "year": 2024, "quarter": None, "region": "全国", "source": "工商总局"},
        {"industry_name": "智慧交通", "metric_name": "专利申请数", "metric_value": 12500, "unit": "件", "year": 2024, "quarter": None, "region": "全国", "source": "国家知识产权局"},
    ]

    for data in stats_data:
        stat = IndustryStats(**data)
        db.add(stat)

    db.commit()
    print(f"✓ 插入 {len(stats_data)} 条行业统计数据")


def seed_company_data(db):
    """插入企业数据"""
    companies = [
        # 头部企业
        {"company_name": "海康威视", "stock_code": "002415.SZ", "industry": "智慧交通", "sub_industry": "智能监控", "revenue": 893.5, "net_profit": 141.2, "gross_margin": 44.3, "market_cap": 3200, "employees": 52000, "market_share": 15.2, "year": 2024, "quarter": 3, "data_source": "公司财报"},
        {"company_name": "大华股份", "stock_code": "002236.SZ", "industry": "智慧交通", "sub_industry": "智能监控", "revenue": 328.6, "net_profit": 28.5, "gross_margin": 38.6, "market_cap": 620, "employees": 18000, "market_share": 8.5, "year": 2024, "quarter": 3, "data_source": "公司财报"},
        {"company_name": "千方科技", "stock_code": "002373.SZ", "industry": "智慧交通", "sub_industry": "交通信息化", "revenue": 85.2, "net_profit": 5.8, "gross_margin": 32.1, "market_cap": 180, "employees": 6500, "market_share": 5.2, "year": 2024, "quarter": 3, "data_source": "公司财报"},
        {"company_name": "易华录", "stock_code": "300212.SZ", "industry": "智慧交通", "sub_industry": "数据存储", "revenue": 42.3, "net_profit": 2.1, "gross_margin": 28.5, "market_cap": 95, "employees": 3200, "market_share": 3.8, "year": 2024, "quarter": 3, "data_source": "公司财报"},
        {"company_name": "银江技术", "stock_code": "300020.SZ", "industry": "智慧交通", "sub_industry": "智慧城市", "revenue": 38.6, "net_profit": 1.5, "gross_margin": 25.2, "market_cap": 75, "employees": 2800, "market_share": 2.5, "year": 2024, "quarter": 3, "data_source": "公司财报"},

        # 中型企业
        {"company_name": "金溢科技", "stock_code": "002869.SZ", "industry": "智慧交通", "sub_industry": "ETC", "revenue": 28.5, "net_profit": 3.2, "gross_margin": 42.1, "market_cap": 68, "employees": 1800, "market_share": 4.2, "year": 2024, "quarter": 3, "data_source": "公司财报"},
        {"company_name": "万集科技", "stock_code": "300552.SZ", "industry": "智慧交通", "sub_industry": "ETC", "revenue": 22.1, "net_profit": 2.5, "gross_margin": 38.5, "market_cap": 52, "employees": 1500, "market_share": 3.5, "year": 2024, "quarter": 3, "data_source": "公司财报"},
        {"company_name": "皖通科技", "stock_code": "002331.SZ", "industry": "智慧交通", "sub_industry": "高速公路信息化", "revenue": 18.6, "net_profit": 1.2, "gross_margin": 28.3, "market_cap": 35, "employees": 1200, "market_share": 2.8, "year": 2024, "quarter": 3, "data_source": "公司财报"},
        {"company_name": "中远海科", "stock_code": "002401.SZ", "industry": "智慧交通", "sub_industry": "港口信息化", "revenue": 15.8, "net_profit": 1.8, "gross_margin": 35.2, "market_cap": 42, "employees": 980, "market_share": 2.2, "year": 2024, "quarter": 3, "data_source": "公司财报"},
        {"company_name": "四维图新", "stock_code": "002405.SZ", "industry": "智慧交通", "sub_industry": "高精地图", "revenue": 32.5, "net_profit": -2.1, "gross_margin": 45.6, "market_cap": 185, "employees": 3500, "market_share": 6.8, "year": 2024, "quarter": 3, "data_source": "公司财报"},

        # 新兴企业
        {"company_name": "蘑菇车联", "stock_code": "未上市", "industry": "智慧交通", "sub_industry": "车路协同", "revenue": 8.5, "net_profit": -3.2, "gross_margin": 25.0, "market_cap": None, "employees": 1200, "market_share": 1.5, "year": 2024, "quarter": 3, "data_source": "企业公告"},
        {"company_name": "希迪智驾", "stock_code": "未上市", "industry": "智慧交通", "sub_industry": "自动驾驶", "revenue": 5.2, "net_profit": -2.8, "gross_margin": 18.5, "market_cap": None, "employees": 800, "market_share": 0.8, "year": 2024, "quarter": 3, "data_source": "企业公告"},

        # 历史数据
        {"company_name": "海康威视", "stock_code": "002415.SZ", "industry": "智慧交通", "sub_industry": "智能监控", "revenue": 831.2, "net_profit": 128.5, "gross_margin": 43.8, "market_cap": 2850, "employees": 48000, "market_share": 14.5, "year": 2023, "quarter": 4, "data_source": "公司财报"},
        {"company_name": "大华股份", "stock_code": "002236.SZ", "industry": "智慧交通", "sub_industry": "智能监控", "revenue": 305.2, "net_profit": 25.2, "gross_margin": 37.2, "market_cap": 550, "employees": 16500, "market_share": 8.0, "year": 2023, "quarter": 4, "data_source": "公司财报"},
    ]

    for data in companies:
        company = CompanyData(**data)
        db.add(company)

    db.commit()
    print(f"✓ 插入 {len(companies)} 条企业数据")


def seed_policy_data(db):
    """插入政策数据"""
    policies = [
        {
            "policy_name": "交通强国建设纲要",
            "policy_number": "中发〔2019〕39号",
            "department": "中共中央、国务院",
            "level": "国家级",
            "publish_date": date(2019, 9, 19),
            "effective_date": date(2019, 9, 19),
            "category": "发展规划",
            "industry": "智慧交通",
            "summary": "明确到2035年基本建成交通强国，到本世纪中叶全面建成交通强国的战略目标。强调推进智慧交通发展，推动大数据、互联网、人工智能、区块链等新技术与交通行业深度融合。",
            "impact_level": "重大"
        },
        {
            "policy_name": "智能汽车创新发展战略",
            "policy_number": "发改产业〔2020〕202号",
            "department": "国家发展改革委等11部门",
            "level": "国家级",
            "publish_date": date(2020, 2, 24),
            "effective_date": date(2020, 2, 24),
            "category": "发展战略",
            "industry": "智慧交通",
            "summary": "提出到2025年实现有条件自动驾驶的智能汽车达到规模化生产，实现高度自动驾驶的智能汽车在特定环境下市场化应用。",
            "impact_level": "重大"
        },
        {
            "policy_name": "数字交通发展规划纲要",
            "policy_number": "交规划发〔2019〕115号",
            "department": "交通运输部",
            "level": "国家级",
            "publish_date": date(2019, 7, 25),
            "effective_date": date(2019, 7, 25),
            "category": "发展规划",
            "industry": "智慧交通",
            "summary": "提出到2025年交通运输基础设施和运载装备全要素、全周期的数字化升级迈出新步伐，数字化采集体系和网络化传输体系基本形成。",
            "impact_level": "重大"
        },
        {
            "policy_name": "关于促进道路交通自动驾驶技术发展和应用的指导意见",
            "policy_number": "交公路发〔2020〕123号",
            "department": "交通运输部",
            "level": "国家级",
            "publish_date": date(2020, 12, 23),
            "effective_date": date(2020, 12, 23),
            "category": "技术规范",
            "industry": "智慧交通",
            "summary": "鼓励有条件的地方开展自动驾驶车辆共享、摆渡接驳、智能泊车等试运行及商业运营服务。",
            "impact_level": "重大"
        },
        {
            "policy_name": "十四五现代综合交通运输体系发展规划",
            "policy_number": "国发〔2022〕2号",
            "department": "国务院",
            "level": "国家级",
            "publish_date": date(2022, 1, 18),
            "effective_date": date(2022, 1, 18),
            "category": "发展规划",
            "industry": "智慧交通",
            "summary": "到2025年综合交通运输基本实现一体化融合发展，智能化、绿色化取得实质性突破。",
            "impact_level": "重大"
        },
        {
            "policy_name": "关于推动城市公共交通优先发展的实施意见",
            "policy_number": "交运发〔2023〕85号",
            "department": "交通运输部",
            "level": "国家级",
            "publish_date": date(2023, 6, 15),
            "effective_date": date(2023, 7, 1),
            "category": "实施意见",
            "industry": "智慧交通",
            "summary": "推进公交智能化建设，提升公交运营效率，鼓励发展需求响应式公交服务。",
            "impact_level": "一般"
        },
        {
            "policy_name": "智慧城市基础设施与智能网联汽车协同发展试点通知",
            "policy_number": "建城〔2021〕30号",
            "department": "住建部、工信部",
            "level": "国家级",
            "publish_date": date(2021, 5, 6),
            "effective_date": date(2021, 5, 6),
            "category": "试点通知",
            "industry": "智慧交通",
            "summary": "确定北京、上海、广州等16个城市为智慧城市基础设施与智能网联汽车协同发展试点城市。",
            "impact_level": "重大"
        },
        {
            "policy_name": "车联网（智能网联汽车）产业发展行动计划",
            "policy_number": "工信部联科〔2018〕283号",
            "department": "工业和信息化部",
            "level": "国家级",
            "publish_date": date(2018, 12, 27),
            "effective_date": date(2018, 12, 27),
            "category": "行动计划",
            "industry": "智慧交通",
            "summary": "到2020年车联网用户渗透率达到30%以上，新车驾驶辅助系统(L2)搭载率达到30%以上。",
            "impact_level": "重大"
        },
        {
            "policy_name": "关于加快推进ETC应用发展的指导意见",
            "policy_number": "交公路发〔2019〕68号",
            "department": "交通运输部",
            "level": "国家级",
            "publish_date": date(2019, 5, 16),
            "effective_date": date(2019, 5, 16),
            "category": "指导意见",
            "industry": "智慧交通",
            "summary": "加快推进高速公路电子不停车快捷收费应用服务实施方案，到2019年底ETC车道成为主要收费车道。",
            "impact_level": "一般"
        },
        {
            "policy_name": "广东省智慧交通十四五发展规划",
            "policy_number": "粤交规〔2022〕15号",
            "department": "广东省交通运输厅",
            "level": "省级",
            "publish_date": date(2022, 3, 20),
            "effective_date": date(2022, 3, 20),
            "category": "发展规划",
            "industry": "智慧交通",
            "summary": "到2025年广东省智慧交通发展水平进入全国前列，建成一批智慧公路、智慧港口示范项目。",
            "impact_level": "一般"
        },
        {
            "policy_name": "上海市智能网联汽车创新发展工作实施方案",
            "policy_number": "沪府办发〔2023〕12号",
            "department": "上海市人民政府",
            "level": "省级",
            "publish_date": date(2023, 8, 10),
            "effective_date": date(2023, 8, 10),
            "category": "实施方案",
            "industry": "智慧交通",
            "summary": "推进智能网联汽车在浦东新区开展创新应用，探索自动驾驶出租车、无人配送等商业化运营。",
            "impact_level": "一般"
        },
        {
            "policy_name": "北京市自动驾驶汽车条例",
            "policy_number": "北京市人大常委会公告〔2024〕1号",
            "department": "北京市人大常委会",
            "level": "省级",
            "publish_date": date(2024, 4, 26),
            "effective_date": date(2024, 7, 1),
            "category": "地方法规",
            "industry": "智慧交通",
            "summary": "全国首部自动驾驶地方立法，明确自动驾驶汽车上路权限、事故责任划分等关键问题。",
            "impact_level": "重大"
        },
    ]

    for data in policies:
        policy = PolicyData(**data)
        db.add(policy)

    db.commit()
    print(f"✓ 插入 {len(policies)} 条政策数据")


def main():
    """主函数"""
    print("开始初始化行业数据库...")

    # 创建表（如果不存在）
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
        # 清空现有数据
        db.query(IndustryStats).delete()
        db.query(CompanyData).delete()
        db.query(PolicyData).delete()
        db.commit()
        print("✓ 清空现有数据")

        # 插入新数据
        seed_industry_stats(db)
        seed_company_data(db)
        seed_policy_data(db)

        print("\n数据库初始化完成!")
        print(f"  - 行业统计: {db.query(IndustryStats).count()} 条")
        print(f"  - 企业数据: {db.query(CompanyData).count()} 条")
        print(f"  - 政策数据: {db.query(PolicyData).count()} 条")

    except Exception as e:
        db.rollback()
        print(f"错误: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
