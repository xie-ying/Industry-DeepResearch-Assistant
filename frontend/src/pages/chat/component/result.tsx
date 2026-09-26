import IconImage from '@/assets/chat/image.svg'
import IconSource from '@/assets/chat/source.svg'
import IconThink from '@/assets/chat/think.svg'
import Markdown from '@/components/markdown'
import StockCard from '@/components/stock-card'
import host from '@/configs/data/host'
import { CheckOutlined, BulbOutlined, ThunderboltOutlined, EyeOutlined } from '@ant-design/icons'
import classNames from 'classnames'
import { TokenizerAndRendererExtension } from 'marked'
import { useMemo } from 'react'
import styles from './result.module.scss'
import Section from './section'

function findHost(url: string) {
  return host.find((o) => {
    try {
      const _url = new URL(url)
      const hostname = _url.hostname
      if (hostname === o.url) return true
      if (hostname.replace(/^www\./, '') === o.url.replace(/^www\./, ''))
        return true
      if (
        hostname.split('.').length >= 2 &&
        hostname.replace(/^.+?\.(.+)$/, '$1') === o.url.replace(/^www\./, '')
      )
        return true

      return false
    } catch (err) {
      console.error(err)
      return false
    }
  })
}

const 来源 = (props: { item: API.ChatItem }) => {
  const { item } = props

  const source = useMemo(() => {
    return {
      web: item.reference
        ?.filter((item) => item.source === 'web')
        .map((item) => ({
          ...item,
          hostname: findHost(item.link)?.name,
        })),
      knowledge: item.reference
        ?.filter((item) => item.source === 'knowledge')
        .map((item) => ({
          ...item,
          hostname: findHost(item.link)?.name,
        })),
    }
  }, [item])

  return (
    <>
      {source.knowledge?.length ? (
        <Section title="相关知识库来源" icon={IconSource} defaultOpen>
          <div className={styles['chat-message-result__source']}>
            {source.knowledge?.map((item, index) => {
              // 截断标题，保留合理长度
              const displayTitle = item.title && item.title !== '来源' && !item.title.startsWith('来源 ')
                ? (item.title.length > 40 ? item.title.slice(0, 40) + '...' : item.title)
                : (item.content ? (item.content.slice(0, 40) + '...') : (item.hostname || '知识库来源'))
              // 确保链接有效
              const validLink = item.link && item.link.startsWith('http') ? item.link : undefined
              return (
                <div
                  key={`knowledge-${index}-${item.id}`}
                  className={styles.item}
                  onClick={() => validLink && window.open(validLink, '_blank')}
                  style={{ cursor: validLink ? 'pointer' : 'default' }}
                >
                  <div className={styles.header}>
                    <div className={styles.id}>[{item.id}]</div>
                    <div className={styles.title}>{displayTitle}</div>
                  </div>
                  <div className={styles.sourceUrl}>{item.hostname || '知识库'}</div>
                </div>
              )
            })}
          </div>
        </Section>
      ) : null}

      {source.web?.length ? (
        <Section title="相关网络来源" icon={IconSource} defaultOpen>
          <div className={styles['chat-message-result__source']}>
            {source.web?.map((item, index) => {
              // 从链接中提取域名作为备用
              let domainName = ''
              try {
                if (item.link) {
                  const url = new URL(item.link)
                  domainName = url.hostname.replace(/^www\./, '')
                }
              } catch (e) {
                domainName = item.link || ''
              }
              // 截断标题，保留合理长度
              const displayTitle = item.title && item.title !== '来源' && !item.title.startsWith('来源 ')
                ? (item.title.length > 40 ? item.title.slice(0, 40) + '...' : item.title)
                : (item.content ? (item.content.slice(0, 40) + '...') : (domainName || '网络来源'))
              // 确保链接有效
              const validLink = item.link && item.link.startsWith('http') ? item.link : undefined
              return (
                <div
                  key={`web-${index}-${item.id}`}
                  className={styles.item}
                  onClick={() => validLink && window.open(validLink, '_blank')}
                  style={{ cursor: validLink ? 'pointer' : 'default' }}
                >
                  <div className={styles.header}>
                    <div className={styles.id}>[{item.id}]</div>
                    <div className={styles.title}>{displayTitle}</div>
                  </div>
                  <div className={styles.sourceUrl}>{domainName || '未知来源'}</div>
                </div>
              )
            })}
          </div>
        </Section>
      ) : null}
    </>
  )
}

const 图像 = (props: { item: API.ChatItem }) => {
  const { item } = props

  return (
    <Section title="图像" icon={IconImage} defaultOpen>
      <div className={styles['chat-message-result__images']}>
        {item.image_results?.images?.map((item, index) => (
          <div
            className={styles.item}
            key={index}
            onClick={() => window.open(item.link, '_blank')}
          >
            <div className={styles.box}>
              <img className={styles.cover} src={item.thumbnailUrl} />
            </div>
          </div>
        ))}
      </div>
    </Section>
  )
}

