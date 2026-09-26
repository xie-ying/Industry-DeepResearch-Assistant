import { useState, useMemo } from 'react'
import Markdown from '@/components/markdown'
import ReactECharts from 'echarts-for-react'
import styles from './process-report.module.scss'

export interface SectionDraft {
  id: string
  title: string
  content: string
  wordCount?: number
}

export interface ChartData {
  id: string
  title: string
  subtitle?: string
  type?: string
  echarts_option?: Record<string, unknown>
  image_base64?: string
}

export interface KnowledgeGraphData {
  nodes: Array<{ id: string; name: string; type: string }>
  edges: Array<{ source: string; target: string; relation: string }>
}

interface ProcessReportProps {
  content?: string  // 最终报告
  sections?: SectionDraft[]  // 章节草稿
  charts?: ChartData[]  // 图表数据
  knowledgeGraph?: KnowledgeGraphData  // 知识图谱
}

// 渲染单个图表
function ChartRenderer({ chart, inline = false }: { chart: ChartData; inline?: boolean }) {
  if (chart.image_base64) {
    return (
      <div className={`${styles.chartCard} ${inline ? styles.inlineChart : ''}`}>
        <div className={styles.chartTitle}>📊 {chart.title}</div>
        <img
          src={`data:image/png;base64,${chart.image_base64}`}
          alt={chart.title}
          className={styles.chartImage}
        />
      </div>
    )
  }
  if (chart.echarts_option) {
    return (
      <div className={`${styles.chartCard} ${inline ? styles.inlineChart : ''}`}>
        <div className={styles.chartTitle}>📊 {chart.title}</div>
        <div className={styles.echartsWrapper}>
          <ReactECharts
            option={chart.echarts_option}
            style={{ height: '300px', width: '100%' }}
            opts={{ renderer: 'canvas' }}
          />
        </div>
      </div>
    )
  }
  return null
}

// 简单的文本相似度计算（用于匹配图表标题）
function textSimilarity(text1: string, text2: string): number {
  const s1 = text1.toLowerCase().replace(/[^\u4e00-\u9fa5a-z0-9]/g, '')
  const s2 = text2.toLowerCase().replace(/[^\u4e00-\u9fa5a-z0-9]/g, '')
  if (s1 === s2) return 1
  if (s1.includes(s2) || s2.includes(s1)) return 0.8
  // 计算共同字符比例
  const chars1 = new Set(s1.split(''))
  const chars2 = new Set(s2.split(''))
  const common = [...chars1].filter(c => chars2.has(c)).length
  return common / Math.max(chars1.size, chars2.size)
}

// 查找最匹配的图表
function findMatchingChart(altText: string, charts: ChartData[]): ChartData | null {
  if (!charts || charts.length === 0) return null

  let bestMatch: ChartData | null = null
  let bestScore = 0.5 // 最低相似度阈值

  for (const chart of charts) {
    const score = textSimilarity(altText, chart.title)
    if (score > bestScore) {
      bestScore = score
      bestMatch = chart
    }
  }

  return bestMatch
}

// 内容块类型
type ContentBlock =
  | { type: 'markdown'; content: string }
  | { type: 'chart'; chart: ChartData }
  | { type: 'knowledgeGraph'; data: KnowledgeGraphData }

// 查找图表最匹配的章节标题
function findBestSectionForChart(chartTitle: string, sectionTitles: string[]): number {
  let bestIndex = -1
  let bestScore = 0.2 // 降低相似度阈值，让更多图表能匹配到章节

  for (let i = 0; i < sectionTitles.length; i++) {
    const score = textSimilarity(chartTitle, sectionTitles[i])
    if (score > bestScore) {
      bestScore = score
      bestIndex = i
    }
  }

  // 如果没有找到好的匹配，尝试关键词匹配
  if (bestIndex === -1) {
    const chartKeywords = chartTitle.toLowerCase().split(/[,，、\s]+/).filter(k => k.length > 1)
    for (let i = 0; i < sectionTitles.length; i++) {
      const sectionLower = sectionTitles[i].toLowerCase()
      for (const keyword of chartKeywords) {
        if (sectionLower.includes(keyword)) {
          return i
        }
      }
    }
  }

  return bestIndex
}

