import { proxy, subscribe } from 'valtio'

export interface UserInfo {
  id: string
  username: string
  email: string
  is_active: boolean
  created_at: string
}

interface AuthState {
  token: string | null
  user: UserInfo | null
  isLoggedIn: boolean
}

const AUTH_STORAGE_KEY = 'auth'

// 从 localStorage 加载初始状态
function loadAuthState(): AuthState {
  try {
    const saved = localStorage.getItem(AUTH_STORAGE_KEY)
    if (saved) {
      return JSON.parse(saved)
    }
  } catch (e) {
    console.error('Failed to load auth state:', e)
  }
  return {
    token: null,
    user: null,
    isLoggedIn: false,
  }
}

// 保存状态到 localStorage
function saveAuthState(state: AuthState) {
  try {
    localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(state))
  } catch (e) {
    console.error('Failed to save auth state:', e)
  }
}

export const authState = proxy<AuthState>(loadAuthState())

// 订阅状态变化，自动保存
subscribe(authState, () => {
  saveAuthState({
    token: authState.token,
    user: authState.user,
    isLoggedIn: authState.isLoggedIn,
  })
})

export const authActions = {
  login(token: string, user: UserInfo) {
    authState.token = token
    authState.user = user
    authState.isLoggedIn = true
  },

  logout() {
    authState.token = null
    authState.user = null
    authState.isLoggedIn = false
    localStorage.removeItem(AUTH_STORAGE_KEY)
  },

  updateUser(user: Partial<UserInfo>) {
    if (authState.user) {
      Object.assign(authState.user, user)
    }
  },
}
