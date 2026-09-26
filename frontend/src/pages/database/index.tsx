import { useEffect, useState, useCallback } from 'react'
import { message, Empty, Spin, Tooltip, Tag, Input } from 'antd'
import { TableOutlined, DatabaseOutlined, SearchOutlined, CloseOutlined } from '@ant-design/icons'
import { useSnapshot } from 'valtio'
import { authState } from '@/store/auth'
import * as api from '@/api'
import type { TableInfo, Text2SQLResponse } from '@/api/database'

// 白底黑字配色
const colors = {
  bg: '#ffffff',
  border: '#e8e8e8',
  textPrimary: '#1a1a1a',
  textSecondary: '#666666',
  textTertiary: '#999999',
  hover: '#f5f5f5',
  active: '#f0f0f0',
}

// 只展示行业相关的表（过滤掉系统表）
const ALLOWED_TABLES = [
  'industry_stats',
  'company_data',
  'policy_data',
]

// 表名中文映射
const TABLE_NAMES: Record<string, string> = {
  'industry_stats': '行业统计数据',
  'company_data': '企业数据',
  'policy_data': '政策数据',
}

// 列名中文映射
const COLUMN_NAMES: Record<string, string> = {
  'id': 'ID',
  'industry_name': '行业名称',
  'metric_name': '指标名称',
  'metric_value': '指标值',
  'unit': '单位',
  'year': '年份',
  'quarter': '季度',
  'month': '月份',
  'region': '地区',
  'source': '数据来源',
  'created_at': '创建时间',
  'company_name': '企业名称',
  'stock_code': '股票代码',
  'industry': '所属行业',
  'sub_industry': '细分行业',
  'revenue': '营收(亿元)',
  'net_profit': '净利润(亿元)',
  'gross_margin': '毛利率(%)',
  'market_cap': '市值(亿元)',
  'employees': '员工数',
  'market_share': '市场份额(%)',
  'policy_name': '政策名称',
  'policy_number': '政策文号',
  'department': '发布部门',
  'level': '政策级别',
  'publish_date': '发布日期',
  'effective_date': '生效日期',
  'category': '政策类别',
  'summary': '政策摘要',
  'impact_level': '影响程度',
}

