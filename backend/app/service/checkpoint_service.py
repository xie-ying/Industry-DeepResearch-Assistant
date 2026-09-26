"""检查点服务 - 用于保存和恢复深度研究状态"""
import json
import logging
from typing import Dict, Any, Optional, List
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session

from models.research import ResearchCheckpoint
from core.database import SessionLocal

logger = logging.getLogger(__name__)


class CheckpointService:
    """检查点服务"""

    def __init__(self):
        pass

    def _get_db(self) -> Session:
        """获取数据库会话"""
        return SessionLocal()

    def save_checkpoint(
        self,
        session_id: str,
        state: Dict[str, Any],
        user_id: Optional[str] = None,
        ui_state: Optional[Dict[str, Any]] = None,
        final_report: Optional[str] = None,
    ) -> Optional[str]:
        """
        保存检查点

        Args:
            session_id: 研究会话 ID
            state: ResearchState 字典（后端状态）
            user_id: 用户 ID（可选）
            ui_state: 前端 UI 状态（研究步骤、搜索结果、图表等）
            final_report: 最终报告内容

        Returns:
            检查点 ID，失败返回 None
        """
        db = self._get_db()
        try:
            # 提取关键信息
            query = state.get("query", "")
            phase = state.get("phase", "planning")
            iteration = state.get("iteration", 0)

            # 清理 state 中不可序列化的内容
            clean_state = self._clean_state_for_storage(state)
            clean_ui_state = self._clean_state_for_storage(ui_state) if ui_state else None

            # 查找现有检查点
            existing = db.query(ResearchCheckpoint).filter(
                ResearchCheckpoint.session_id == session_id
            ).first()

            if existing:
                # 更新现有检查点
                existing.phase = phase
                existing.iteration = iteration
                existing.state_json = clean_state
                if clean_ui_state:
                    existing.ui_state_json = clean_ui_state
                if final_report:
                    existing.final_report = final_report
                existing.status = "running"
                existing.updated_at = datetime.utcnow()
                checkpoint_id = str(existing.id)
            else:
                # 创建新检查点
                checkpoint = ResearchCheckpoint(
                    session_id=session_id,
                    user_id=UUID(user_id) if user_id else None,
                    query=query,
                    phase=phase,
                    iteration=iteration,
                    state_json=clean_state,
                    ui_state_json=clean_ui_state,
                    final_report=final_report,
                    status="running",
                )
                db.add(checkpoint)
                db.flush()
                checkpoint_id = str(checkpoint.id)

            db.commit()
            # 详细日志
            ui_steps = clean_ui_state.get("research_steps", []) if clean_ui_state else []
            ui_search = clean_ui_state.get("search_results", []) if clean_ui_state else []
            ui_charts = clean_ui_state.get("charts", []) if clean_ui_state else []
            ui_kg = clean_ui_state.get("knowledge_graph", {}) if clean_ui_state else {}
            logger.info(f"[CheckpointService] 保存成功: session={session_id}, phase={phase}, "
                       f"ui_state=[steps={len(ui_steps)}, search_results={len(ui_search)}, "
                       f"charts={len(ui_charts)}, kg_nodes={len(ui_kg.get('nodes', []) if ui_kg else [])}]")
            return checkpoint_id

        except Exception as e:
            logger.error(f"Failed to save checkpoint: {e}")
            db.rollback()
            return None
        finally:
            db.close()

    def load_checkpoint(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        加载最新的检查点（仅后端状态）

        Args:
            session_id: 研究会话 ID

        Returns:
            ResearchState 字典，未找到返回 None
        """
        db = self._get_db()
        try:
            checkpoint = db.query(ResearchCheckpoint).filter(
                ResearchCheckpoint.session_id == session_id
            ).order_by(ResearchCheckpoint.updated_at.desc()).first()

            if not checkpoint:
                return None

            return checkpoint.state_json

        except Exception as e:
            logger.error(f"Failed to load checkpoint: {e}")
            return None
        finally:
            db.close()

    def load_full_checkpoint(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        加载完整的检查点（包含后端状态、UI状态和报告）

        Args:
            session_id: 研究会话 ID

        Returns:
            完整检查点数据，包含 state_json, ui_state_json, final_report 等
        """
        db = self._get_db()
        try:
            checkpoint = db.query(ResearchCheckpoint).filter(
                ResearchCheckpoint.session_id == session_id
            ).order_by(ResearchCheckpoint.updated_at.desc()).first()

            if not checkpoint:
                logger.info(f"[CheckpointService] 未找到检查点: session={session_id}")
                return None

            result = checkpoint.to_dict(include_state=True)
            # 详细日志
            ui_state = result.get("ui_state_json", {})
            if ui_state:
                logger.info(f"[CheckpointService] 加载成功: session={session_id}, phase={result.get('phase')}, "
                           f"ui_state=[steps={len(ui_state.get('research_steps', []))}, "
                           f"search_results={len(ui_state.get('search_results', []))}, "
                           f"charts={len(ui_state.get('charts', []))}, "
                           f"kg_nodes={len((ui_state.get('knowledge_graph') or {}).get('nodes', []))}]")
            else:
                logger.info(f"[CheckpointService] 加载成功但无ui_state: session={session_id}, phase={result.get('phase')}")
            return result

        except Exception as e:
            logger.error(f"Failed to load full checkpoint: {e}")
            return None
        finally:
            db.close()

    def get_checkpoint_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        获取检查点信息（不包含完整状态）

        Args:
            session_id: 研究会话 ID

        Returns:
            检查点元信息
        """
        db = self._get_db()
        try:
            checkpoint = db.query(ResearchCheckpoint).filter(
                ResearchCheckpoint.session_id == session_id
            ).order_by(ResearchCheckpoint.updated_at.desc()).first()

            if not checkpoint:
                return None

            return checkpoint.to_dict()

        except Exception as e:
            logger.error(f"Failed to get checkpoint info: {e}")
            return None
        finally:
            db.close()

    def list_checkpoints(
        self,
        user_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        列出检查点

        Args:
            user_id: 用户 ID（可选，用于过滤）
            status: 状态过滤
            limit: 限制数量

        Returns:
            检查点列表
        """
        db = self._get_db()
        try:
            query = db.query(ResearchCheckpoint)

            if user_id:
                query = query.filter(ResearchCheckpoint.user_id == UUID(user_id))
            if status:
                query = query.filter(ResearchCheckpoint.status == status)

            checkpoints = query.order_by(
                ResearchCheckpoint.updated_at.desc()
            ).limit(limit).all()

            return [cp.to_dict() for cp in checkpoints]

        except Exception as e:
            logger.error(f"Failed to list checkpoints: {e}")
            return []
        finally:
            db.close()

    def update_status(
        self,
        session_id: str,
        status: str,
        error_message: Optional[str] = None,
    ) -> bool:
        """
        更新检查点状态

        Args:
            session_id: 研究会话 ID
            status: 新状态 (running/paused/completed/failed)
            error_message: 错误信息（可选）

        Returns:
            是否成功
        """
        db = self._get_db()
        try:
            checkpoint = db.query(ResearchCheckpoint).filter(
                ResearchCheckpoint.session_id == session_id
            ).first()

            if not checkpoint:
                return False

            checkpoint.status = status
            if error_message:
                checkpoint.error_message = error_message
            checkpoint.updated_at = datetime.utcnow()

            db.commit()
            return True

        except Exception as e:
            logger.error(f"Failed to update checkpoint status: {e}")
            db.rollback()
            return False
        finally:
            db.close()

    def delete_checkpoint(self, session_id: str) -> bool:
        """
        删除检查点

        Args:
            session_id: 研究会话 ID

        Returns:
            是否成功
        """
        db = self._get_db()
        try:
            deleted = db.query(ResearchCheckpoint).filter(
                ResearchCheckpoint.session_id == session_id
            ).delete()

            db.commit()
            return deleted > 0

        except Exception as e:
            logger.error(f"Failed to delete checkpoint: {e}")
            db.rollback()
            return False
        finally:
            db.close()

    def _clean_state_for_storage(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        清理状态以便存储

        移除不可序列化的内容，保留可恢复的数据
        """
        clean = {}
        for key, value in state.items():
            try:
                # 尝试序列化测试
                json.dumps(value, default=str)
                clean[key] = value
            except (TypeError, ValueError):
                # 跳过不可序列化的值，或转换为字符串
                if isinstance(value, (list, tuple)):
                    clean[key] = [str(v) for v in value]
                elif isinstance(value, dict):
                    clean[key] = self._clean_state_for_storage(value)
                else:
                    clean[key] = str(value)
        return clean


# 单例
_checkpoint_service = None


def get_checkpoint_service() -> CheckpointService:
    """获取检查点服务实例"""
    global _checkpoint_service
    if _checkpoint_service is None:
        _checkpoint_service = CheckpointService()
    return _checkpoint_service
