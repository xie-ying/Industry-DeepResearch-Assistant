import { useEffect, useState, useCallback } from 'react'
import {
  Card,
  Button,
  Tag,
  message,
  Empty,
  Skeleton,
  Pagination,
  Select,
  Statistic,
  Row,
  Col,
} from 'antd'
import {
  ProjectOutlined,
  ReloadOutlined,
  ClockCircleOutlined,
  EnvironmentOutlined,
  SyncOutlined,
} from '@ant-design/icons'
import { useSnapshot } from 'valtio'
import { authState } from '@/store/auth'
import { industryState, getCurrentIndustry } from '@/store/industry'
import { useNavigate } from 'react-router-dom'
import * as api from '@/api'
import type { BiddingItem, BiddingStats } from '@/api/news'
import CollectionModal, { CollectionResult } from '@/components/collection-modal'
import styles from './index.module.scss'

// 招投标类型
const BIDDING_TYPES = [
  { label: '全部', value: '' },
  { label: '招标', value: '招标' },
  { label: '中标', value: '中标' },
]

export default function BiddingPage() {
  const navigate = useNavigate()
  const { isLoggedIn } = useSnapshot(authState)
  const { currentIndustryId } = useSnapshot(industryState)
  const currentIndustry = getCurrentIndustry()

  // 招投标状态
  const [biddingList, setBiddingList] = useState<BiddingItem[]>([])
  const [biddingLoading, setBiddingLoading] = useState(false)
  const [biddingType, setBiddingType] = useState('')
  const [biddingProvince, setBiddingProvince] = useState('')
  const [biddingPage, setBiddingPage] = useState(1)
  const [biddingTotal, setBiddingTotal] = useState(0)
  const [biddingStats, setBiddingStats] = useState<BiddingStats | null>(null)

  // 采集状态
  const [collecting, setCollecting] = useState(false)
  const [collectionModalOpen, setCollectionModalOpen] = useState(false)
  const [collectionResult, setCollectionResult] = useState<CollectionResult | null>(null)

  const pageSize = 20

  // 获取招投标列表
  const fetchBidding = useCallback(async () => {
    setBiddingLoading(true)
    try {
      const res = await api.news.getBiddingList({
        notice_type: biddingType || undefined,
        province: biddingProvince || undefined,
        industry_id: currentIndustryId,
        limit: pageSize,
        offset: (biddingPage - 1) * pageSize,
      })
      if (res.success) {
        setBiddingList(res.data)
        setBiddingTotal(res.total)
        setBiddingStats(res.stats)
      }
    } catch (error: any) {
      console.error('[BiddingPage] fetchBidding 错误:', error)
      message.error(error?.response?.data?.detail || '获取招投标信息失败')
    } finally {
      setBiddingLoading(false)
    }
  }, [biddingType, biddingProvince, biddingPage, currentIndustryId])

  useEffect(() => {
    if (isLoggedIn) {
      fetchBidding()
    }
  }, [isLoggedIn, fetchBidding])

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
        await fetchBidding()
      }
    } catch (error: any) {
      console.error('[BiddingPage] handleCollect 错误:', error)
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

  if (!isLoggedIn) {
    return (
      <div className={styles['bidding-page']}>
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
    <div className={styles['bidding-page']}>
      <div className={styles.header}>
        <div className={styles['header-left']}>
          <ProjectOutlined style={{ fontSize: 24, marginRight: 12 }} />
          <h2>招投标信息</h2>
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
                title="招投标总数"
                value={biddingStats?.total || 0}
                prefix={<ProjectOutlined />}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card size="small">
              <Statistic
                title="招标"
                value={biddingStats?.by_type?.['招标'] || 0}
                valueStyle={{ color: '#1890ff' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card size="small">
              <Statistic
                title="中标"
                value={biddingStats?.by_type?.['中标'] || 0}
                valueStyle={{ color: '#52c41a' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card size="small">
              <Statistic
                title="省份覆盖"
                value={Object.keys(biddingStats?.by_province || {}).length}
                suffix="个"
              />
            </Card>
          </Col>
        </Row>

        {/* 筛选 */}
        <div className={styles.filters}>
          <Select
            placeholder="公告类型"
            allowClear
            style={{ width: 120 }}
            value={biddingType || undefined}
            onChange={(val) => {
              setBiddingType(val || '')
              setBiddingPage(1)
            }}
            options={BIDDING_TYPES.map((t) => ({ label: t.label, value: t.value }))}
          />
          <Select
            placeholder="省份"
            allowClear
            style={{ width: 140 }}
            value={biddingProvince || undefined}
            onChange={(val) => {
              setBiddingProvince(val || '')
              setBiddingPage(1)
            }}
            options={[
              { label: '全部', value: '' },
              ...Object.keys(biddingStats?.by_province || {}).map((p) => ({
                label: p,
                value: p,
              }))
            ]}
          />
        </div>

        {/* 招投标列表 */}
        {biddingLoading ? (
          <div className={styles['bidding-list']}>
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className={styles['bidding-item']}>
                <Skeleton active paragraph={{ rows: 2 }} />
              </div>
            ))}
          </div>
        ) : biddingList.length === 0 ? (
          <Empty description="暂无招投标信息" />
        ) : (
          <div className={styles['bidding-list']}>
            {biddingList.map((item) => (
              <div key={item.id} className={styles['bidding-item']}>
                <div className={styles['bidding-title']}>{item.title}</div>
                <div className={styles['bidding-info']}>
                  <span className={styles['info-item']}>
                    <Tag color={item.notice_type === '中标' ? 'green' : 'blue'}>
                      {item.notice_type}
                    </Tag>
                  </span>
                  <span className={styles['info-item']}>
                    <EnvironmentOutlined />
                    {item.province}
                    {item.city && ` ${item.city}`}
                  </span>
                </div>
                <div className={styles['bidding-meta']}>
                  <span>
                    <ClockCircleOutlined style={{ marginRight: 4 }} />
                    发布于 {formatTime(item.publish_time || item.collected_at)}
                  </span>
                  <span>ID: {item.bid_id}</span>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* 分页 */}
        {biddingTotal > pageSize && (
          <div className={styles['pagination-wrapper']}>
            <Pagination
              current={biddingPage}
              pageSize={pageSize}
              total={biddingTotal}
              onChange={(page) => setBiddingPage(page)}
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