export default function DatabasePage() {
  const { isLoggedIn } = useSnapshot(authState)

  const [tables, setTables] = useState<TableInfo[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedTable, setSelectedTable] = useState<string | null>(null)
  const [tableData, setTableData] = useState<any[]>([])
  const [tableColumns, setTableColumns] = useState<string[]>([])
  const [dataLoading, setDataLoading] = useState(false)
  const [pagination, setPagination] = useState({ current: 1, pageSize: 20, total: 0 })

  // 自然语言查询状态
  const [searchQuery, setSearchQuery] = useState('')
  const [searchLoading, setSearchLoading] = useState(false)
  const [searchResult, setSearchResult] = useState<Text2SQLResponse | null>(null)

  const fetchTables = useCallback(async () => {
    setLoading(true)
    try {
      const res = await api.database.getTables()
      // 过滤只展示行业相关的表
      const filteredTables = (res.data || []).filter(t => ALLOWED_TABLES.includes(t.name))
      setTables(filteredTables)
      if (filteredTables.length > 0) {
        setSelectedTable(filteredTables[0].name)
        fetchTableData(filteredTables[0].name, 1)
      }
    } catch (error: any) {
      console.error('获取表列表失败:', error)
      message.error('获取表列表失败')
    } finally {
      setLoading(false)
    }
  }, [])

  const fetchTableData = async (tableName: string, page: number) => {
    setDataLoading(true)
    try {
      const res = await api.database.getTableData(tableName, {
        limit: pagination.pageSize,
        offset: (page - 1) * pagination.pageSize,
      })
      if (res.data) {
        setTableData(res.data.rows || [])
        setTableColumns(res.data.columns || [])
        setPagination(prev => ({
          ...prev,
          current: page,
          total: res.data.total || 0,
        }))
      }
    } catch (error: any) {
      console.error('获取表数据失败:', error)
      message.error('获取表数据失败')
    } finally {
      setDataLoading(false)
    }
  }

  useEffect(() => {
    if (isLoggedIn) {
      fetchTables()
    }
  }, [isLoggedIn])

  const handleSelectTable = (tableName: string) => {
    setSelectedTable(tableName)
    fetchTableData(tableName, 1)
  }

  const handlePageChange = (page: number) => {
    if (selectedTable) {
      fetchTableData(selectedTable, page)
    }
  }

  // 获取列的中文名
  const getColumnName = (col: string) => COLUMN_NAMES[col] || col

  // 自然语言搜索
  const handleSearch = async () => {
    if (!searchQuery.trim()) return

    setSearchLoading(true)
    setSearchResult(null)
    try {
      const res = await api.database.text2sql(searchQuery.trim())
      if (res.data) {
        setSearchResult(res.data)
        if (!res.data.success && res.data.error) {
          message.error(res.data.error)
        }
      }
    } catch (error: any) {
      console.error('自然语言查询失败:', error)
      message.error('查询失败，请重试')
    } finally {
      setSearchLoading(false)
    }
  }

  const clearSearch = () => {
    setSearchQuery('')
    setSearchResult(null)
  }

  if (!isLoggedIn) {
    return (
      <div style={{ background: colors.bg, minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <Empty description="请先登录" />
      </div>
    )
  }

  return (
    <div style={{ background: colors.bg, minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* 头部 */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '16px 24px', borderBottom: `1px solid ${colors.border}` }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <DatabaseOutlined style={{ fontSize: 18, color: colors.textSecondary }} />
          <span style={{ fontSize: 16, fontWeight: 600, color: colors.textPrimary }}>数据库</span>
          <Tag style={{ margin: 0, background: '#f0f0f0', border: 'none', color: colors.textSecondary, fontSize: 11 }}>PostgreSQL</Tag>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <Input
            placeholder="用自然语言查询，如：智慧交通市场规模是多少"
            prefix={<SearchOutlined style={{ color: colors.textTertiary }} />}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onPressEnter={handleSearch}
            style={{
              width: 360,
              borderRadius: 6,
              border: `1px solid ${colors.border}`,
            }}
            allowClear
          />
          <button
            onClick={handleSearch}
            disabled={searchLoading || !searchQuery.trim()}
            style={{
              padding: '6px 16px',
              fontSize: 13,
              border: `1px solid ${colors.border}`,
              borderRadius: 6,
              background: searchQuery.trim() ? colors.textPrimary : colors.bg,
              color: searchQuery.trim() ? colors.bg : colors.textTertiary,
              cursor: searchQuery.trim() ? 'pointer' : 'not-allowed',
            }}
          >
            {searchLoading ? '查询中...' : '查询'}
          </button>
        </div>
      </div>

      <div style={{ flex: 1, display: 'flex', minHeight: 0 }}>
        {/* 左侧表列表 */}
        <div style={{ width: 260, borderRight: `1px solid ${colors.border}`, display: 'flex', flexDirection: 'column' }}>
          <div style={{ padding: '12px 16px', borderBottom: `1px solid ${colors.border}`, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: 12, color: colors.textSecondary, fontWeight: 500, textTransform: 'uppercase', letterSpacing: 1 }}>数据表</span>
            <span style={{ fontSize: 12, color: colors.textTertiary }}>{loading ? '-' : tables.length}</span>
          </div>
          <div style={{ flex: 1, overflowY: 'auto', padding: 8 }}>
            {loading ? (
              <div style={{ display: 'flex', justifyContent: 'center', padding: '40px 0' }}>
                <Spin size="small" />
              </div>
            ) : tables.length === 0 ? (
              <div style={{ padding: '40px 16px', textAlign: 'center', fontSize: 13, color: colors.textTertiary }}>暂无数据表</div>
            ) : (
              tables.map((table) => (
                <div
                  key={table.name}
                  onClick={() => handleSelectTable(table.name)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 10,
                    padding: '10px 12px',
                    borderRadius: 6,
                    cursor: 'pointer',
                    marginBottom: 2,
                    background: selectedTable === table.name ? colors.active : 'transparent',
                    transition: 'background 0.15s',
                  }}
                  onMouseEnter={(e) => {
                    if (selectedTable !== table.name) e.currentTarget.style.background = colors.hover
                  }}
                  onMouseLeave={(e) => {
                    if (selectedTable !== table.name) e.currentTarget.style.background = 'transparent'
                  }}
                >
                  <TableOutlined style={{ fontSize: 14, color: selectedTable === table.name ? colors.textPrimary : colors.textTertiary }} />
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontSize: 13, color: selectedTable === table.name ? colors.textPrimary : colors.textSecondary, fontWeight: 500, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      {TABLE_NAMES[table.name] || table.name}
                    </div>
                    <div style={{ fontSize: 11, color: colors.textTertiary }}>
                      {table.name} · {table.row_count?.toLocaleString() || 0} 行
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* 右侧内容 */}
        <div style={{ flex: 1, overflowY: 'auto', padding: 24 }}>
          {/* 自然语言查询结果 */}
          {(searchLoading || searchResult) && (
            <div style={{ marginBottom: 24, border: `1px solid ${colors.border}`, borderRadius: 8, overflow: 'hidden' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px 16px', background: '#fafafa', borderBottom: `1px solid ${colors.border}` }}>
                <span style={{ fontSize: 12, color: colors.textSecondary, fontWeight: 500, textTransform: 'uppercase', letterSpacing: 0.5 }}>查询结果</span>
                {searchResult && (
                  <CloseOutlined
                    style={{ fontSize: 14, color: colors.textTertiary, cursor: 'pointer' }}
                    onClick={clearSearch}
                  />
                )}
              </div>

              {searchLoading ? (
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '40px 0', gap: 12 }}>
                  <Spin size="small" />
                  <span style={{ color: colors.textSecondary, fontSize: 13 }}>正在分析查询...</span>
                </div>
              ) : searchResult ? (
                <div>
                  {/* SQL */}
                  {searchResult.sql && (
                    <div style={{ padding: '12px 16px', borderBottom: `1px solid ${colors.border}`, background: '#f8f9fa' }}>
                      <div style={{ fontSize: 11, color: colors.textTertiary, marginBottom: 6 }}>生成的 SQL</div>
                      <code style={{ fontSize: 12, color: '#6366f1', fontFamily: 'monospace', whiteSpace: 'pre-wrap', wordBreak: 'break-all' }}>
                        {searchResult.sql}
                      </code>
                    </div>
                  )}

                  {/* 解释 */}
                  {searchResult.explanation && (
                    <div style={{ padding: '12px 16px', borderBottom: `1px solid ${colors.border}` }}>
                      <div style={{ fontSize: 13, color: colors.textSecondary }}>{searchResult.explanation}</div>
                    </div>
                  )}

                  {/* 结果数据 */}
                  {searchResult.success && searchResult.data && searchResult.data.length > 0 ? (
                    <div style={{ overflowX: 'auto' }}>
                      <div style={{ display: 'flex', minWidth: (searchResult.columns?.length || 1) * 150, background: '#fafafa', borderBottom: `1px solid ${colors.border}` }}>
                        {searchResult.columns?.map((col) => (
                          <div key={col} style={{ flex: '0 0 150px', padding: '10px 16px', fontSize: 12, color: colors.textSecondary, fontWeight: 500 }}>
                            {getColumnName(col)}
                          </div>
                        ))}
                      </div>
                      {searchResult.data.map((row, rowIdx) => (
                        <div key={rowIdx} style={{ display: 'flex', minWidth: (searchResult.columns?.length || 1) * 150, borderBottom: rowIdx < searchResult.data.length - 1 ? `1px solid ${colors.border}` : 'none' }}>
                          {searchResult.columns?.map((col) => (
                            <div key={col} style={{ flex: '0 0 150px', padding: '10px 16px', fontSize: 13, color: colors.textPrimary, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                              <Tooltip title={String((row as any)[col] ?? '-')}>
                                <span>{(row as any)[col] !== null && (row as any)[col] !== undefined ? String((row as any)[col]) : '-'}</span>
                              </Tooltip>
                            </div>
                          ))}
                        </div>
                      ))}
                      <div style={{ padding: '10px 16px', fontSize: 12, color: colors.textTertiary, background: '#fafafa' }}>
                        共 {searchResult.row_count} 条结果
                      </div>
                    </div>
                  ) : searchResult.error ? (
                    <div style={{ padding: '20px 16px', color: '#ef4444', fontSize: 13 }}>{searchResult.error}</div>
                  ) : (
                    <div style={{ padding: '20px 16px', color: colors.textTertiary, fontSize: 13 }}>暂无数据</div>
                  )}
                </div>
              ) : null}
            </div>
          )}

          {selectedTable && (
            <div>
              {/* 表头 */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20, paddingBottom: 16, borderBottom: `1px solid ${colors.border}` }}>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    <TableOutlined style={{ fontSize: 16, color: colors.textSecondary }} />
                    <span style={{ fontSize: 16, fontWeight: 600, color: colors.textPrimary }}>
                      {TABLE_NAMES[selectedTable] || selectedTable}
                    </span>
                  </div>
                  <div style={{ fontSize: 12, color: colors.textTertiary, marginTop: 4, marginLeft: 26 }}>
                    {selectedTable}
                  </div>
                </div>
                <span style={{ fontSize: 12, color: colors.textTertiary }}>
                  共 {pagination.total.toLocaleString()} 条数据
                </span>
              </div>

              {/* 数据表格 */}
              {dataLoading ? (
                <div style={{ display: 'flex', justifyContent: 'center', padding: '60px 0' }}>
                  <Spin />
                </div>
              ) : tableData.length > 0 ? (
                <>
                  <div style={{ border: `1px solid ${colors.border}`, borderRadius: 8, overflow: 'hidden' }}>
                    {/* 表头 */}
                    <div style={{ overflowX: 'auto' }}>
                      <div style={{ display: 'flex', minWidth: tableColumns.length * 150, background: '#fafafa', borderBottom: `1px solid ${colors.border}` }}>
                        {tableColumns.map((col) => (
                          <div key={col} style={{ flex: '0 0 150px', padding: '12px 16px', fontSize: 12, color: colors.textSecondary, fontWeight: 500 }}>
                            <div>{getColumnName(col)}</div>
                            <div style={{ fontSize: 11, color: colors.textTertiary, fontFamily: 'monospace' }}>{col}</div>
                          </div>
                        ))}
                      </div>
                      {/* 数据行 */}
                      {tableData.map((row, rowIdx) => (
                        <div key={rowIdx} style={{ display: 'flex', minWidth: tableColumns.length * 150, borderBottom: rowIdx < tableData.length - 1 ? `1px solid ${colors.border}` : 'none' }}>
                          {tableColumns.map((col) => (
                            <div key={col} style={{ flex: '0 0 150px', padding: '10px 16px', fontSize: 13, color: colors.textPrimary, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                              <Tooltip title={String(row[col] ?? '-')}>
                                <span>{row[col] !== null && row[col] !== undefined ? String(row[col]) : '-'}</span>
                              </Tooltip>
                            </div>
                          ))}
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* 分页 */}
                  {pagination.total > pagination.pageSize && (
                    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', marginTop: 20, gap: 8 }}>
                      <button
                        onClick={() => handlePageChange(pagination.current - 1)}
                        disabled={pagination.current <= 1}
                        style={{
                          padding: '6px 12px',
                          fontSize: 13,
                          border: `1px solid ${colors.border}`,
                          borderRadius: 4,
                          background: colors.bg,
                          color: pagination.current <= 1 ? colors.textTertiary : colors.textSecondary,
                          cursor: pagination.current <= 1 ? 'not-allowed' : 'pointer',
                        }}
                      >
                        上一页
                      </button>
                      <span style={{ fontSize: 13, color: colors.textSecondary, padding: '0 12px' }}>
                        {pagination.current} / {Math.ceil(pagination.total / pagination.pageSize)}
                      </span>
                      <button
                        onClick={() => handlePageChange(pagination.current + 1)}
                        disabled={pagination.current >= Math.ceil(pagination.total / pagination.pageSize)}
                        style={{
                          padding: '6px 12px',
                          fontSize: 13,
                          border: `1px solid ${colors.border}`,
                          borderRadius: 4,
                          background: colors.bg,
                          color: pagination.current >= Math.ceil(pagination.total / pagination.pageSize) ? colors.textTertiary : colors.textSecondary,
                          cursor: pagination.current >= Math.ceil(pagination.total / pagination.pageSize) ? 'not-allowed' : 'pointer',
                        }}
                      >
                        下一页
                      </button>
                    </div>
                  )}
                </>
              ) : (
                <div style={{ display: 'flex', justifyContent: 'center', padding: '60px 0' }}>
                  <Empty description="暂无数据" />
                </div>
              )}
            </div>
          )}

          {!selectedTable && !loading && (
            <div style={{ display: 'flex', justifyContent: 'center', padding: '60px 0' }}>
              <Empty description="选择一个数据表" />
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
