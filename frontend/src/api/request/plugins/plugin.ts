import { AxiosInstance } from 'axios'

export type IRequestPlugin = {
  preinstall?: (instance: AxiosInstance) => void
  install?: (instance: AxiosInstance) => void
  postinstall?: (instance: AxiosInstance) => void
}

export function installPlugins(
  instance: AxiosInstance,
  plugins: IRequestPlugin[],
) {
  plugins
    .slice()
    .reverse()
    .forEach(({ preinstall }) => preinstall?.(instance))
  plugins.forEach(({ install }) => install?.(instance))
  plugins.forEach(({ postinstall }) => postinstall?.(instance))
}
