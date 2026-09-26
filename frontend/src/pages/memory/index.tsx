import { useEffect, useState, useCallback } from 'react'
import {
  Card,
  Button,
  List,
  Input,
  message,
  Popconfirm,
  Tag,
  Empty,
  Spin,
  Typography,
  Timeline,
  Collapse,
} from 'antd'
import {
  DeleteOutlined,
  SearchOutlined,
  BulbOutlined,
  ClockCircleOutlined,
  FileTextOutlined,
  ReloadOutlined,
} from '@ant-design/icons'
import { useSnapshot } from 'valtio'
import { authState } from '@/store/auth'
import { useNavigate } from 'react-router-dom'
import * as api from '@/api'
import type { Memory, MemorySearchResult } from '@/api/memory'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import 'dayjs/locale/zh-cn'
import styles from './index.module.scss'

dayjs.extend(relativeTime)
dayjs.locale('zh-cn')

const { Text, Paragraph } = Typography
const { Search } = Input

export default function MemoryPage() {
  const navigate = useNavigate()
  const { isLoggedIn } = useSnapshot(authState)
  const [memories, setMemories] = useState<Memory[]>([])
  const [loading, setLoading] = useState(false)
  const [searchResults, setSearchResults] = useState<MemorySearchResult[] | null>(null)
  const [searchLoading, setSearchLoading] = useState(false)
  const [total, setTotal] = useState(0)

  const fetchMemories = useCallback(async () => {
    setLoading(true)
    try {
      const res = await api.memory.getMemories({ limit: 50 })
      if (res.data) {
        setMemories(res.data.memories)
        setTotal(res.data.total)
      }
    } catch (error: any) {
      message.error(error?.response?.data?.detail || '获取记忆列表失败')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    if (isLoggedIn) {
      fetchMemories()
    }
  }, [isLoggedIn, fetchMemories])

  if (!isLoggedIn) {
    return (
      <div className={styles['memory-page']}>
        <div className={styles['empty-state']}>
          <Empty description="请先登录" />
          <Button type="primary" onClick={() => navigate('/login')}>
            去登录
          </Button>
        </div>
      </div>
    )
  }

  const handleSearch = async (query: string) => {
    if (!query.trim()) {
      setSearchResults(null)
      return
    }
    setSearchLoading(true)
    try {
      const res = await api.memory.searchMemories({ query, top_k: 10 })
      if (res.data) {
        setSearchResults(res.data)
      }
    } catch (error: any) {
      message.error(error?.response?.data?.detail || '搜索失败')
    } finally {
      setSearchLoading(false)
    }
  }

  const handleDelete = async (memoryId: string) => {
    try {
      await api.memory.deleteMemory(memoryId)
      message.success('记忆已删除')
      fetchMemories()
      // 如果正在显示搜索结果，也需要更新
      if (searchResults) {
        setSearchResults(searchResults.filter(r => r.id !== memoryId))
      }
    } catch (error: any) {
      message.error(error?.response?.data?.detail || '删除失败')
    }
  }

  const handleClearSearch = () => {
    setSearchResults(null)
  }

  const renderKeyInsights = (insights: Record<string, unknown> | undefined) => {
    if (!insights || typeof insights !== 'object') return null

    const items = Object.entries(insights).map(([key, value]) => ({
      key,
      label: formatKeyLabel(key),
      children: <Text>{String(value)}</Text>,
    }))

    if (items.length === 0) return null

    return (
      <Collapse
        ghost
        size="small"
        items={items}
        className={styles['insights-collapse']}
      />
    )
  }

  const formatKeyLabel = (key: string): string => {
    const labels: Record<string, string> = {
      main_topics: '主要话题',
      key_entities: '关键实体',
      sentiment: '情感倾向',
      action_items: '待办事项',
      decisions: '做出的决定',
      questions: '问题',
      summary: '总结',
    }
    return labels[key] || key.replace(/_/g, ' ')
  }

  const renderMemoryList = () => (
    <List
      className={styles['memory-list']}
      loading={loading}
      dataSource={memories}
      locale={{ emptyText: <Empty description="暂无记忆" /> }}
      renderItem={(memory) => (
        <List.Item
          className={styles['memory-item']}
          actions={[
            <Popconfirm
              key="delete"
              title="确定删除此记忆？"
              description="删除后将无法恢复"
              onConfirm={() => handleDelete(memory.id)}
            >
              <Button type="text" danger size="small" icon={<DeleteOutlined />} />
            </Popconfirm>,
          ]}
        >
          <List.Item.Meta
            avatar={
              <div className={styles['memory-icon']}>
                <BulbOutlined />
              </div>
            }
            title={
              <div className={styles['memory-title']}>
                <Text ellipsis={{ tooltip: true }} style={{ flex: 1 }}>
                  {memory.summary}
                </Text>
                {memory.token_count && (
                  <Tag color="blue">{memory.token_count} tokens</Tag>
                )}
              </div>
            }
            description={
              <div className={styles['memory-meta']}>
                {renderKeyInsights(memory.key_insights)}
                <div className={styles['memory-footer']}>
                  <span>
                    <ClockCircleOutlined style={{ marginRight: 4 }} />
                    {dayjs(memory.created_at).format('YYYY-MM-DD HH:mm')}
                  </span>
                  <span>{dayjs(memory.created_at).fromNow()}</span>
                </div>
              </div>
            }
          />
        </List.Item>
      )}
    />
  )

  const renderSearchResults = () => (
    <div className={styles['search-results']}>
      <div className={styles['search-header']}>
        <Text type="secondary">找到 {searchResults?.length || 0} 条相关记忆</Text>
        <Button type="link" onClick={handleClearSearch}>
          清除搜索
        </Button>
      </div>
      <List
        className={styles['memory-list']}
        loading={searchLoading}
        dataSource={searchResults || []}
        locale={{ emptyText: <Empty description="未找到相关记忆" /> }}
        renderItem={(result) => (
          <List.Item
            className={styles['memory-item']}
            actions={[
              <Popconfirm
                key="delete"
                title="确定删除此记忆？"
                onConfirm={() => handleDelete(result.id)}
              >
                <Button type="text" danger size="small" icon={<DeleteOutlined />} />
              </Popconfirm>,
            ]}
          >
            <List.Item.Meta
              avatar={
                <div className={styles['memory-icon']}>
                  <FileTextOutlined />
                </div>
              }
              title={
                <div className={styles['memory-title']}>
                  <Text ellipsis={{ tooltip: true }} style={{ flex: 1 }}>
                    {result.content}
                  </Text>
                  <Tag color="purple">相关度 {(result.score * 100).toFixed(0)}%</Tag>
                  <Tag>{result.memory_type}</Tag>
                </div>
              }
            />
          </List.Item>
        )}
      />
    </div>
  )

  return (
    <div className={styles['memory-page']}>
      <div className={styles['header']}>
        <div className={styles['header-left']}>
          <h2>记忆库</h2>
          <Text type="secondary">共 {total} 条记忆</Text>
        </div>
        <div className={styles['header-right']}>
          <Button icon={<ReloadOutlined />} onClick={fetchMemories} loading={loading}>
            刷新
          </Button>
        </div>
      </div>

      <div className={styles['search-bar']}>
        <Search
          placeholder="搜索相关记忆..."
          allowClear
          enterButton={<SearchOutlined />}
          size="large"
          onSearch={handleSearch}
          loading={searchLoading}
          style={{ maxWidth: 600 }}
        />
      </div>

      <Card className={styles['content-card']}>
        {searchResults ? renderSearchResults() : renderMemoryList()}
      </Card>
    </div>
  )
}
