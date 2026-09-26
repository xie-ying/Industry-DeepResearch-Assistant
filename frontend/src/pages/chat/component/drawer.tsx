import classNames from 'classnames'
import { PropsWithChildren } from 'react'
import styles from './drawer.module.scss'

export default function Drawer(
  props: PropsWithChildren<{
    title?: string
  }>,
) {
  const { title, children } = props

  return (
    <div className={styles['drawer']}>
      <div className={styles['drawer__header']}>
        <div className={styles['drawer__title']}>
          <span>{title}</span>
        </div>
        {/* <Button
          className={styles['drawer__close']}
          type="text"
          shape="circle"
          color="default"
          size="small"
        >
          <CloseOutlined />
        </Button> */}
      </div>

      <div className={classNames(styles['drawer__content'], 'scrollbar-style')}>
        {children}
      </div>
    </div>
  )
}
