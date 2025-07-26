'use client'

import React, { createContext, useContext, useState, useEffect } from 'react'

interface AuthContextType {
  isAuthenticated: boolean
  login: (username: string, password: string) => boolean
  logout: () => void
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

const ADMIN_USERNAME = 'admin'
const ADMIN_PASSWORD = 'Aa1234567$$$'

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState(false)

  useEffect(() => {
    const authStatus = localStorage.getItem('videoConverter_auth')
    if (authStatus === 'true') {
      setIsAuthenticated(true)
    }
  }, [])

  const login = (username: string, password: string): boolean => {
    if (username === ADMIN_USERNAME && password === ADMIN_PASSWORD) {
      setIsAuthenticated(true)
      localStorage.setItem('videoConverter_auth', 'true')
      return true
    }
    return false
  }

  const logout = () => {
    setIsAuthenticated(false)
    localStorage.removeItem('videoConverter_auth')
  }

  return (
    <AuthContext.Provider value={{ isAuthenticated, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}