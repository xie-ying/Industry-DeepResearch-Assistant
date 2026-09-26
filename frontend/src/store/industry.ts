/**
 * 全局行业状态管理
 */
import { proxy, subscribe } from 'valtio'

// 行业配置类型
export interface IndustryConfig {
  id: string
  name: string
  description: string
  // 资讯搜索关键词
  newsKeywords: string[]
  // 招投标搜索关键词
  biddingKeywords: string[]
  // 研究相关关键词
  researchKeywords: string[]
}

// 预定义的行业配置
export const INDUSTRY_CONFIGS: IndustryConfig[] = [
  {
    id: 'smart_transportation',
    name: '智慧交通',
    description: '智能交通系统、车路协同、自动驾驶等领域',
    newsKeywords: [
      '智慧交通 政策',
      '智慧交通 市场',
      '交通运输部 通知',
      '智能网联汽车',
      '自动驾驶 政策',
      '新能源汽车 政策',
      '交通大数据',
      '车路协同',
    ],
    biddingKeywords: [
      '智慧交通',
      '智能交通',
      '交通信息化',
      '车路协同',
      '自动驾驶',
      '智能网联',
    ],
    researchKeywords: ['智慧交通', '智能交通', '车路协同', '自动驾驶'],
  },
  {
    id: 'finance',
    name: '金融科技',
    description: '银行、保险、证券、支付等金融领域',
    newsKeywords: [
      '金融科技 政策',
      '数字人民币',
      '银行数字化转型',
      '保险科技',
      '证券 金融科技',
      '支付 监管',
      '金融大数据',
      '智能风控',
    ],
    biddingKeywords: [
      '银行信息化',
      '金融科技',
      '核心银行系统',
      '保险系统',
      '证券交易系统',
      '支付系统',
    ],
    researchKeywords: ['金融科技', '数字金融', '银行数字化', '智能风控'],
  },
  {
    id: 'healthcare',
    name: '医疗健康',
    description: '医疗信息化、智慧医院、医药研发等领域',
    newsKeywords: [
      '医疗信息化 政策',
      '智慧医院',
      '医保 政策',
      '药品集采',
      '医疗大数据',
      '互联网医疗',
      'AI医疗',
      '医药研发',
    ],
    biddingKeywords: [
      '医院信息化',
      '智慧医疗',
      'HIS系统',
      '医疗设备',
      '医药采购',
      '医保系统',
    ],
    researchKeywords: ['医疗信息化', '智慧医疗', '医药研发', '互联网医疗'],
  },
  {
    id: 'energy',
    name: '能源电力',
    description: '新能源、电力系统、储能等领域',
    newsKeywords: [
      '新能源 政策',
      '碳中和',
      '光伏 市场',
      '风电 政策',
      '储能 市场',
      '电力市场化',
      '智能电网',
      '充电桩',
    ],
    biddingKeywords: [
      '新能源项目',
      '光伏电站',
      '风电项目',
      '储能系统',
      '智能电网',
      '充电设施',
    ],
    researchKeywords: ['新能源', '碳中和', '储能', '智能电网'],
  },
]

// 行业状态
export interface IndustryState {
  currentIndustryId: string
  industries: IndustryConfig[]
}

// 从 localStorage 读取
const getStoredIndustryId = (): string => {
  if (typeof window !== 'undefined') {
    const stored = localStorage.getItem('selected_industry_id')
    console.log('[industry store] 从 localStorage 读取行业:', stored)
    return stored || 'smart_transportation'
  }
  return 'smart_transportation'
}

// 创建状态
export const industryState = proxy<IndustryState>({
  currentIndustryId: getStoredIndustryId(),
  industries: INDUSTRY_CONFIGS,
})

// 订阅变化，保存到 localStorage
subscribe(industryState, () => {
  if (typeof window !== 'undefined') {
    console.log('[industry store] 保存行业到 localStorage:', industryState.currentIndustryId)
    localStorage.setItem('selected_industry_id', industryState.currentIndustryId)
  }
})

// 获取当前行业配置
export const getCurrentIndustry = (): IndustryConfig => {
  const industry = industryState.industries.find(
    (i) => i.id === industryState.currentIndustryId
  )
  console.log('[industry store] 获取当前行业:', industry?.name)
  return industry || INDUSTRY_CONFIGS[0]
}

// 切换行业
export const setCurrentIndustry = (industryId: string) => {
  console.log('[industry store] 切换行业:', industryId)
  industryState.currentIndustryId = industryId
}

// 获取行业列表（用于选择器）
export const getIndustryOptions = () => {
  return industryState.industries.map((i) => ({
    value: i.id,
    label: i.name,
    description: i.description,
  }))
}