// 解析内容，将图片占位符替换为图表
function parseContentWithCharts(
  content: string,
  charts: ChartData[],
  knowledgeGraph?: KnowledgeGraphData
): ContentBlock[] {
  const blocks: ContentBlock[] = []
  const usedCharts = new Set<string>()

  // 第一步：处理图片占位符
  // 匹配 Markdown 图片语法: ![alt](url) 或 ![alt]()
  const imageRegex = /!\[([^\]]*)\]\([^)]*\)/g

  let lastIndex = 0
  let match
  let graphInserted = false
  let firstH2Passed = false

  while ((match = imageRegex.exec(content)) !== null) {
    const altText = match[1]
    const matchIndex = match.index

    // 添加图片之前的文本
    if (matchIndex > lastIndex) {
      const textBefore = content.slice(lastIndex, matchIndex)
      if (textBefore.trim()) {
        blocks.push({ type: 'markdown', content: textBefore })
      }

      // 在第一个章节后插入知识图谱（如果有）
      if (!graphInserted && knowledgeGraph && knowledgeGraph.nodes.length > 0) {
        const h2Count = (textBefore.match(/^## /gm) || []).length
        if (h2Count >= 1) {
          blocks.push({ type: 'knowledgeGraph', data: knowledgeGraph })
          graphInserted = true
          firstH2Passed = true
        }
      }
    }

    // 尝试匹配图表
    const matchedChart = findMatchingChart(altText, charts.filter(c => !usedCharts.has(c.id)))
    if (matchedChart) {
      blocks.push({ type: 'chart', chart: matchedChart })
      usedCharts.add(matchedChart.id)
    }

    lastIndex = matchIndex + match[0].length
  }

  // 添加剩余的文本
  if (lastIndex < content.length) {
    const remaining = content.slice(lastIndex)
    if (remaining.trim()) {
      blocks.push({ type: 'markdown', content: remaining })
    }
  }

  // 第二步：如果有未使用的图表，尝试根据章节标题匹配并插入
  let unusedCharts = charts.filter(c => !usedCharts.has(c.id))

  if (unusedCharts.length > 0) {
    // 提取所有章节标题及其在 blocks 中的位置
    const sectionPositions: { title: string; blockIndex: number }[] = []

    blocks.forEach((block, blockIndex) => {
      if (block.type === 'markdown') {
        // 为每个 block 创建新的 regex 以避免状态问题
        const sectionRegex = /^(#{2,3})\s+(.+)$/gm
        let sectionMatch
        while ((sectionMatch = sectionRegex.exec(block.content)) !== null) {
          sectionPositions.push({
            title: sectionMatch[2].trim(),
            blockIndex,
          })
        }
      }
    })

    // 为每个未使用的图表找到最佳插入位置
    const chartInsertions: { chart: ChartData; afterBlockIndex: number }[] = []

    for (const chart of unusedCharts) {
      const bestSectionIdx = findBestSectionForChart(
        chart.title,
        sectionPositions.map(s => s.title)
      )
      if (bestSectionIdx >= 0) {
        chartInsertions.push({
          chart,
          afterBlockIndex: sectionPositions[bestSectionIdx].blockIndex,
        })
        usedCharts.add(chart.id)
      }
    }

    // 按 blockIndex 降序排序，从后往前插入以保持索引正确
    chartInsertions.sort((a, b) => b.afterBlockIndex - a.afterBlockIndex)

    for (const insertion of chartInsertions) {
      // 在匹配的章节 block 之后插入图表
      blocks.splice(insertion.afterBlockIndex + 1, 0, { type: 'chart', chart: insertion.chart })
    }
  }

  // 第三步：处理知识图谱 - 在执行摘要后或第一个主要章节后插入
  if (!graphInserted && knowledgeGraph && knowledgeGraph.nodes.length > 0 && blocks.length > 0) {
    let insertAfterIdx = -1

    // 优先查找"执行摘要"或"摘要"章节之后
    for (let i = 0; i < blocks.length; i++) {
      const block = blocks[i]
      if (block.type === 'markdown') {
        if (/^##\s*(执行摘要|摘要|概述|研究背景)/m.test(block.content)) {
          insertAfterIdx = i
          break
        }
      }
    }

    // 如果没找到摘要，找第一个编号章节（如 "## 1 xxx"）
    if (insertAfterIdx === -1) {
      for (let i = 0; i < blocks.length; i++) {
        const block = blocks[i]
        if (block.type === 'markdown' && /^##\s+\d+/m.test(block.content)) {
          insertAfterIdx = i
          break
        }
      }
    }

    // 还没找到就用第一个 h2
    if (insertAfterIdx === -1) {
      for (let i = 0; i < blocks.length; i++) {
        const block = blocks[i]
        if (block.type === 'markdown' && /^## /m.test(block.content)) {
          insertAfterIdx = i
          break
        }
      }
    }

    // 插入知识图谱
    if (insertAfterIdx >= 0) {
      blocks.splice(insertAfterIdx + 1, 0, { type: 'knowledgeGraph', data: knowledgeGraph })
      graphInserted = true
    }
  }

  // 第四步：处理仍未使用的图表 - 均匀分布到各章节中，而不是全部放到末尾
  unusedCharts = charts.filter(c => !usedCharts.has(c.id))
  if (unusedCharts.length > 0) {
    // 找到所有章节标题的位置（markdown blocks 中包含 ## 的）
    const sectionBlockIndices: number[] = []
    blocks.forEach((block, idx) => {
      if (block.type === 'markdown' && /^##\s+\d/m.test(block.content)) {
        sectionBlockIndices.push(idx)
      }
    })

    if (sectionBlockIndices.length > 0) {
      // 均匀分配图表到各章节
      const chartsPerSection = Math.ceil(unusedCharts.length / sectionBlockIndices.length)
      let chartIdx = 0

      // 从后往前插入，避免索引偏移问题
      for (let i = sectionBlockIndices.length - 1; i >= 0 && chartIdx < unusedCharts.length; i--) {
        const insertPos = sectionBlockIndices[i] + 1
        const chartsToInsert = unusedCharts.slice(chartIdx, Math.min(chartIdx + chartsPerSection, unusedCharts.length))

        // 反向插入这批图表
        for (let j = chartsToInsert.length - 1; j >= 0; j--) {
          blocks.splice(insertPos, 0, { type: 'chart', chart: chartsToInsert[j] })
        }
        chartIdx += chartsToInsert.length
      }
    } else {
      // 没有找到章节，放在参考文献之前（或末尾）
      let refIndex = blocks.length
      for (let i = blocks.length - 1; i >= 0; i--) {
        const block = blocks[i]
        if (block.type === 'markdown' && /^##\s*(参考文献|参考资料|References)/m.test(block.content)) {
          refIndex = i
          break
        }
      }
      // 在参考文献之前插入图表
      for (const chart of unusedCharts) {
        blocks.splice(refIndex, 0, { type: 'chart', chart })
        refIndex++ // 保持插入顺序
      }
    }
  }

  return blocks
}

// 简化的知识图谱组件（内联显示）
function InlineKnowledgeGraph({ data }: { data: KnowledgeGraphData }) {
  if (!data || !data.nodes || data.nodes.length === 0) return null

  // 按类型分组节点
  const nodesByType: Record<string, string[]> = {}
  data.nodes.forEach(node => {
    const type = node.type || 'other'
    if (!nodesByType[type]) nodesByType[type] = []
    nodesByType[type].push(node.name)
  })

  const typeLabels: Record<string, string> = {
    core: '核心概念',
    tech: '技术/方法',
    company: '企业/机构',
    policy: '政策/法规',
    product: '产品/服务',
    person: '人物',
    other: '其他',
  }

  return (
    <div className={styles.inlineGraph}>
      <div className={styles.graphTitle}>🔗 知识图谱</div>
      <div className={styles.graphContent}>
        {Object.entries(nodesByType).map(([type, names]) => (
          <div key={type} className={styles.graphCategory}>
            <span className={styles.categoryLabel}>{typeLabels[type] || type}:</span>
            <span className={styles.categoryItems}>
              {names.slice(0, 8).join('、')}
              {names.length > 8 && ` 等${names.length}项`}
            </span>
          </div>
        ))}
        {data.edges && data.edges.length > 0 && (
          <div className={styles.graphStats}>
            共 {data.nodes.length} 个实体，{data.edges.length} 个关系
          </div>
        )}
      </div>
    </div>
  )
}

export default function ProcessReport({ content, sections, charts, knowledgeGraph }: ProcessReportProps) {
  const [activeView, setActiveView] = useState<'sections' | 'final'>('final')

  const hasSections = sections && sections.length > 0
  const hasContent = !!content

  // 解析内容块（将图表插入到合适位置）
  const contentBlocks = useMemo(() => {
    if (!content) return []
    return parseContentWithCharts(content, charts || [], knowledgeGraph)
  }, [content, charts, knowledgeGraph])

  if (!hasSections && !hasContent) {
    return (
      <div className={styles.emptyState}>
        <div className={styles.emptyIcon}>
          <svg viewBox="0 0 24 24" width="48" height="48" fill="none" stroke="currentColor" strokeWidth="1.5">
            <path d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
        </div>
        <div className={styles.emptyText}>写作阶段开始后将在此显示报告内容</div>
      </div>
    )
  }

  return (
    <div className={styles.container}>
      {/* 切换按钮 */}
      {(hasSections || hasContent) && (
        <div className={styles.viewSwitch}>
          <button
            className={`${styles.switchBtn} ${activeView === 'sections' ? styles.active : ''}`}
            onClick={() => setActiveView('sections')}
            disabled={!hasSections}
          >
            章节草稿 {hasSections && <span className={styles.count}>{sections.length}</span>}
          </button>
          <button
            className={`${styles.switchBtn} ${activeView === 'final' ? styles.active : ''}`}
            onClick={() => setActiveView('final')}
            disabled={!hasContent}
          >
            最终报告
          </button>
        </div>
      )}

      {/* 内容区 */}
      <div className={styles.contentArea}>
        {activeView === 'sections' && hasSections ? (
          <div className={styles.sectionsView}>
            {sections.map((section, index) => (
              <div key={section.id} className={styles.sectionCard}>
                <div className={styles.sectionHeader}>
                  <span className={styles.sectionIndex}>{index + 1}</span>
                  <span className={styles.sectionTitle}>{section.title}</span>
                  {section.wordCount && (
                    <span className={styles.wordCount}>{section.wordCount} 字</span>
                  )}
                </div>
                <div className={styles.sectionContent}>
                  <Markdown value={section.content} />
                </div>
              </div>
            ))}
          </div>
        ) : hasContent ? (
          <div className={styles.finalReport}>
            {contentBlocks.map((block, index) => {
              if (block.type === 'markdown') {
                return <Markdown key={index} value={block.content} />
              }
              if (block.type === 'chart') {
                return <ChartRenderer key={index} chart={block.chart} inline />
              }
              if (block.type === 'knowledgeGraph') {
                return <InlineKnowledgeGraph key={index} data={block.data} />
              }
              return null
            })}
          </div>
        ) : (
          <div className={styles.emptyState}>
            <div className={styles.emptyText}>
              {activeView === 'sections' ? '暂无章节草稿' : '报告生成中...'}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
