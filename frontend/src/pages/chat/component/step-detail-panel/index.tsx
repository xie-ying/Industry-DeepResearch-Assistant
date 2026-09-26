import { LinkOutlined, FileTextOutlined, BarChartOutlined, BulbOutlined } from '@ant-design/icons'
import { Empty, Tag, Collapse } from 'antd'
import styles from './index.module.scss'

// 搜索结果类型
interface SearchResult {
  title: string
  url: string
  source: string
  snippet: string
  date?: string
}

// 提取的事实类型
interface ExtractedFact {
  content: string
  source_name: string
  source_url: string
  credibility: number
}

// 数据点类型
interface DataPoint {
  name: string
  value: string
  unit: string
  year?: number
  source?: string
}

// 步骤详情类型
export interface StepDetailData {
  stepId: string
  type: string
  section?: string
  searchResults?: SearchResult[]
  extractedFacts?: ExtractedFact[]
  dataPoints?: DataPoint[]
  insights?: string[]
  outline?: any[]
  content?: string
}

interface StepDetailPanelProps {
  detail: StepDetailData | null
  onClose?: () => void
}

export default function StepDetailPanel({ detail, onClose }: StepDetailPanelProps) {
  if (!detail) {
    return (
      <div className={styles.panel}>
        <div className={styles.empty}>
          <Empty description="点击左侧步骤查看详情" />
        </div>
      </div>
    )
  }

  const hasSearchResults = detail.searchResults && detail.searchResults.length > 0
  const hasFacts = detail.extractedFacts && detail.extractedFacts.length > 0
  const hasDataPoints = detail.dataPoints && detail.dataPoints.length > 0
  const hasInsights = detail.insights && detail.insights.length > 0

  return (
    <div className={styles.panel}>
      <div className={styles.header}>
        <span className={styles.title}>
          {detail.section ? `📑 ${detail.section}` : '步骤详情'}
        </span>
        <Tag color="blue">{detail.type}</Tag>
      </div>

      <div className={styles.content}>
        {/* 搜索结果 */}
        {hasSearchResults && (
          <div className={styles.section}>
            <div className={styles.sectionTitle}>
              <LinkOutlined /> 搜索结果 ({detail.searchResults!.length})
            </div>
            <div className={styles.searchResults}>
              {detail.searchResults!.map((item, index) => (
                <div
                  key={index}
                  className={styles.searchItem}
                  onClick={() => item.url && window.open(item.url, '_blank')}
                >
                  <div className={styles.searchTitle}>{item.title || '无标题'}</div>
                  <div className={styles.searchMeta}>
                    <span className={styles.source}>{item.source || '未知来源'}</span>
                    {item.date && <span className={styles.date}>{item.date}</span>}
                  </div>
                  {item.snippet && (
                    <div className={styles.searchSnippet}>{item.snippet}</div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 提取的事实 */}
        {hasFacts && (
          <div className={styles.section}>
            <div className={styles.sectionTitle}>
              <FileTextOutlined /> 提取的事实 ({detail.extractedFacts!.length})
            </div>
            <div className={styles.factsList}>
              {detail.extractedFacts!.map((fact, index) => (
                <div key={index} className={styles.factItem}>
                  <div className={styles.factContent}>{fact.content}</div>
                  <div className={styles.factMeta}>
                    <span className={styles.factSource}>{fact.source_name}</span>
                    <Tag
                      color={fact.credibility >= 0.8 ? 'green' : fact.credibility >= 0.5 ? 'orange' : 'red'}
                      className={styles.credibilityTag}
                    >
                      可信度 {(fact.credibility * 100).toFixed(0)}%
                    </Tag>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 数据点 */}
        {hasDataPoints && (
          <div className={styles.section}>
            <div className={styles.sectionTitle}>
              <BarChartOutlined /> 数据点 ({detail.dataPoints!.length})
            </div>
            <div className={styles.dataPointsList}>
              {detail.dataPoints!.map((dp, index) => (
                <div key={index} className={styles.dataPointItem}>
                  <span className={styles.dpName}>{dp.name}</span>
                  <span className={styles.dpValue}>
                    {dp.value} {dp.unit}
                  </span>
                  {dp.year && <span className={styles.dpYear}>({dp.year})</span>}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 洞察 */}
        {hasInsights && (
          <div className={styles.section}>
            <div className={styles.sectionTitle}>
              <BulbOutlined /> 关键洞察
            </div>
            <ul className={styles.insightsList}>
              {detail.insights!.map((insight, index) => (
                <li key={index}>{insight}</li>
              ))}
            </ul>
          </div>
        )}

        {/* 无详细数据时显示内容 */}
        {!hasSearchResults && !hasFacts && !hasDataPoints && !hasInsights && detail.content && (
          <div className={styles.section}>
            <div className={styles.plainContent}>{detail.content}</div>
          </div>
        )}
      </div>
    </div>
  )
}
