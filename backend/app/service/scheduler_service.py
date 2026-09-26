"""
定时任务调度服务
- 每天12点自动采集行业资讯和招投标信息
"""
import asyncio
import logging
from datetime import datetime, time
from typing import Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session

from core.database import SessionLocal
from service.news_collection_service import NewsCollectionService

logger = logging.getLogger(__name__)


class SchedulerService:
    """定时任务调度服务"""

    _instance: Optional['SchedulerService'] = None
    _scheduler: Optional[AsyncIOScheduler] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._scheduler is None:
            self._scheduler = AsyncIOScheduler()

    def start(self):
        """启动调度器"""
        if not self._scheduler.running:
            # 添加每日12点执行的任务
            self._scheduler.add_job(
                self._daily_collection_task,
                CronTrigger(hour=12, minute=0),
                id="daily_news_collection",
                name="每日资讯采集",
                replace_existing=True
            )

            self._scheduler.start()
            logger.info("定时任务调度器已启动")
            logger.info("已添加每日12:00资讯采集任务")

    def stop(self):
        """停止调度器"""
        if self._scheduler and self._scheduler.running:
            self._scheduler.shutdown()
            logger.info("定时任务调度器已停止")

    async def _daily_collection_task(self):
        """每日采集任务"""
        logger.info(f"开始执行每日资讯采集任务 - {datetime.now()}")

        db = SessionLocal()
        try:
            service = NewsCollectionService(db)
            result = await service.collect_all(max_news=20, max_bidding=20)

            logger.info(f"每日资讯采集完成: {result}")
        except Exception as e:
            logger.error(f"每日资讯采集失败: {e}")
        finally:
            db.close()

    async def run_collection_now(self, db: Session) -> dict:
        """立即执行采集任务"""
        logger.info(f"手动触发资讯采集任务 - {datetime.now()}")

        try:
            service = NewsCollectionService(db)
            result = await service.collect_all(max_news=20, max_bidding=20)
            logger.info(f"手动采集完成: {result}")
            return result
        except Exception as e:
            logger.error(f"手动采集失败: {e}")
            return {"success": False, "error": str(e)}

    def get_jobs_info(self) -> list:
        """获取所有任务信息"""
        jobs = []
        if self._scheduler:
            for job in self._scheduler.get_jobs():
                jobs.append({
                    "id": job.id,
                    "name": job.name,
                    "next_run_time": str(job.next_run_time) if job.next_run_time else None,
                    "trigger": str(job.trigger)
                })
        return jobs


# 全局调度器实例
_scheduler_service: Optional[SchedulerService] = None


def get_scheduler_service() -> SchedulerService:
    """获取调度器服务单例"""
    global _scheduler_service
    if _scheduler_service is None:
        _scheduler_service = SchedulerService()
    return _scheduler_service


async def init_scheduler_and_check_data():
    """
    初始化调度器并检查数据
    - 启动定时任务
    - 如果数据库没有数据则立即采集
    """
    scheduler = get_scheduler_service()
    scheduler.start()

    # 检查是否需要初始化数据
    db = SessionLocal()
    try:
        service = NewsCollectionService(db)
        if not service.has_data():
            logger.info("数据库中没有资讯数据，开始初始采集...")
            result = await scheduler.run_collection_now(db)
            logger.info(f"初始采集结果: {result}")
        else:
            logger.info("数据库中已有资讯数据，跳过初始采集")
    except Exception as e:
        logger.error(f"初始化检查失败: {e}")
    finally:
        db.close()
