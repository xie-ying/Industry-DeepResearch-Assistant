import { createContext } from 'react'
import { createBrowserRouter } from 'react-router-dom'

export const RouterContext = createContext<
  ReturnType<typeof createBrowserRouter>
>(null as any)
