import ComSpinner from '@/components/spin/spinner'
import { ChatRole } from '@/configs'
import classNames from 'classnames'
import styles from './chat-message.module.scss'
import { Result } from './result'

function UserMessage(props: { item: API.ChatItem }) {
  const { item } = props

  return (
    <div className={classNames(styles['chat-message-item--user'])}>
      {item.content}
    </div>
  )
}

function AssistantMessage(props: {
  item: API.ChatItem
  isEnd?: boolean
  onSend?: (text: string) => void
  onOpenCiations?: () => void
  onStepClick?: (stepId: string) => void
}) {
  const { item, isEnd, onSend, onStepClick } = props

  return (
    <div
      className={classNames(
        styles['chat-message-item'],
        styles['chat-message-item--assistant'],
      )}
    >
      <Result item={item} isEnd={isEnd} onSend={onSend} onStepClick={onStepClick} />

      {item.loading ? <ComSpinner /> : null}
    </div>
  )
}

export default function ChatMessage(props: {
  list: API.ChatItem[]
  onSend?: (text: string) => void
  onOpenCiations?: (item: API.ChatItem) => void
  onStepClick?: (stepId: string) => void
}) {
  const { list, onSend, onOpenCiations, onStepClick } = props

  return (
    <div className={styles['chat-message']}>
      {list.map((item, index) => {
        if (item.role === ChatRole.User) {
          return <UserMessage key={item.id} item={item} />
        }

        return (
          <AssistantMessage
            key={item.id}
            item={item}
            isEnd={list.length - 1 === index}
            onSend={onSend}
            onOpenCiations={() => onOpenCiations?.(item)}
            onStepClick={onStepClick}
          />
        )
      })}
    </div>
  )
}
