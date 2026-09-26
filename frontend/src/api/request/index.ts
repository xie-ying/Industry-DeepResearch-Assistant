import { createRequest } from './request'

export const request = createRequest({
  baseURL: import.meta.env.VITE_API_BASE,
  loading: true,
  errorToast: true,
  cancelRepeat: true,
  unwrap: true,
})
