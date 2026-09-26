import { authState } from '@/store/auth'
import { Navigate, useLocation } from 'react-router-dom'
import { useSnapshot } from 'valtio'

interface AuthGuardProps {
  children: React.ReactNode
}

/**
 * 认证守卫组件
 *
 * 检查用户是否已登录，未登录则重定向到登录页面
 * 登录后会自动跳转回原来的页面
 */
export function AuthGuard({ children }: AuthGuardProps) {
  const { isLoggedIn } = useSnapshot(authState)
  const location = useLocation()

  if (!isLoggedIn) {
    // 保存当前路径，登录后可以跳转回来
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  return <>{children}</>
}
