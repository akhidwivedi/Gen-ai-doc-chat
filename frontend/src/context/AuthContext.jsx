import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import * as authApi from '../api/auth'
import { tokenStore } from '../api/client'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(Boolean(tokenStore.access))

  const logout = useCallback(() => {
    tokenStore.clear()
    setUser(null)
  }, [])

  // Restore session on page load.
  useEffect(() => {
    if (!tokenStore.access) return
    authApi.me().then(setUser).catch(logout).finally(() => setLoading(false))
  }, [logout])

  // The axios interceptor fires this when a refresh fails.
  useEffect(() => {
    window.addEventListener('docchat:logout', logout)
    return () => window.removeEventListener('docchat:logout', logout)
  }, [logout])

  const login = useCallback(async (credentials) => {
    const tokens = await authApi.login(credentials)
    tokenStore.set(tokens)
    setUser(await authApi.me())
  }, [])

  const register = useCallback(async (payload) => {
    const data = await authApi.register(payload)
    tokenStore.set(data)
    setUser(data.user)
  }, [])

  const value = useMemo(
    () => ({ user, loading, login, register, logout }),
    [user, loading, login, register, logout],
  )
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export const useAuth = () => useContext(AuthContext)
