"""
初始化行业数据表并插入示例数据

使用方法：
    python -m scripts.init_industry_data
"""
import sys
import os
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from core.database import engine, Base
# 导入所有模型以确保表被创建
from models import (
    User, ChatSession, ChatMessage, ChatAttachment, LongTermMemory,
    KnowledgeBase, Document, IndustryStats, CompanyData, PolicyData
)


def create_tables():
    """创建数据表"""
    print("Creating industry data tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully!")


def insert_sample_data():
    """插入示例数据"""
    from sqlalchemy.orm import sessionmaker
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:
        # 检查是否已有数据
        existing = db.query(IndustryStats).first()
        if existing:
            print("Sample data already exists, skipping...")
            return

        print("Inserting sample industry stats...")

        # 新能源汽车行业统计数据
        ev_stats = [
            IndustryStats(
                industry_name="新能源汽车",
                metric_name="销量",
                metric_value=949.5,
                unit="万辆",
                year=2023,
                region="全国",
                source="中国汽车工业协会"
            ),
            IndustryStats(
                industry_name="新能源汽车",
                metric_name="销量",
                metric_value=1200,
                unit="万辆",
                year=2024,
                region="全国",
                source="中国汽车工业协会",
                notes="预测数据"
            ),
            IndustryStats(
                industry_name="新能源汽车",
                metric_name="市场渗透率",
                metric_value=35.8,
                unit="%",
                year=2023,
                region="全国",
                source="乘联会"
            ),
            IndustryStats(
                industry_name="新能源汽车",
                metric_name="市场渗透率",
                metric_value=45,
                unit="%",
                year=2024,
                region="全国",
                source="乘联会",
                notes="预测数据"
            ),
            IndustryStats(
                industry_name="新能源汽车",
                metric_name="出口量",
                metric_value=120.3,
                unit="万辆",
                year=2023,
                region="全国",
                source="海关总署"
            ),
            IndustryStats(
                industry_name="动力电池",
                metric_name="装车量",
                metric_value=387.7,
                unit="GWh",
                year=2023,
                region="全国",
                source="中国汽车动力电池产业创新联盟"
            ),
            IndustryStats(
                industry_name="充电桩",
                metric_name="保有量",
                metric_value=859.6,
                unit="万台",
                year=2023,
                region="全国",
                source="中国充电联盟"
            ),
        ]
        db.add_all(ev_stats)

        print("Inserting sample company data...")

        # 企业数据
        companies = [
            CompanyData(
                company_name="比亚迪",
                stock_code="002594.SZ",
                industry="新能源汽车",
                sub_industry="整车制造",
                revenue=6023.15,
                net_profit=300.41,
                market_share=35.0,
                employees=703000,
                year=2023,
                data_source="年报"
            ),
            CompanyData(
                company_name="特斯拉中国",
                stock_code="TSLA",
                industry="新能源汽车",
                sub_industry="整车制造",
                revenue=2100,
                market_share=15.5,
                year=2023,
                data_source="财报估算"
            ),
            CompanyData(
                company_name="蔚来汽车",
                stock_code="NIO",
                industry="新能源汽车",
                sub_industry="整车制造",
                revenue=556.18,
                net_profit=-207.2,
                market_share=3.5,
                employees=32000,
                year=2023,
                data_source="年报"
            ),
            CompanyData(
                company_name="理想汽车",
                stock_code="LI",
                industry="新能源汽车",
                sub_industry="整车制造",
                revenue=1238.5,
                net_profit=118.1,
                market_share=5.0,
                employees=31591,
                year=2023,
                data_source="年报"
            ),
            CompanyData(
                company_name="宁德时代",
                stock_code="300750.SZ",
                industry="动力电池",
                sub_industry="电池制造",
                revenue=4009.17,
                net_profit=441.21,
                market_share=43.11,
                employees=124000,
                year=2023,
                data_source="年报"
            ),
        ]
        db.add_all(companies)

        print("Inserting sample policy data...")

        # 政策数据
        policies = [
            PolicyData(
                policy_name="关于延续和优化新能源汽车车辆购置税减免政策的公告",
                policy_number="财政部 税务总局 工业和信息化部公告2023年第10号",
                department="财政部、税务总局、工业和信息化部",
                level="国家级",
                publish_date=date(2023, 6, 21),
                effective_date=date(2024, 1, 1),
                category="财税政策",
                industry="新能源汽车",
                summary="延续新能源汽车购置税减免政策至2027年底，对购置日期在2024年1月1日至2025年12月31日期间的新能源汽车免征车辆购置税",
                impact_level="重大"
            ),
            PolicyData(
                policy_name="新能源汽车产业发展规划(2021-2035年)",
                department="国务院办公厅",
                level="国家级",
                publish_date=date(2020, 11, 2),
                category="产业规划",
                industry="新能源汽车",
                summary="到2025年新能源汽车新车销售量达到汽车新车销售总量的20%左右，到2035年纯电动汽车成为新销售车辆的主流",
                impact_level="重大"
            ),
            PolicyData(
                policy_name="关于进一步构建高质量充电基础设施体系的指导意见",
                department="国务院办公厅",
                level="国家级",
                publish_date=date(2023, 6, 19),
                category="基础设施",
                industry="充电桩",
                summary="到2030年基本建成覆盖广泛、规模适度、结构合理、功能完善的高质量充电基础设施体系",
                impact_level="重大"
            ),
        ]
        db.add_all(policies)

        db.commit()
        print("Sample data inserted successfully!")

    except Exception as e:
        db.rollback()
        print(f"Error inserting data: {e}")
        raise
    finally:
        db.close()


def main():
    """主函数"""
    print("=" * 50)
    print("Initializing Industry Data Tables")
    print("=" * 50)

    create_tables()
    insert_sample_data()

    print("\n" + "=" * 50)
    print("Initialization complete!")
    print("=" * 50)


if __name__ == "__main__":
    main()
