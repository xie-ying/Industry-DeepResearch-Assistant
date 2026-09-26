import storage from './storage'
import proxyWithPersist, { PersistStrategy } from './valtio-persist'

// 搜索模式类型
export type SearchMode = 'web' | 'local'

const state = proxyWithPersist({
  name: 'device',
  version: 1,
  getStorage: () => storage,
  persistStrategies: {
    searchModes: PersistStrategy.SingleFile,
  },
  migrations: {
    // 从 v0 迁移: useDeepsearch -> searchModes
    1: (oldState: any) => ({
      ...oldState,
      searchModes: oldState.useDeepsearch ? ['web'] : [],
      useDeepsearch: undefined,
    }),
  },

  initialState: {
    chatting: false,
    // 搜索模式: 'web' = 深度搜索(网络), 'local' = 本地知识库
    searchModes: [] as SearchMode[],
  },
})

const actions = {
  setChatting(chatting: boolean) {
    state.chatting = chatting
  },
  setSearchModes(modes: SearchMode[]) {
    state.searchModes = modes
  },
  toggleSearchMode(mode: SearchMode) {
    const currentModes = state.searchModes as SearchMode[]
    if (currentModes.includes(mode)) {
      state.searchModes = currentModes.filter(m => m !== mode)
    } else {
      state.searchModes = [...currentModes, mode]
    }
  },
  // 兼容旧代码
  get useDeepsearch() {
    return (state.searchModes as SearchMode[]).includes('web')
  },
  get useLocalKb() {
    return (state.searchModes as SearchMode[]).includes('local')
  },
}

export const deviceState = state
export const deviceActions = actions
