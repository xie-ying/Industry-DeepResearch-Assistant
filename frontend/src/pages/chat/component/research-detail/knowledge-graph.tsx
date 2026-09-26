import { ShareAltOutlined } from '@ant-design/icons'
import ReactECharts from 'echarts-for-react'
import styles from './knowledge-graph.module.scss'

interface GraphNode {
  id: string
  name: string
  type: 'core' | 'tech' | 'company' | 'policy' | 'product' | 'person'
  size?: number
  importance?: number
}

interface GraphEdge {
  source: string
  target: string
  relation: string
}

interface KnowledgeGraphData {
  nodes: GraphNode[]
  edges: GraphEdge[]
  stats?: {
    entitiesCount: number
    relationsCount: number
  }
}

interface KnowledgeGraphProps {
  data?: KnowledgeGraphData
}

const typeConfig: Record<string, { color: string; label: string }> = {
  core: { color: '#1677ff', label: '核心' },
  tech: { color: '#722ed1', label: '技术' },
  company: { color: '#52c41a', label: '企业' },
  policy: { color: '#fa8c16', label: '政策' },
  product: { color: '#eb2f96', label: '产品' },
  person: { color: '#13c2c2', label: '人物' },
}

export default function KnowledgeGraph({ data }: KnowledgeGraphProps) {
  if (!data?.nodes?.length) {
    return (
      <div className={styles.empty}>
        <ShareAltOutlined className={styles.emptyIcon} />
        <span>暂无知识图谱数据</span>
      </div>
    )
  }

  // 获取使用的类型
  const usedTypes = [...new Set(data.nodes.map(n => n.type))]

  // ECharts 配置
  const option = {
    tooltip: {
      trigger: 'item',
      formatter: (params: any) => {
        if (params.dataType === 'node') {
          const typeLabel = typeConfig[params.data.nodeType]?.label || params.data.nodeType
          return `<strong>${params.data.name}</strong><br/>类型: ${typeLabel}`
        }
        if (params.dataType === 'edge') {
          return `${params.data.source} → ${params.data.target}<br/>关系: ${params.data.relation || '-'}`
        }
        return ''
      },
    },
    legend: {
      show: true,
      orient: 'horizontal',
      right: 20,
      top: 20,
      itemWidth: 10,
      itemHeight: 10,
      itemGap: 16,
      textStyle: {
        fontSize: 12,
        color: '#595959',
      },
      data: usedTypes.map(type => ({
        name: typeConfig[type]?.label || type,
        icon: 'circle',
      })),
    },
    series: [
      {
        type: 'graph',
        layout: 'force',
        roam: true,
        draggable: true,
        zoom: 0.9,
        force: {
          repulsion: 400,
          edgeLength: [80, 180],
          gravity: 0.1,
        },
        categories: usedTypes.map(type => ({
          name: typeConfig[type]?.label || type,
          itemStyle: { color: typeConfig[type]?.color || '#1677ff' },
        })),
        data: data.nodes.map(node => ({
          id: node.id,
          name: node.name,
          symbolSize: node.size || 30 + (node.importance || 5) * 2,
          category: usedTypes.indexOf(node.type),
          nodeType: node.type,
          itemStyle: {
            color: typeConfig[node.type]?.color || '#1677ff',
            shadowBlur: 10,
            shadowColor: 'rgba(0, 0, 0, 0.1)',
          },
          label: {
            show: true,
            fontSize: 12,
            color: '#262626',
            position: 'bottom',
            distance: 5,
          },
        })),
        edges: data.edges.map(edge => ({
          source: edge.source,
          target: edge.target,
          relation: edge.relation,
          lineStyle: {
            color: '#d9d9d9',
            width: 1.5,
            curveness: 0.2,
          },
          label: {
            show: true,
            formatter: edge.relation,
            fontSize: 10,
            color: '#8c8c8c',
          },
        })),
        emphasis: {
          focus: 'adjacency',
          lineStyle: {
            width: 3,
          },
        },
      },
    ],
  }

  return (
    <div className={styles.graph}>
      <div className={styles.stats}>
        知识图谱 · {data.stats?.entitiesCount || data.nodes.length} 个实体 · {data.stats?.relationsCount || data.edges.length} 条关系
      </div>
      <div className={styles.chartContainer}>
        <ReactECharts
          option={option}
          style={{ height: '100%', width: '100%' }}
          opts={{ renderer: 'canvas' }}
        />
      </div>
    </div>
  )
}