const 思考过程 = (props: { item: API.ChatItem }) => {
  const { item } = props

  return (
    <div className={styles['chat-message-result__thinks']}>
      {item.thinks?.map((o, index) => (
        <div key={o.id} className={styles['chat-message-result__thinks-item']}>
          <div className={styles['header']}>
            <div
              className={classNames(styles['header-icon'], {
                [styles['thinking']]:
                  index === item.thinks!.length - 1 && !item.think,
              })}
            >
              {item.thinks!.length - 1 && !item.think ? (
                <div
                  style={{
                    width: 6,
                    height: 6,
                    backgroundColor: '#fff',
                    borderRadius: 1,
                  }}
                ></div>
              ) : (
                <CheckOutlined />
              )}
            </div>
            {
              {
                status: '思考',
                search_results: '执行',
              }[o.type]
            }
          </div>

          <div className={styles['thinks-results']}>
            {o.results?.map((item) => (
              <div className={styles['thinks-results__item']} key={item.id}>
                <div className={styles.content}>{item.content}</div>
                {/* {item.count ? (
                  <div className={styles.count}>找到{item.count}个来源</div>
                ) : null} */}
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  )
}

// 渲染观察内容的辅助函数
const renderObservationContent = (content: string) => {
  const lines = content.split('\n')
  return lines.map((line, i) => {
    // 解析带有统计数据的行
    const sectionMatch = line.match(/^📑\s*(.+)$/)
    const factsMatch = line.match(/^事实:\s*(\d+)\s*条$/)
    const dataPointsMatch = line.match(/^数据点:\s*(\d+)\s*个$/)
    const dedupeMatch = line.match(/^去重:\s*(\d+)\s*条$/)
    const qualityMatch = line.match(/^来源质量:\s*(.+)$/)
    const insightsMatch = line.match(/^洞察:$/)
    const insightItemMatch = line.match(/^\s+•\s*(.+)$/)

    if (sectionMatch) {
      return (
        <div key={i} className={styles['obs-section']}>
          <span className={styles['obs-section-icon']}>📑</span>
          <span className={styles['obs-section-name']}>{sectionMatch[1]}</span>
        </div>
      )
    }
    if (factsMatch) {
      return (
        <div key={i} className={styles['obs-stat']}>
          <span className={styles['obs-stat-label']}>事实</span>
          <span className={styles['obs-stat-value']}>{factsMatch[1]}</span>
          <span className={styles['obs-stat-unit']}>条</span>
        </div>
      )
    }
    if (dataPointsMatch) {
      return (
        <div key={i} className={styles['obs-stat']}>
          <span className={styles['obs-stat-label']}>数据点</span>
          <span className={styles['obs-stat-value']}>{dataPointsMatch[1]}</span>
          <span className={styles['obs-stat-unit']}>个</span>
        </div>
      )
    }
    if (dedupeMatch) {
      return (
        <div key={i} className={styles['obs-stat']}>
          <span className={styles['obs-stat-label']}>去重</span>
          <span className={styles['obs-stat-value']}>{dedupeMatch[1]}</span>
          <span className={styles['obs-stat-unit']}>条</span>
        </div>
      )
    }
    if (qualityMatch) {
      return (
        <div key={i} className={styles['obs-quality']}>
          <div className={styles['obs-quality-label']}>来源质量</div>
          <div className={styles['obs-quality-value']}>{qualityMatch[1]}</div>
        </div>
      )
    }
    if (insightsMatch) {
      return (
        <div key={i} className={styles['obs-insights-title']}>洞察</div>
      )
    }
    if (insightItemMatch) {
      return (
        <div key={i} className={styles['obs-insight-item']}>
          <span className={styles['obs-insight-bullet']}>•</span>
          <span>{insightItemMatch[1]}</span>
        </div>
      )
    }
    // 默认渲染
    return line ? <div key={i}>{line}</div> : null
  })
}

// ReAct 智能推理过程组件
const ReAct过程 = (props: { item: API.ChatItem; onStepClick?: (stepId: string) => void }) => {
  const { item, onStepClick } = props

  if (!item.reactSteps?.length) return null

  const getStepIcon = (type: string) => {
    switch (type) {
      case 'plan':
        return <BulbOutlined style={{ color: '#722ed1' }} />
      case 'thought':
        return <BulbOutlined style={{ color: '#faad14' }} />
      case 'action':
        return <ThunderboltOutlined style={{ color: '#1677ff' }} />
      case 'observation':
        return <EyeOutlined style={{ color: '#52c41a' }} />
      default:
        return <CheckOutlined />
    }
  }

  const getStepLabel = (type: string) => {
    switch (type) {
      case 'plan':
        return '研究计划'
      case 'thought':
        return '思考'
      case 'action':
        return '行动'
      case 'observation':
        return '观察'
      default:
        return type
    }
  }

  return (
    <div className={styles['react-process']}>
      <div className={styles['react-title']}>
        <BulbOutlined /> ReAct 智能推理过程
      </div>
      {item.reactSteps.map((step, index) => {
        const isClickable = step.type === 'observation' && step.stepId
        return (
          <div
            key={index}
            className={classNames(
              styles['react-step'],
              styles[`react-step--${step.type}`],
              { [styles['react-step--clickable']]: isClickable }
            )}
            onClick={() => {
              if (isClickable && onStepClick) {
                onStepClick(step.stepId!)
              }
            }}
          >
            <div className={styles['react-step-header']}>
              {step.type !== 'plan' && (
                <span className={styles['react-step-badge']}>Step {step.step}</span>
              )}
              <span className={styles['react-step-icon']}>{getStepIcon(step.type)}</span>
              <span className={styles['react-step-label']}>{getStepLabel(step.type)}</span>
              {step.tool && step.tool !== 'parallel_search' && (
                <span className={styles['react-step-tool']}>{step.tool}</span>
              )}
              {step.tool === 'parallel_search' && (
                <span className={styles['react-step-tool']}>并行搜索</span>
              )}
              {isClickable && (
                <span className={styles['react-step-detail-hint']}>点击查看详情 →</span>
              )}
            </div>
            <div className={styles['react-step-content']}>
              {step.content != null && (
                typeof step.content === 'string' && step.content
                  ? (step.type === 'plan'
                      ? <Markdown className={styles['react-step-markdown']} value={step.content} />
                      : step.type === 'observation'
                        ? renderObservationContent(step.content)
                        : step.content.split('\n').map((line, i) => (
                            <div key={i}>{line}</div>
                          ))
                    )
                  : typeof step.content === 'object'
                    ? <pre>{JSON.stringify(step.content, null, 2)}</pre>
                    : <div>{String(step.content)}</div>
              )}
              {step.params && step.tool !== 'parallel_search' && (
                <pre className={styles['react-step-params']}>
                  {JSON.stringify(step.params, null, 2)}
                </pre>
              )}
            </div>
          </div>
        )
      })}
    </div>
  )
}

// 数据洞察组件
const 数据洞察 = (props: { item: API.ChatItem }) => {
  const { item } = props

  if (!item.insights?.length) return null

  return (
    <div className={styles['data-insights']}>
      <div className={styles['insights-title']}>
        <BulbOutlined /> 数据洞察
      </div>
      <ul className={styles['insights-list']}>
        {item.insights.map((insight, index) => (
          <li key={index}>{insight}</li>
        ))}
      </ul>
    </div>
  )
}

export function Result(props: {
  item: API.ChatItem
  isEnd?: boolean
  onSend?: (text: string) => void
  onStepClick?: (stepId: string) => void
}) {
  const { item, onStepClick } = props

  /* markdown */
  const extensions = useMemo<TokenizerAndRendererExtension[]>(
    () => [
      {
        name: 'reference',
        level: 'inline',
        start(src) {
          return src.match(/##\d+\$\$/)?.index
        },
        tokenizer(src) {
          const match = /^##(\d+?)\$\$/.exec(src)
          if (match) {
            const [raw, index] = match
            return {
              type: 'reference',
              raw,
              index: this.lexer.inlineTokens(index),
              tokens: [],
            }
          }
        },
        renderer(token) {
          const index = this.parser.parseInline(token.index)
          const id = Number(index) + 1
          const target = item.reference?.find((item) => item.id === id)
          return `<a class="refrence-token" href="${target?.link || 'javascript: void 0'}" target="${target?.link ? '_blank' : '_self'}">[${Number(index) + 1}]</a>`
        },
      },
    ],
    [item, item.reference],
  )

  return (
    <div className={styles['chat-message-result']}>
      <Section title="智能回答" icon={IconThink} defaultOpen>
        {/* ReAct 智能推理过程 */}
        {item.reactSteps?.length ? <ReAct过程 item={item} onStepClick={onStepClick} /> : null}

        {/* 传统思考过程 */}
        {item.thinks && !item.reactSteps?.length ? <思考过程 item={item} /> : null}

        {/* 数据洞察 */}
        {item.insights?.length ? <数据洞察 item={item} /> : null}

        {/* 股票实时行情 */}
        {item.stockQuote ? <StockCard data={item.stockQuote} /> : null}

        {item.think ? (
          <Markdown
            className={classNames(
              styles['chat-message-result__think'],
              styles['chat-message-result__md'],
            )}
            value={item.think}
            extensions={extensions}
          />
        ) : null}

        <Markdown
          className={styles['chat-message-result__md']}
          value={item.content}
          extensions={extensions}
        />
      </Section>

      {item.reference?.length && !item.loading ? <来源 item={item} /> : null}

      {item.image_results?.images?.length && !item.loading ? (
        <图像 item={item} />
      ) : null}
    </div>
  )
}
