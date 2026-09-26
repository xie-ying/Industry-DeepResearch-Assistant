import { AxiosResponse } from 'axios'

export class ResponseError extends Error {
  response: AxiosResponse<any> | undefined

  constructor(message: string, response?: AxiosResponse<any>) {
    super(message)
    this.response = response
  }
}
