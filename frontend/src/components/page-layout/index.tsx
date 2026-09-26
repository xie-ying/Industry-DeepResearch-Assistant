import classNames from 'classnames'
import { PropsWithChildren, ReactNode } from 'react'
import './index.scss'

export default function ComPageLayout(
  props: PropsWithChildren<{
    className?: string
    right?: ReactNode
    sender?: ReactNode
    wideRight?: boolean  // 宽右侧面板模式（1/3 左 + 2/3 右）
  }>,
) {
  const { children, className, right, sender, wideRight, ...rest } = props
  return (
    <div className={classNames('com-page-layout', className, { 'wide-right-mode': wideRight })} {...rest}>
      <div className="com-page-layout__main">
        <div className="com-page-layout__main-content">{children}</div>

        <div className="com-page-layout__sender">{sender}</div>
      </div>
      {right ? <div className="com-page-layout__right">{right}</div> : null}
    </div>
  )
}
