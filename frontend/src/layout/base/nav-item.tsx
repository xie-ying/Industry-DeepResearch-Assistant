import classNames from 'classnames'
import { Link } from 'react-router-dom'
import './nav-item.scss'

export function NavItem(props: {
  icon: string
  label: string
  href: string
  active?: boolean
  dot?: boolean
  className?: string
  onClick?: () => void
}) {
  const { icon, label, href, active, dot, className, onClick, ...rest } = props

  const handleClick = (e: React.MouseEvent) => {
    if (onClick) {
      e.preventDefault()
      onClick()
    }
  }

  return (
    <Link
      className={classNames('base-layout-nav__item', className, { active })}
      to={href}
      onClick={handleClick}
      {...rest}
    >
      <img className="base-layout-nav__item-icon" src={icon} />
      <span className="base-layout-nav__item-label">{label}</span>

      {dot && <div className="base-layout-nav__item-dot" />}
    </Link>
  )
}
