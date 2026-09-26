import { AxiosRequestConfig } from 'axios'
import { IRequestPlugin } from './plugin'

const abortControllerMap = new WeakMap<AbortSignal, AbortController>()

export function createAbortController() {
  const controller = new AbortController()
  abortControllerMap.set(controller.signal, controller)
  return controller
}

const map = new Map<string, AxiosRequestConfig>()

function set(config: AxiosRequestConfig) {
  const key = getRepeatKey(config)
  const signal = map.get(key)?.signal as AbortSignal
  if (signal) {
    abortControllerMap.get(signal)?.abort('Duplicate request canceled')
  }
  map.set(key, config)
}
export function remove(config: AxiosRequestConfig) {
  const key = getRepeatKey(config)
  map.delete(key)
}

export function getRepeatKey(config: AxiosRequestConfig) {
  return `${config.method}-${config.url}-${config.repeatKey ?? ''}`
}

export const repeatPlugin: IRequestPlugin = {
  preinstall(instance) {
    instance.interceptors.response.use((response) => {
      const config = response.config as AxiosRequestConfig
      if (!config.cancelRepeat) return response

      remove(config)

      return response
    })
  },

  postinstall(instance) {
    instance.interceptors.request.use((config) => {
      if (!config.cancelRepeat) return config

      config.signal = config.signal ?? createAbortController().signal
      set(config)

      return config
    })
  },
}
