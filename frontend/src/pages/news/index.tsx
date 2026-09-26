import { useEffect, useState, useCallback } from 'react'
import {
  Card,
  Button,
  Tag,
  message,
  Empty,
  Skeleton,
  Pagination,
  Statistic,
  Row,
  Col,
} from 'antd'
import {
  FileTextOutlined,
  ReloadOutlined,
  ClockCircleOutlined,
  BankOutlined,
  LinkOutlined,
  SyncOutlined,
} from '@ant-design/icons'
import { useSnapshot } from 'valtio'
import { authState } from '@/store/auth'
import { industryState, getCurrentIndustry } from '@/store/industry'
import { useNavigate } from 'react-router-dom'
import * as api from '@/api'
import type { NewsItem, NewsStats } from '@/api/news'
import CollectionModal, { CollectionResult } from '@/components/collection-modal'
import styles from './index.module.scss'

// 资讯分类
const NEWS_CATEGORIES = [
  { label: '全部', value: '' },
  { label: '政策', value: '政策' },
  { label: '研报', value: '研报' },
  { label: '新闻', value: '新闻' },
]

export default function NewsPage() {
  const navigate = useNavigate()
  const { isLoggedIn } = useSnapshot(authState)
  const { currentIndustryId } = useSnapshot(industryState)
  const currentIndustry = getCurrentIndustry()

  // 资讯状态
  const [newsList, setNewsList] = useState<NewsItem[]>([])
  const [newsLoading, setNewsLoading] = useState(false)
  const [newsCategory, setNewsCategory] = useState('')
  const [newsPage, setNewsPage] = useState(1)
  const [newsTotal, setNewsTotal] = useState(0)
  const [newsStats, setNewsStats] = useState<NewsStats | null>(null)

  // 采集状态
  const [collecting, setCollecting] = useState(false)
  const [collectionModalOpen, setCollectionModalOpen] = useState(false)
  const [collectionResult, setCollectionResult] = useState<CollectionResult | null>(null)

  const pageSize = 20

  // 获取资讯列表
  const fetchNews = useCallback(async () => {
    setNewsLoading(true)
    try {
      const res = await api.news.getNewsList({
        category: newsCategory || undefined,
        industry_id: currentIndustryId,
        limit: pageSize,
        offset: (newsPage - 1) * pageSize,
      })
      if (res.success) {
        setNewsList(res.data)
        setNewsTotal(res.total)
        setNewsStats(res.stats)
      }
    } catch (error: any) {
      console.error('[NewsPage] fetchNews 错误:', error)
      message.error(error?.response?.data?.detail || '获取资讯失败')
    } finally {
      setNewsLoading(false)
    }
  }, [newsCategory, newsPage, currentIndustryId])

  useEffect(() => {
    if (isLoggedIn) {
      fetchNews()
    }
  }, [isLoggedIn, fetchNews])

  // 手动触发采集
  const handleCollect = async () => {
    // 打开模态框
    setCollectionModalOpen(true)
    setCollectionResult(null)
    setCollecting(true)

    try {
      const res = await api.news.triggerCollection({
        max_news: 50,
        max_bidding: 50,
        industry_id: currentIndustryId,
      })

      // 设置结果
      setCollectionResult(res)

      // 刷新数据
      if (res.success) {
        await fetchNews()
      }
    } catch (error: any) {
      console.error('[NewsPage] handleCollect 错误:', error)
      setCollectionResult({
        success: false,
        message: '采集失败',
        news_collected: 0,
        bidding_collected: 0,
        errors: [error?.message || '网络请求失败'],
      })
    } finally {
      setCollecting(false)
    }
  }

  // 关闭模态框
  const handleCloseModal = () => {
    if (!collecting) {
      setCollectionModalOpen(false)
      setCollectionResult(null)
    }
  }

  // 格式化时间
  const formatTime = (timeStr: string) => {
    if (!timeStr) return '-'
    const date = new Date(timeStr)
    return date.toLocaleDateString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
    })
  }

  // 打开链接
  const openLink = (url: string) => {
    if (url) {
      window.open(url, '_blank')
    }
  }

  if (!isLoggedIn) {
    return (
      <div className={styles['news-page']}>
        <div className={styles['empty-state']}>
          <Empty description="请先登录" />
          <Button type="primary" onClick={() => navigate('/login')}>
            去登录
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className={styles['news-page']}>
      <div className={styles.header}>
        <div className={styles['header-left']}>
          <FileTextOutlined style={{ fontSize: 24, marginRight: 12 }} />
          <h2>行业资讯</h2>
          <Tag color="purple" style={{ marginLeft: 12 }}>{currentIndustry.name}</Tag>
        </div>
        <div className={styles['header-right']}>
          <Button
            type="primary"
            icon={collecting ? <SyncOutlined spin /> : <ReloadOutlined />}
            onClick={handleCollect}
            disabled={collecting}
          >
            {collecting ? '采集中...' : '立即采集'}
          </Button>
        </div>
      </div>

      <Card>
        {/* 统计信息 */}
        <Row gutter={16} style={{ marginBottom: 24 }}>
          <Col span={6}>
            <Card size="small">
              <Statistic
                title="资讯总数"
                value={newsStats?.total || 0}
                prefix={<FileTextOutlined />}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card size="small">
              <Statistic
                title="24小时更新"
                value={newsStats?.recent_24h || 0}
                valueStyle={{ color: '#3f8600' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card size="small">
              <Statistic
                title="政策"
                value={newsStats?.by_category?.['政策'] || 0}
                valueStyle={{ color: '#1890ff' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card size="small">
              <Statistic
                title="研报"
                value={newsStats?.by_category?.['研报'] || 0}
                valueStyle={{ color: '#722ed1' }}
              />
            </Card>
          </Col>
        </Row>

        {/* 分类筛选 */}
        <div className={styles.filters}>
          <div className={styles['category-tags']}>
            {NEWS_CATEGORIES.map((cat) => (
              <span
                key={cat.value}
                className={`${styles['category-tag']} ${
                  newsCategory === cat.value ? styles.active : ''
                }`}
                onClick={() => {
                  setNewsCategory(cat.value)
                  setNewsPage(1)
                }}
              >
                {cat.label}
              </span>
            ))}
          </div>
        </div>

        {/* 资讯列表 */}
        {newsLoading ? (
          <div className={styles['news-list']}>
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className={styles['news-item']}>
                <Skeleton active paragraph={{ rows: 3 }} />
              </div>
            ))}
          </div>
        ) : newsList.length === 0 ? (
          <Empty description="暂无资讯" />
        ) : (
          <div className={styles['news-list']}>
            {newsList.map((item) => (
              <div
                key={item.id}
                className={styles['news-item']}
                onClick={() => openLink(item.source_url)}
              >
                <div className={styles['news-title']}>
                  {item.title}
                </div>
                {item.content && (
                  <div className={styles['news-content']}>{item.content}</div>
                )}
                <div className={styles['news-meta']}>
                  <span className={styles['meta-item']}>
                    <ClockCircleOutlined />
                    {formatTime(item.publish_time || item.collected_at)}
                  </span>
                  {item.department && (
                    <span className={styles['meta-item']}>
                      <BankOutlined />
                      {item.department}
                    </span>
                  )}
                  <span className={styles['meta-item']}>
                    <LinkOutlined />
                    {item.source || '未知来源'}
                  </span>
                  <Tag
                    color={
                      item.category === '政策'
                        ? 'blue'
                        : item.category === '研报'
                        ? 'purple'
                        : 'default'
                    }
                  >
                    {item.category || '新闻'}
                  </Tag>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* 分页 */}
        {newsTotal > pageSize && (
          <div className={styles['pagination-wrapper']}>
            <Pagination
              current={newsPage}
              pageSize={pageSize}
              total={newsTotal}
              onChange={(page) => setNewsPage(page)}
              showTotal={(total) => `共 ${total} 条`}
            />
          </div>
        )}
      </Card>

      {/* 采集进度模态框 */}
      <CollectionModal
        open={collectionModalOpen}
        collecting={collecting}
        result={collectionResult}
        industryName={currentIndustry.name}
        onClose={handleCloseModal}
      />
    </div>
  )
}
