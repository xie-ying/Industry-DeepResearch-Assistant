import { AxiosResponse } from 'axios'
import { ResponseError } from '../error'
import { IRequestPlugin } from './plugin'

export const CODE_KEY = 'status'
export const MESSAGE_KEY = 'message'

/**
 * 处理与后端接口上的约定
 */
export const servicePlugin: IRequestPlugin = {
  install(instance) {
    instance.interceptors.response.use(
      (response) => {
        const data = response?.data
        if (!response || !isObject(data)) return response
        if (!(CODE_KEY in data)) return response

        const code = data[CODE_KEY]
        if (code !== 'success') {
          const message =
            data[MESSAGE_KEY] || data.detail || 'API data exception'
          const error = new ResponseError(message, response)
          return Promise.reject(error)
        }

        return response
      },
      (error) => {
        const response = error.response as AxiosResponse<any> | undefined

        const data = response?.data
        if (!response || !isObject(data)) return Promise.reject(error)
        if (!(CODE_KEY in data)) return Promise.reject(error)

        const code = data[CODE_KEY]
        if (code !== 'success') {
          const message =
            data[MESSAGE_KEY] || data.detail || 'API data exception'
          const error = new ResponseError(message, response)
          return Promise.reject(error)
        }

        return Promise.reject(error)
      },
    )
  },
}

function isObject(value: unknown) {
  const type = typeof value
  return value != null && (type === 'object' || type === 'function')
}
