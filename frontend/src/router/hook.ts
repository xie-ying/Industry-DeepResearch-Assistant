import { useContext, useMemo } from 'react'
import { matchRoutes, useLocation } from 'react-router-dom'
import { RouterContext } from './context'
import { IRouteObject } from './routes'

export function useRoute() {
  const router = useContext(RouterContext)
  const { pathname } = useLocation()
  const route = useMemo(() => {
    const routes = matchRoutes(router.routes, pathname)
    return routes?.[routes.length - 1]?.route
  }, [pathname, router])
  return route as IRouteObject | undefined
}

export function useQuery() {
  const location = useLocation()
  const query = useMemo(
    () => new URLSearchParams(location.search),
    [location.search],
  )

  return query
}
