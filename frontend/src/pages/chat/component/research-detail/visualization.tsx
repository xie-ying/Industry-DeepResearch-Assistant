import { BarChartOutlined, PictureOutlined } from '@ant-design/icons'
import ReactECharts from 'echarts-for-react'
import styles from './visualization.module.scss'

interface ChartConfig {
  id: string
  title: string
  subtitle?: string
  type: 'line' | 'bar' | 'pie' | 'horizontal_bar' | 'radar' | 'sankey' | 'wordcloud' | 'graph'
  echarts_option?: Record<string, unknown>
  image_base64?: string  // 支持 matplotlib 生成的图片
}

interface VisualizationProps {
  charts?: ChartConfig[]
}

export default function Visualization({ charts }: VisualizationProps) {
  console.log(`[Visualization] 渲染，charts 数量: ${charts?.length || 0}`)
  if (charts?.length) {
    charts.forEach((c, i) => {
      console.log(`[Visualization] 图表 ${i+1}: id=${c.id}, title=${c.title}, type=${c.type}, has_echarts=${!!c.echarts_option}, has_image=${!!c.image_base64}`)
    })
  }

  if (!charts?.length) {
    console.log(`[Visualization] 无图表数据，显示空状态`)
    return (
      <div className={styles.empty}>
        <BarChartOutlined className={styles.emptyIcon} />
        <span>暂无可视化图表</span>
      </div>
    )
  }

  return (
    <div className={styles.grid}>
      {charts.map((chart) => (
        <div key={chart.id} className={styles.card}>
          <div className={styles.cardHeader}>
            <h3 className={styles.cardTitle}>{chart.title}</h3>
            {chart.subtitle && <p className={styles.cardSubtitle}>{chart.subtitle}</p>}
          </div>
          <div className={styles.chartContainer}>
            {chart.image_base64 ? (
              // 渲染 matplotlib 生成的 base64 图片
              <div className={styles.imageWrapper}>
                <img
                  src={`data:image/png;base64,${chart.image_base64}`}
                  alt={chart.title}
                  className={styles.chartImage}
                />
              </div>
            ) : chart.echarts_option ? (
              // 渲染 ECharts 图表
              <ReactECharts
                option={chart.echarts_option}
                style={{ height: '100%', width: '100%' }}
                opts={{ renderer: 'canvas' }}
              />
            ) : (
              // 无数据占位
              <div className={styles.noData}>
                <PictureOutlined />
                <span>图表数据加载中...</span>
              </div>
            )}
          </div>
        </div>
      ))}
    </div>
  )
}
