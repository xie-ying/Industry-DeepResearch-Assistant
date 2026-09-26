declare namespace API {
  interface ChatItem {
    id: number
    role: import('@/configs').ChatRole
    type: import('@/configs').ChatType
    loading?: boolean
    error?: string
    content?: string
    think?: string

    documents?: Document[]
    reference?: Reference[]
    image_results?: {
      images?: {
        title: string
        imageUrl: string
        thumbnailUrl: string
        source: string
        link: string
        googleUrl: string
      }[]
    }
    thinks?: {
      id: string
      type: 'status' | 'search_results'
      results?: {
        id: string
        count?: number
        content?: string
      }[]
    }[]
    search_results?: {
      id: string
      subquery: string
      url: string
      name: string
      summary: string
      snippet: string
      siteName: string
      siteIcon: string
      host: string
    }[]

    // ReAct 相关字段
    reactMode?: boolean
    reactSteps?: ReactStep[]
    researchPlan?: ResearchPlan  // 研究计划
    charts?: ChartConfig[]
    insights?: string[]
    stockQuote?: StockQuoteData  // 股票实时行情
  }

  // 股票行情数据
  interface StockQuoteData {
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

  // 研究计划
  interface ResearchPlan {
    understanding: string
    strategy: string
    subQueries: SubQuery[]
    expectedAspects: string[]
  }

  // 子查询
  interface SubQuery {
    query: string
    purpose: string
    tool: string
  }

  // ReAct 步骤
  interface ReactStep {
    step: number
    type: 'thought' | 'action' | 'observation' | 'plan'
    content: string
    tool?: string
    params?: Record<string, unknown>
    queries?: string[]  // 并行搜索的查询列表
    success?: boolean
    timestamp?: number
    stepId?: string  // 步骤ID，用于关联详情面板
  }

  // 图表配置
  interface ChartConfig {
    type: 'line' | 'bar' | 'pie' | 'scatter' | 'table'
    title: string
    echarts_option?: Record<string, unknown>
    data?: unknown
  }

  interface Document {
    document_id: string
    document_name: string
    preview: string
  }

  interface Reference {
    id: number
    title: string
    link: string
    content: string
    source: 'web' | 'knowledge'
  }
}
