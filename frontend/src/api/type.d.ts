declare namespace API {
  type Result<T> = T & {
    status: 'success' | 'error'
    message: string
  }
}
