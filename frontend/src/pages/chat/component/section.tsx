import { UpOutlined } from '@ant-design/icons'
import { Collapse } from 'antd'
import styles from './section.module.scss'

export default function Section(props: {
  title: string
  icon?: string
  children?: React.ReactNode
  defaultOpen?: boolean
}) {
  const { title, icon, children, defaultOpen } = props

  return (
    <Collapse
      className={styles['section']}
      bordered={false}
      ghost
      defaultActiveKey={defaultOpen ? '1' : undefined}
    >
      <Collapse.Panel
        header={
          <div className={styles['section-header']}>
            {icon ? (
              <div className={styles['section-header__icon']}>
                <img src={icon} />{' '}
              </div>
            ) : null}

            <div className={styles['section-header__title']}>{title}</div>
            <div className={styles['section-header__arrow']}>
              <UpOutlined />
            </div>
          </div>
        }
        key="1"
        showArrow={false}
      >
        {children}
      </Collapse.Panel>
    </Collapse>
  )
}
