"""招投标信息服务 - 81API 招投标数据"""
import os
import httpx
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime
from urllib.parse import quote


@dataclass
class BidInfo:
    """招投标信息"""
    id: str  # 项目ID (bid)
    title: str  # 项目标题
    notice_type: str  # 公告类型 (中标/招标/采购等)
    province: str  # 省份
    city: str  # 城市
    publish_time: str  # 发布时间
    source: str  # 来源

    @classmethod
    def from_dict(cls, data: Dict) -> "BidInfo":
        return cls(
            id=data.get("bid", ""),
            title=data.get("title", ""),
            notice_type=data.get("noticeType", ""),
            province=data.get("province", ""),
            city=data.get("city", "") or "",
            publish_time=data.get("publishTime", ""),
            source="81api",
        )

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "title": self.title,
            "notice_type": self.notice_type,
            "province": self.province,
            "city": self.city,
            "publish_time": self.publish_time,
            "source": self.source,
        }

    def format_display(self) -> str:
        """格式化显示"""
        location = f"{self.province}"
        if self.city:
            location += f" {self.city}"
        return f"""
📋 {self.title}
━━━━━━━━━━━━━━━━━━━━━━━━
类型: {self.notice_type}
地区: {location}
发布时间: {self.publish_time}
ID: {self.id}
"""


class BiddingService:
    """招投标信息服务 - 81API"""

    # 81API 招投标接口
    BASE_URL = "https://bid.81api.com"

    # API 端点
    ENDPOINTS = {
        "win_bid": "/queryWinBid",      # 中标查询
        "bid": "/queryBid",              # 招标查询
        "detail": "/queryBidDetail",     # 标书详情
    }

    def __init__(self):
        self.app_code = os.getenv("BID_APP_CODE", "")

        if not self.app_code:
            print("警告: BID_APP_CODE 环境变量未设置")

    async def search_win_bids(
        self,
        keyword: str,
        page: int = 1
    ) -> Dict[str, Any]:
        """
        搜索中标信息

        Args:
            keyword: 搜索关键词
            page: 页码 (从1开始)

        Returns:
            搜索结果
        """
        return await self._search(
            endpoint=self.ENDPOINTS["win_bid"],
            keyword=keyword,
            page=page
        )

    async def search_bids(
        self,
        keyword: str,
        category: Optional[str] = None,
        region: Optional[str] = None,
        page: int = 1,
        page_size: int = 10
    ) -> Dict[str, Any]:
        """
        搜索招投标信息 (统一接口)

        Args:
            keyword: 搜索关键词
            category: 项目类别 (招标/中标) - 决定使用哪个端点
            region: 地区 (暂不支持，API按省市返回)
            page: 页码
            page_size: 每页数量 (API固定返回10条)

        Returns:
            搜索结果
        """
        # 根据类别选择端点
        if category and "招标" in category:
            endpoint = self.ENDPOINTS["bid"]
        else:
            # 默认查询中标信息
            endpoint = self.ENDPOINTS["win_bid"]

        return await self._search(endpoint, keyword, page)

    async def search_bid_notices(
        self,
        keyword: str,
        page: int = 1
    ) -> Dict[str, Any]:
        """
        搜索招标公告

        Args:
            keyword: 搜索关键词
            page: 页码

        Returns:
            搜索结果
        """
        return await self._search(
            endpoint=self.ENDPOINTS["bid"],
            keyword=keyword,
            page=page
        )

    async def get_bid_detail(self, bid_id: str) -> Dict[str, Any]:
        """
        获取标书详情

        Args:
            bid_id: 标书ID

        Returns:
            标书详情
        """
        if not self.app_code:
            return {
                "success": False,
                "error": "招投标API未配置，请设置 BID_APP_CODE 环境变量",
                "data": None
            }

        try:
            url = f"{self.BASE_URL}{self.ENDPOINTS['detail']}/{bid_id}"
            headers = {
                "Authorization": f"APPCODE {self.app_code}"
            }

            async with httpx.AsyncClient(timeout=15.0, verify=False) as client:
                response = await client.get(url, headers=headers)

                if response.status_code == 200:
                    data = response.json()
                    if data.get("status") == "200":
                        return {
                            "success": True,
                            "data": data.get("data", {}),
                            "message": data.get("message", "")
                        }
                    else:
                        return {
                            "success": False,
                            "error": data.get("message", "查询失败"),
                            "data": None
                        }

            return {
                "success": False,
                "error": "API请求失败",
                "data": None
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "data": None
            }

    async def _search(
        self,
        endpoint: str,
        keyword: str,
        page: int = 1
    ) -> Dict[str, Any]:
        """
        内部搜索方法

        Args:
            endpoint: API端点
            keyword: 搜索关键词
            page: 页码

        Returns:
            搜索结果
        """
        if not self.app_code:
            return {
                "success": False,
                "error": "招投标API未配置，请设置 BID_APP_CODE 环境变量",
                "results": [],
                "total": 0
            }

        if not keyword:
            return {
                "success": False,
                "error": "请提供搜索关键词",
                "results": [],
                "total": 0
            }

        try:
            # 构建URL: /endpoint/keyword/page
            url = f"{self.BASE_URL}{endpoint}/{keyword}/{page}"
            headers = {
                "Authorization": f"APPCODE {self.app_code}"
            }

            # 注意：该API的SSL证书与域名不匹配，需要跳过验证
            async with httpx.AsyncClient(timeout=15.0, verify=False) as client:
                response = await client.get(url, headers=headers)

                if response.status_code == 200:
                    data = response.json()

                    if data.get("status") == "200":
                        result_data = data.get("data", {})
                        items = result_data.get("list", [])
                        total = result_data.get("total", 0)

                        results = [BidInfo.from_dict(item).to_dict() for item in items]

                        return {
                            "success": True,
                            "results": results,
                            "total": total,
                            "page": page,
                            "count": len(results),
                            "message": data.get("message", "")
                        }
                    else:
                        return {
                            "success": False,
                            "error": data.get("message", "查询失败"),
                            "results": [],
                            "total": 0
                        }

                # 处理 403 配额用尽错误
                if response.status_code == 403:
                    error_msg = response.headers.get("x-ca-error-message", "")
                    if "quota exhausted" in error_msg.lower():
                        return {
                            "success": False,
                            "error": "API 调用配额已用尽，请续费或等待配额重置",
                            "results": [],
                            "total": 0,
                            "quota_exhausted": True
                        }

                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}",
                    "results": [],
                    "total": 0
                }

        except httpx.TimeoutException:
            return {
                "success": False,
                "error": "请求超时",
                "results": [],
                "total": 0
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "results": [],
                "total": 0
            }

    def format_results(self, results: List[Dict]) -> str:
        """格式化搜索结果为可读文本"""
        if not results:
            return "未找到相关招投标信息"

        output = []
        for i, item in enumerate(results, 1):
            location = item.get("province", "")
            if item.get("city"):
                location += f" {item['city']}"

            output.append(f"""
{i}. {item.get('title', '无标题')}
   类型: {item.get('notice_type', '-')} | 地区: {location}
   发布时间: {item.get('publish_time', '-')}
""")

        return "\n".join(output)


# 单例
_bidding_service: Optional[BiddingService] = None


def get_bidding_service() -> BiddingService:
    """获取招投标服务单例"""
    global _bidding_service
    if _bidding_service is None:
        _bidding_service = BiddingService()
    return _bidding_service
