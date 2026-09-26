/**
 * RichContent Component - 图文混排渲染器
 *
 * 支持在聊天结果中混合展示：
 * - 文本/Markdown 内容
 * - 数据可视化图表
 * - 数据表格
 * - 代码块
 * - 数据洞察
 * - ReAct 思考过程
 */

import Markdown from '@/components/markdown'
import { Chart, DataInsights, type ChartConfig } from '@/components/chart'
import classNames from 'classnames'
import styles from './rich-content.module.scss'

// 内容块类型
export type ContentBlockType =
  | 'text'
  | 'chart'
  | 'table'
  | 'code'
  | 'insight'
  | 'thought'
  | 'action'
  | 'observation'

// 内容块接口
export interface ContentBlock {
  type: ContentBlockType
  content: string | ChartConfig | string[] | Record<string, unknown>
  step?: number
  tool?: string
  success?: boolean
}

// 组件属性
interface RichContentProps {
  blocks: ContentBlock[]
  className?: string
  extensions?: unknown[]
}

// 思考过程组件
function ThoughtBlock(props: { content: string; step?: number }) {
  const { content, step } = props
  return (
    <div className={styles.thoughtBlock}>
      <div className={styles.blockHeader}>
        {step && <span className={styles.stepBadge}>Step {step}</span>}
        <span className={styles.blockLabel}>思考</span>
      </div>
      <div className={styles.blockContent}>{content}</div>
    </div>
  )
}

// 动作组件
function ActionBlock(props: { tool: string; params?: Record<string, unknown>; step?: number }) {
  const { tool, params, step } = props
  return (
    <div className={styles.actionBlock}>
      <div className={styles.blockHeader}>
        {step && <span className={styles.stepBadge}>Step {step}</span>}
        <span className={styles.blockLabel}>执行工具</span>
        <span className={styles.toolName}>{tool}</span>
      </div>
      {params && (
        <div className={styles.blockContent}>
          <pre className={styles.paramsCode}>
            {JSON.stringify(params, null, 2)}
          </pre>
        </div>
      )}
    </div>
  )
}

// 观察结果组件
function ObservationBlock(props: {
  content: unknown
  tool?: string
  success?: boolean
  step?: number
}) {
  const { content, tool, success, step } = props
  return (
    <div
      className={classNames(styles.observationBlock, {
        [styles.success]: success,
        [styles.error]: success === false,
      })}
    >
      <div className={styles.blockHeader}>
        {step && <span className={styles.stepBadge}>Step {step}</span>}
        <span className={styles.blockLabel}>
          {success === false ? '执行失败' : '执行结果'}
        </span>
        {tool && <span className={styles.toolName}>{tool}</span>}
      </div>
      <div className={styles.blockContent}>
        {typeof content === 'string' ? (
          content
        ) : (
          <pre className={styles.resultCode}>
            {JSON.stringify(content, null, 2)}
          </pre>
        )}
      </div>
    </div>
  )
}

// 代码块组件
function CodeBlock(props: { code: string; language?: string }) {
  const { code, language } = props
  return (
    <div className={styles.codeBlock}>
      {language && <div className={styles.codeLanguage}>{language}</div>}
      <pre className={styles.codeContent}>
        <code>{code}</code>
      </pre>
    </div>
  )
}

// 渲染单个内容块
function renderBlock(
  block: ContentBlock,
  index: number,
  extensions?: unknown[]
) {
  switch (block.type) {
    case 'text':
      return (
        <div key={index} className={styles.textBlock}>
          <Markdown
            value={block.content as string}
            extensions={extensions}
          />
        </div>
      )

    case 'chart':
      return (
        <div key={index} className={styles.chartBlock}>
          <Chart config={block.content as ChartConfig} />
        </div>
      )

    case 'table':
      return (
        <div key={index} className={styles.tableBlock}>
          <Chart
            config={{
              type: 'table',
              title: '',
              ...(block.content as Record<string, unknown>),
            } as ChartConfig}
          />
        </div>
      )

    case 'insight':
      return (
        <div key={index} className={styles.insightBlock}>
          <DataInsights insights={block.content as string[]} />
        </div>
      )

    case 'thought':
      return (
        <ThoughtBlock
          key={index}
          content={block.content as string}
          step={block.step}
        />
      )

    case 'action':
      return (
        <ActionBlock
          key={index}
          tool={block.tool || ''}
          params={block.content as Record<string, unknown>}
          step={block.step}
        />
      )

    case 'observation':
      return (
        <ObservationBlock
          key={index}
          content={block.content}
          tool={block.tool}
          success={block.success}
          step={block.step}
        />
      )

    case 'code':
      return <CodeBlock key={index} code={block.content as string} />

    default:
      return null
  }
}

// 主组件
export function RichContent(props: RichContentProps) {
  const { blocks, className, extensions } = props

  if (!blocks || blocks.length === 0) {
    return null
  }

  return (
    <div className={classNames(styles.richContent, className)}>
      {blocks.map((block, index) => renderBlock(block, index, extensions))}
    </div>
  )
}

// 辅助函数：从 SSE 事件构建内容块
export function buildContentBlocks(events: Record<string, unknown>[]): ContentBlock[] {
  const blocks: ContentBlock[] = []

  for (const event of events) {
    const type = event.type as string

    switch (type) {
      case 'thought':
        blocks.push({
          type: 'thought',
          content: event.content as string,
          step: event.step as number,
        })
        break

      case 'action':
        blocks.push({
          type: 'action',
          content: event.params as Record<string, unknown>,
          tool: event.tool as string,
          step: event.step as number,
        })
        break

      case 'observation':
        blocks.push({
          type: 'observation',
          content: event.result as unknown,
          tool: event.tool as string,
          success: event.success as boolean,
          step: event.step as number,
        })
        break

      case 'chart':
        blocks.push({
          type: 'chart',
          content: event as unknown as ChartConfig,
        })
        break

      case 'data_insight':
        blocks.push({
          type: 'insight',
          content: event.insights as string[],
        })
        break

      case 'answer':
        // 合并连续的文本
        const lastBlock = blocks[blocks.length - 1]
        if (lastBlock && lastBlock.type === 'text') {
          lastBlock.content = (lastBlock.content as string) + (event.content as string)
        } else {
          blocks.push({
            type: 'text',
            content: event.content as string,
          })
        }
        break
    }
  }

  return blocks
}

export default RichContent
