import { request } from './request'

// 资讯类型定义
export interface NewsItem {
  id: string
  title: string
  content: string
  source: string
  source_url: string
  category: string
  department: string
  publish_time: string
  collected_at: string
  keywords: string
  is_read: boolean
  created_at: string
}

export interface BiddingItem {
  id: string
  bid_id: string
  title: string
  notice_type: string
  province: string
  city: string
  content: string
  publish_time: string
  source: string
  collected_at: string
  is_read: boolean
  created_at: string
}

export interface NewsStats {
  total: number
  recent_24h: number
  by_category: Record<string, number>
}

export interface BiddingStats {
  total: number
  by_type: Record<string, number>
  by_province: Record<string, number>
}

export interface NewsListResponse {
  success: boolean
  data: NewsItem[]
  total: number
  stats: NewsStats
}

export interface BiddingListResponse {
  success: boolean
  data: BiddingItem[]
  total: number
  stats: BiddingStats
}

export interface CollectionResponse {
  success: boolean
  message: string
  news_collected: number
  bidding_collected: number
  errors: string[]
}

// 获取行业资讯列表
export const getNewsList = async (params?: {
  category?: string
  industry_id?: string
  limit?: number
  offset?: number
}): Promise<NewsListResponse> => {
  // loading: false 禁用全局 loading，使用页面的骨架屏
  const res = await request.get<NewsListResponse>('/news/list', { params, loading: false })
  return res.data
}

// 获取招投标列表
export const getBiddingList = async (params?: {
  notice_type?: string
  province?: string
  industry_id?: string
  limit?: number
  offset?: number
}): Promise<BiddingListResponse> => {
  // loading: false 禁用全局 loading，使用页面的骨架屏
  const res = await request.get<BiddingListResponse>('/news/bidding/list', { params, loading: false })
  return res.data
}

// 获取所有统计
export const getStats = async () => {
  console.log('[API] getStats 请求')
  const res = await request.get<{
    success: boolean
    news: NewsStats
    bidding: BiddingStats
  }>('/news/stats')
  console.log('[API] getStats 响应:', res.data)
  return res.data
}

// 手动触发采集
export const triggerCollection = async (params?: {
  max_news?: number
  max_bidding?: number
  industry_id?: string
}): Promise<CollectionResponse> => {
  // loading: false 禁用全局 loading，按钮已有自己的 loading 状态
  // cancelRepeat: false 禁用取消重复请求（采集是长时间操作）
  // timeout: 120000 设置2分钟超时（采集需要较长时间）
  const res = await request.post<CollectionResponse>('/news/collect', null, {
    params,
    loading: false,
    cancelRepeat: false,
    timeout: 120000,
  })
  return res.data
}

// 获取行业列表
export const getIndustries = async () => {
  console.log('[API] getIndustries 请求')
  const res = await request.get<{
    success: boolean
    industries: Array<{
      id: string
      name: string
      description: string
    }>
  }>('/news/industries')
  console.log('[API] getIndustries 响应:', res.data)
  return res.data
}

// 获取单个行业配置
export const getIndustry = async (industryId: string) => {
  console.log('[API] getIndustry 请求:', industryId)
  const res = await request.get<{
    success: boolean
    industry: {
      id: string
      name: string
      description: string
      news_keywords: string[]
      bidding_keywords: string[]
    }
  }>(`/news/industries/${industryId}`)
  console.log('[API] getIndustry 响应:', res.data)
  return res.data
}

// 检查数据状态
export const checkDataStatus = async () => {
  const res = await request.get<{
    success: boolean
    has_data: boolean
    news_count: number
    bidding_count: number
    news_recent_24h: number
  }>('/news/check')
  return res.data
}

// 获取定时任务状态
export const getSchedulerStatus = async () => {
  const res = await request.get<{
    success: boolean
    jobs: Array<{
      id: string
      name: string
      next_run_time: string
      trigger: string
    }>
  }>('/news/scheduler/status')
  return res.data
}
