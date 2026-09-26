/**
 * 认证插件：自动添加 Token 到请求头
 */
import { IRequestPlugin } from './plugin'

const AUTH_STORAGE_KEY = 'auth'

function getToken(): string | null {
  try {
    const authData = localStorage.getItem(AUTH_STORAGE_KEY)
    if (authData) {
      const parsed = JSON.parse(authData)
      return parsed?.token || null
    }
  } catch {
    // ignore
  }
  return null
}

export const authPlugin: IRequestPlugin = {
  preinstall(instance) {
    instance.interceptors.request.use(
      (config) => {
        const token = getToken()
        if (token) {
          config.headers.Authorization = `Bearer ${token}`
        }
        return config
      },
      (error) => Promise.reject(error)
    )
  },
}
