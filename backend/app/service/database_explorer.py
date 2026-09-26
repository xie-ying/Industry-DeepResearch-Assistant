"""数据库探索服务 - 仅支持 PostgreSQL"""
from typing import List, Dict, Any, Optional
from sqlalchemy import text
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)


class DatabaseExplorer:
    """数据库探索器 - 提供只读查询功能"""

    def __init__(self, db: Session):
        self.db = db

    def get_tables(self) -> List[Dict[str, Any]]:
        """获取当前数据库的所有表"""
        query = text("""
            SELECT
                table_name,
                pg_size_pretty(pg_total_relation_size(quote_ident(table_name))) as size,
                (SELECT count(*) FROM information_schema.columns
                 WHERE table_name = t.table_name AND table_schema = 'public') as column_count
            FROM information_schema.tables t
            WHERE table_schema = 'public'
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """)
        result = self.db.execute(query)
        tables = []
        for row in result:
            # 获取行数（单独查询以避免复杂嵌套）
            count_query = text(f'SELECT count(*) FROM "{row.table_name}"')
            try:
                count_result = self.db.execute(count_query)
                row_count = count_result.scalar()
            except Exception:
                self.db.rollback()
                row_count = 0

            tables.append({
                "name": row.table_name,
                "size": row.size,
                "column_count": row.column_count,
                "row_count": row_count,
            })
        return tables

    def get_table_schema(self, table_name: str) -> Dict[str, Any]:
        """获取表结构"""
        # 验证表名安全性
        if not self._is_valid_identifier(table_name):
            raise ValueError("Invalid table name")

        # 获取列信息
        columns_query = text("""
            SELECT
                column_name,
                data_type,
                character_maximum_length,
                is_nullable,
                column_default
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = :table_name
            ORDER BY ordinal_position
        """)
        columns_result = self.db.execute(columns_query, {"table_name": table_name})
        columns = []
        for row in columns_result:
            columns.append({
                "name": row.column_name,
                "type": row.data_type,
                "max_length": row.character_maximum_length,
                "nullable": row.is_nullable == "YES",
                "default": row.column_default,
            })

        # 获取主键信息
        pk_query = text("""
            SELECT a.attname
            FROM pg_index i
            JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
            WHERE i.indrelid = :table_name::regclass AND i.indisprimary
        """)
        try:
            pk_result = self.db.execute(pk_query, {"table_name": table_name})
            primary_keys = [row.attname for row in pk_result]
        except Exception:
            self.db.rollback()
            primary_keys = []

        # 获取索引信息
        idx_query = text("""
            SELECT indexname, indexdef
            FROM pg_indexes
            WHERE tablename = :table_name AND schemaname = 'public'
        """)
        try:
            idx_result = self.db.execute(idx_query, {"table_name": table_name})
            indexes = []
            for row in idx_result:
                indexes.append({
                    "name": row.indexname,
                    "definition": row.indexdef,
                })
        except Exception:
            self.db.rollback()
            indexes = []

        return {
            "table_name": table_name,
            "columns": columns,
            "primary_keys": primary_keys,
            "indexes": indexes,
        }

    def get_table_data(
        self,
        table_name: str,
        limit: int = 100,
        offset: int = 0,
        order_by: Optional[str] = None,
        order_dir: str = "asc"
    ) -> Dict[str, Any]:
        """获取表数据（分页）"""
        # 验证表名安全性
        if not self._is_valid_identifier(table_name):
            raise ValueError("Invalid table name")

        # 验证排序方向
        order_dir = order_dir.lower()
        if order_dir not in ("asc", "desc"):
            order_dir = "asc"

        # 获取总行数
        count_query = text(f'SELECT count(*) FROM "{table_name}"')
        total = self.db.execute(count_query).scalar()

        # 构建查询（使用安全的参数化）
        if order_by and self._is_valid_identifier(order_by):
            data_query = text(f'SELECT * FROM "{table_name}" ORDER BY "{order_by}" {order_dir} LIMIT :limit OFFSET :offset')
        else:
            data_query = text(f'SELECT * FROM "{table_name}" LIMIT :limit OFFSET :offset')

        result = self.db.execute(data_query, {"limit": limit, "offset": offset})

        # 获取列名
        columns = list(result.keys())

        # 获取数据
        rows = []
        for row in result:
            row_dict = {}
            for i, col in enumerate(columns):
                value = row[i]
                # 处理特殊类型
                if hasattr(value, 'isoformat'):
                    value = value.isoformat()
                elif isinstance(value, bytes):
                    value = f"<binary {len(value)} bytes>"
                row_dict[col] = value
            rows.append(row_dict)

        return {
            "table_name": table_name,
            "columns": columns,
            "rows": rows,
            "total": total,
            "limit": limit,
            "offset": offset,
        }

    def execute_query(self, sql: str, limit: int = 100) -> Dict[str, Any]:
        """执行只读 SQL 查询"""
        # 安全检查：只允许 SELECT 语句
        sql_clean = sql.strip().upper()
        if not sql_clean.startswith("SELECT"):
            raise ValueError("Only SELECT queries are allowed")

        # 禁止危险关键字
        dangerous_keywords = ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE", "TRUNCATE", "GRANT", "REVOKE"]
        for keyword in dangerous_keywords:
            if keyword in sql_clean:
                raise ValueError(f"Query contains forbidden keyword: {keyword}")

        # 添加 LIMIT 如果没有
        if "LIMIT" not in sql_clean:
            sql = f"{sql.rstrip(';')} LIMIT {limit}"

        try:
            result = self.db.execute(text(sql))
            columns = list(result.keys())

            rows = []
            for row in result:
                row_dict = {}
                for i, col in enumerate(columns):
                    value = row[i]
                    if hasattr(value, 'isoformat'):
                        value = value.isoformat()
                    elif isinstance(value, bytes):
                        value = f"<binary {len(value)} bytes>"
                    row_dict[col] = value
                rows.append(row_dict)

            return {
                "columns": columns,
                "rows": rows,
                "row_count": len(rows),
            }
        except Exception as e:
            self.db.rollback()
            logger.error(f"Query execution error: {e}")
            raise ValueError(f"Query execution failed: {str(e)}")

    def _is_valid_identifier(self, name: str) -> bool:
        """验证标识符是否安全"""
        if not name:
            return False
        # 只允许字母、数字、下划线
        import re
        return bool(re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', name))
