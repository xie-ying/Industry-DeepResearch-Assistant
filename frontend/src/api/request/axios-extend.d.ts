import 'axios'

declare module 'axios' {
  export interface AxiosRequestConfig {
    /**
     * 是否显示 loading 遮罩
     * plugins/loading.ts
     */
    loading?: boolean

    /**
     * 请求异常时是否显示 toast 提示
     * plugins/error-toast.ts
     */
    errorToast?: boolean

    /**
     * 取消重复请求
     * plugins/repeat.ts
     */
    cancelRepeat?: boolean
    repeatKey?: string

    /**
     * 展开接口数据
     * 将 response.data.data 提升到 response.data
     * plugins/service.ts
     */
    unwrap?: boolean
  }

  export interface AxiosResponse<T, D> {
    /**
     * 展开接口数据前的原始数据
     * plugins/service.ts
     */
    _data?: {
      code: number
      msg: string
      data: T
    }
  }
}
