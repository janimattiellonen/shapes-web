import type { RouteObject } from 'react-router-dom'
import { MainLayout } from '../layouts/MainLayout'
import ShapeDetectionPage from '../pages/ShapeDetectionPage'
import BorderDetectionPage from '../pages/BorderDetectionPage'

export const routes: RouteObject[] = [
  {
    element: <MainLayout />,
    children: [
      {
        path: '/',
        element: <ShapeDetectionPage />
      },
      {
        path: '/discs/border-detection',
        element: <BorderDetectionPage />
      }
    ]
  }
]
