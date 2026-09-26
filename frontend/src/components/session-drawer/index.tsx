import { useEffect, useState } from 'react'
import { Drawer, List, Spin, Empty, Button, Popconfirm, Input, Typography, message } from 'antd'
import { DeleteOutlined, EditOutlined, MessageOutlined, CheckOutlined, CloseOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { useSnapshot } from 'valtio'
import { sessionState, sessionActions } from '@/store/session'
import { authState } from '@/store/auth'
import { Session } from '@/api/session'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import 'dayjs/locale/zh-cn'
import './index.scss'

dayjs.extend(relativeTime)
dayjs.locale('zh-cn')

const { Text } = Typography

interface SessionDrawerProps {
  open: boolean
  onClose: () => void
}

export function SessionDrawer({ open, onClose }: SessionDrawerProps) {
  const navigate = useNavigate()
  const { sessions, loading } = useSnapshot(sessionState)
  const { isLoggedIn } = useSnapshot(authState)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [editTitle, setEditTitle] = useState('')

  useEffect(() => {
    if (open && isLoggedIn) {
      sessionActions.fetchSessions()
    }
  }, [open, isLoggedIn])

  const handleSessionClick = async (session: Session) => {
    // 先关闭抽屉，然后导航
    onClose()
    // 预加载会话数据到 store
    try {
      await sessionActions.loadSession(session.id)
    } catch (e) {
      // 即使预加载失败也继续导航，页面会自己重新加载
      console.log('预加载会话失败，继续导航', e)
    }
    navigate(`/chat/${session.id}`)
  }

  const handleDelete = async (sessionId: string, e: React.MouseEvent) => {
    e.stopPropagation()
    try {
      await sessionActions.removeSession(sessionId)
      message.success('删除成功')
    } catch {
      message.error('删除失败')
    }
  }

  const handleStartEdit = (session: Session, e: React.MouseEvent) => {
    e.stopPropagation()
    setEditingId(session.id)
    setEditTitle(session.title)
  }

  const handleSaveEdit = async (sessionId: string, e: React.MouseEvent) => {
    e.stopPropagation()
    if (!editTitle.trim()) {
      message.warning('标题不能为空')
      return
    }
    try {
      await sessionActions.renameSession(sessionId, editTitle.trim())
      message.success('重命名成功')
      setEditingId(null)
    } catch {
      message.error('重命名失败')
    }
  }

  const handleCancelEdit = (e: React.MouseEvent) => {
    e.stopPropagation()
    setEditingId(null)
  }

  if (!isLoggedIn) {
    return (
      <Drawer
        title="对话历史"
        placement="left"
        onClose={onClose}
        open={open}
        width={320}
        className="session-drawer"
      >
        <Empty description="请先登录" />
        <div style={{ textAlign: 'center', marginTop: 16 }}>
          <Button type="primary" onClick={() => navigate('/login')}>
            去登录
          </Button>
        </div>
      </Drawer>
    )
  }

  return (
    <Drawer
      title="对话历史"
      placement="left"
      onClose={onClose}
      open={open}
      width={320}
      className="session-drawer"
    >
      <Spin spinning={loading}>
        {sessions.length === 0 ? (
          <Empty description="暂无对话记录" />
        ) : (
          <List
            dataSource={sessions as Session[]}
            renderItem={(session) => (
              <List.Item
                className="session-item"
                onClick={() => handleSessionClick(session)}
                actions={
                  editingId === session.id
                    ? [
                        <Button
                          key="save"
                          type="text"
                          size="small"
                          icon={<CheckOutlined />}
                          onClick={(e) => handleSaveEdit(session.id, e)}
                        />,
                        <Button
                          key="cancel"
                          type="text"
                          size="small"
                          icon={<CloseOutlined />}
                          onClick={handleCancelEdit}
                        />,
                      ]
                    : [
                        <Button
                          key="edit"
                          type="text"
                          size="small"
                          icon={<EditOutlined />}
                          onClick={(e) => handleStartEdit(session, e)}
                        />,
                        <Popconfirm
                          key="delete"
                          title="确定删除此对话？"
                          onConfirm={(e) => handleDelete(session.id, e as React.MouseEvent)}
                          onCancel={(e) => e?.stopPropagation()}
                        >
                          <Button
                            type="text"
                            size="small"
                            danger
                            icon={<DeleteOutlined />}
                            onClick={(e) => e.stopPropagation()}
                          />
                        </Popconfirm>,
                      ]
                }
              >
                <List.Item.Meta
                  avatar={<MessageOutlined style={{ fontSize: 20, color: '#1890ff' }} />}
                  title={
                    editingId === session.id ? (
                      <Input
                        value={editTitle}
                        onChange={(e) => setEditTitle(e.target.value)}
                        onClick={(e) => e.stopPropagation()}
                        onPressEnter={(e) => handleSaveEdit(session.id, e as unknown as React.MouseEvent)}
                        size="small"
                        autoFocus
                      />
                    ) : (
                      <Text ellipsis={{ tooltip: session.title }}>{session.title}</Text>
                    )
                  }
                  description={
                    <Text type="secondary" style={{ fontSize: 12 }}>
                      {dayjs(session.updated_at).fromNow()} · {session.message_count} 条消息
                    </Text>
                  }
                />
              </List.Item>
            )}
          />
        )}
      </Spin>
    </Drawer>
  )
}
