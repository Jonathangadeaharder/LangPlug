import React, { useEffect } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { useAuthStore } from '@/store/useAuthStore'
import { FlexCenter } from '@/styles/GlobalStyles'

interface ProtectedRouteProps {
  children: React.ReactNode
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  const { isAuthenticated, isLoading, checkAuth } = useAuthStore()
  const location = useLocation()

  useEffect(() => {
    checkAuth()
  }, [checkAuth])

  if (isLoading) {
    return (
      <FlexCenter>
        <div className="loading-spinner" />
      </FlexCenter>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  return <>{children}</>
}
