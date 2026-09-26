import { ArrowUpOutlined, ArrowDownOutlined, StockOutlined } from '@ant-design/icons'
import styles from './index.module.scss'

export interface StockQuoteData {
  code: string
  name: string
  price: string | number
  change: string | number
  change_percent: string
  high?: string
  low?: string
  volume?: string
  turnover?: string
  open?: string
  prev_close?: string
}

interface StockCardProps {
  data: StockQuoteData
}

export default function StockCard({ data }: StockCardProps) {
  const price = typeof data.price === 'string' ? parseFloat(data.price) : data.price
  const change = typeof data.change === 'string' ? parseFloat(data.change) : data.change
  const changePercent = data.change_percent?.replace('%', '') || '0'
  const isUp = change > 0
  const isDown = change < 0

  return (
    <div className={`${styles.card} ${isUp ? styles.up : isDown ? styles.down : styles.flat}`}>
      <div className={styles.header}>
        <div className={styles.nameSection}>
          <StockOutlined className={styles.icon} />
          <span className={styles.name}>{data.name}</span>
          <span className={styles.code}>{data.code}</span>
        </div>
        <div className={styles.badge}>
          {isUp ? '涨' : isDown ? '跌' : '平'}
        </div>
      </div>

      <div className={styles.priceSection}>
        <div className={styles.currentPrice}>
          <span className={styles.currency}>¥</span>
          <span className={styles.priceValue}>{price?.toFixed(2) || '--'}</span>
        </div>
        <div className={styles.changeInfo}>
          {isUp ? <ArrowUpOutlined /> : isDown ? <ArrowDownOutlined /> : null}
          <span className={styles.changeValue}>
            {change > 0 ? '+' : ''}{change?.toFixed(2) || '0.00'}
          </span>
          <span className={styles.changePercent}>
            ({change > 0 ? '+' : ''}{changePercent}%)
          </span>
        </div>
      </div>

      <div className={styles.details}>
        <div className={styles.detailItem}>
          <span className={styles.label}>今开</span>
          <span className={styles.value}>{data.open || '--'}</span>
        </div>
        <div className={styles.detailItem}>
          <span className={styles.label}>昨收</span>
          <span className={styles.value}>{data.prev_close || '--'}</span>
        </div>
        <div className={styles.detailItem}>
          <span className={styles.label}>最高</span>
          <span className={`${styles.value} ${styles.high}`}>{data.high || '--'}</span>
        </div>
        <div className={styles.detailItem}>
          <span className={styles.label}>最低</span>
          <span className={`${styles.value} ${styles.low}`}>{data.low || '--'}</span>
        </div>
        <div className={styles.detailItem}>
          <span className={styles.label}>成交量</span>
          <span className={styles.value}>{data.volume || '--'}</span>
        </div>
        <div className={styles.detailItem}>
          <span className={styles.label}>成交额</span>
          <span className={styles.value}>{data.turnover || '--'}</span>
        </div>
      </div>

      <div className={styles.source}>
        数据来源: 聚合数据股票API (实时)
      </div>
    </div>
  )
}
