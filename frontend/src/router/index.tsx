import { RouterProvider } from 'react-router-dom'
import { RouterContext } from './context'
import { router } from './routes'

export function Router() {
  return (
    <RouterContext.Provider value={router as any}>
      <RouterProvider router={router} />
    </RouterContext.Provider>
  )
}
