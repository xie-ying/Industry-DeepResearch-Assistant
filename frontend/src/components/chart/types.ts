/**
 * Chart Types - 图表类型定义
 */

// 图表类型枚举
export type ChartType = 'line' | 'bar' | 'pie' | 'scatter' | 'table'

// 系列数据
export interface SeriesData {
  name: string
  data: (number | { name: string; value: number })[]
}

// 图表数据
export interface ChartData {
  xAxis?: string[]
  series?: SeriesData[]
}

// ECharts 配置选项
export interface EChartsOption {
  title?: {
    text?: string
    subtext?: string
    left?: string
  }
  tooltip?: {
    trigger?: string
    axisPointer?: {
      type?: string
    }
    formatter?: string
  }
  legend?: {
    data?: string[]
    bottom?: number | string
    orient?: string
    left?: string
    top?: string
  }
  grid?: {
    left?: string
    right?: string
    bottom?: string
    containLabel?: boolean
  }
  xAxis?: {
    type?: string
    data?: string[]
    boundaryGap?: boolean
    name?: string
  }
  yAxis?: {
    type?: string
    name?: string
  }
  series?: Array<{
    name?: string
    type?: string
    data?: (number | { name: string; value: number })[]
    smooth?: boolean
    areaStyle?: { opacity?: number }
    emphasis?: { focus?: string; itemStyle?: Record<string, unknown> }
    itemStyle?: { borderRadius?: number[] }
    stack?: string
    radius?: string | string[]
    roseType?: string
    label?: { formatter?: string }
    symbolSize?: number
  }>
  color?: string[]
}

// 图表配置
export interface ChartConfig {
  type: ChartType
  title: string
  data?: ChartData
  echarts_option?: EChartsOption
  columns?: Array<{ key: string; label: string }>
  pagination?: boolean
  pageSize?: number
}

// 数据洞察
export interface DataInsight {
  insights: string[]
  statistics?: Record<string, unknown>
  visualization_hint?: ChartType
}
