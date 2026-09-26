import { request } from './request'

export interface Memory {
  id: string
  session_id?: string
  summary: string
  key_insights?: Record<string, unknown>
  token_count?: number
  created_at: string
}

export interface MemoryListResponse {
  memories: Memory[]
  total: number
}

export interface MemorySearchResult {
  id: string
  session_id?: string
  memory_type: string
  content: string
  score: number
}

/**
 * 获取记忆列表
 */
export function getMemories(params?: { limit?: number; offset?: number }) {
  return request.get<MemoryListResponse>('/memories', { params })
}

/**
 * 获取单个记忆详情
 */
export function getMemory(memoryId: string) {
  return request.get<Memory>(`/memories/${memoryId}`)
}

/**
 * 搜索记忆
 */
export function searchMemories(params: { query: string; top_k?: number }) {
  return request.post<MemorySearchResult[]>('/memories/search', params)
}

/**
 * 从会话创建记忆
 */
export function createMemory(sessionId: string) {
  return request.post<Memory>('/memories/create', { session_id: sessionId })
}

/**
 * 删除记忆
 */
export function deleteMemory(memoryId: string) {
  return request.delete(`/memories/${memoryId}`)
}

/**
 * 获取记忆上下文
 */
export function getMemoryContext(query: string) {
  return request.get<{ context: string }>(`/memories/context/${encodeURIComponent(query)}`)
}
