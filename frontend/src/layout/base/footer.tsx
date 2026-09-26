import { authActions, authState } from '@/store/auth'
import { LogoutOutlined, UserOutlined } from '@ant-design/icons'
import { Avatar, Dropdown, message } from 'antd'
import type { MenuProps } from 'antd'
import { useNavigate } from 'react-router-dom'
import { useSnapshot } from 'valtio'
import './footer.scss'

export function Footer() {
  const navigate = useNavigate()
  const { user } = useSnapshot(authState)

  const handleLogout = () => {
    authActions.logout()
    message.success('已退出登录')
    navigate('/login')
  }

  const menuItems: MenuProps['items'] = [
    {
      key: 'user-info',
      label: (
        <div className="user-menu-info">
          <div className="user-menu-name">{user?.username || '用户'}</div>
          <div className="user-menu-email">{user?.email || ''}</div>
        </div>
      ),
      disabled: true,
    },
    {
      type: 'divider',
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录',
      onClick: handleLogout,
      danger: true,
    },
  ]

  // 获取用户名首字母作为头像显示
  const getAvatarText = () => {
    if (user?.username) {
      return user.username.charAt(0).toUpperCase()
    }
    return 'U'
  }

  return (
    <div className="base-layout-footer">
      <Dropdown
        menu={{ items: menuItems }}
        placement="topRight"
        trigger={['click']}
        overlayClassName="user-dropdown-overlay"
      >
        <div className="user-avatar-wrapper">
          <Avatar
            size={36}
            icon={<UserOutlined />}
            className="user-avatar"
          >
            {getAvatarText()}
          </Avatar>
        </div>
      </Dropdown>
    </div>
  )
}
