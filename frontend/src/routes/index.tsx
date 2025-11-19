import type { RouteObject } from 'react-router-dom'
import { MainLayout } from '../layouts/MainLayout'
import ShapeDetectionPage from '../pages/ShapeDetectionPage'
import BorderDetectionPage from '../pages/BorderDetectionPage'
import NewDiscPage from '../pages/NewDiscPage'
import DiscsPage from '../pages/DiscsPage'

export const routes: RouteObject[] = [
  {
    element: <MainLayout />,
    children: [
      {
        path: '/',
        element: <DiscsPage />
      },
      {
        path: '/discs/shape-detection',
        element: <ShapeDetectionPage />
      },
      {
        path: '/discs/border-detection',
        element: <BorderDetectionPage />
      },
      {
        path: '/discs/new',
        element: <NewDiscPage />
      }
    ]
  }
]
