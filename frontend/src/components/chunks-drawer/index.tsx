import { useState, useEffect } from 'react'
import { Drawer, Spin, Empty, Tag, Typography, message } from 'antd'
import { FileTextOutlined } from '@ant-design/icons'
import * as knowledgeApi from '@/api/knowledge'
import type { ChunkInfo } from '@/api/knowledge'
import styles from './index.module.scss'

const { Text, Paragraph } = Typography

interface ChunksDrawerProps {
  open: boolean
  kbId: string
  docId: string
  filename: string
  onClose: () => void
}

export default function ChunksDrawer({
  open,
  kbId,
  docId,
  filename,
  onClose,
}: ChunksDrawerProps) {
  const [loading, setLoading] = useState(false)
  const [chunks, setChunks] = useState<ChunkInfo[]>([])
  const [totalCount, setTotalCount] = useState(0)

  useEffect(() => {
    if (open && kbId && docId) {
      fetchChunks()
    }
  }, [open, kbId, docId])

  const fetchChunks = async () => {
    setLoading(true)
    try {
      const res = await knowledgeApi.getDocumentChunks(kbId, docId)
      setChunks(res.data.chunks)
      setTotalCount(res.data.chunk_count)
    } catch (error: any) {
      message.error(error?.response?.data?.detail || '获取切片失败')
      setChunks([])
    } finally {
      setLoading(false)
    }
  }

  const handleClose = () => {
    setChunks([])
    setTotalCount(0)
    onClose()
  }

  return (
    <Drawer
      title={
        <div className={styles.title}>
          <FileTextOutlined />
          <span className={styles.filename}>{filename}</span>
          <Tag color="blue">{totalCount} 个切片</Tag>
        </div>
      }
      placement="right"
      width={600}
      open={open}
      onClose={handleClose}
      className={styles.drawer}
    >
      {loading ? (
        <div className={styles.loading}>
          <Spin size="large" />
          <Text type="secondary">加载切片中...</Text>
        </div>
      ) : chunks.length === 0 ? (
        <Empty description="暂无切片数据" />
      ) : (
        <div className={styles.chunkList}>
          {chunks.map((chunk, index) => (
            <div key={chunk.index} className={styles.chunkItem}>
              <div className={styles.chunkHeader}>
                <Tag color="purple">#{chunk.index + 1}</Tag>
                <Text type="secondary" className={styles.charCount}>
                  {chunk.content.length} 字符
                </Text>
              </div>
              <Paragraph
                className={styles.chunkContent}
                ellipsis={{ rows: 6, expandable: true, symbol: '展开' }}
              >
                {chunk.content}
              </Paragraph>
            </div>
          ))}
        </div>
      )}
    </Drawer>
  )
}
