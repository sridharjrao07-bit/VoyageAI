import { createContext, useContext, useState, useEffect, useCallback } from 'react'
import { authMe, authLogin, authRegister } from '../api/tourismApi'
import api from '../api/tourismApi'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
    const [user, setUser] = useState(null)
    const [token, setToken] = useState(() => localStorage.getItem('allora_token'))
    const [isLoading, setIsLoading] = useState(!!localStorage.getItem('allora_token'))

    // On mount, verify stored token and load user profile
    useEffect(() => {
        const stored = localStorage.getItem('allora_token')
        if (!stored) { setIsLoading(false); return }

        // Pre-set axios header before the /auth/me call
        api.defaults.headers.common['Authorization'] = `Bearer ${stored}`

        authMe()
            .then(userData => setUser(userData))
            .catch(() => {
                localStorage.removeItem('allora_token')
                setToken(null)
                delete api.defaults.headers.common['Authorization']
            })
            .finally(() => setIsLoading(false))
    }, []) // eslint-disable-line react-hooks/exhaustive-deps

    const _persist = useCallback((tokenStr, userData) => {
        localStorage.setItem('allora_token', tokenStr)
        setToken(tokenStr)
        setUser(userData)
        api.defaults.headers.common['Authorization'] = `Bearer ${tokenStr}`
    }, [])

    const login = useCallback(async (username, password) => {
        const data = await authLogin(username, password)
        _persist(data.access_token, data.user)
        return data.user
    }, [_persist])

    const register = useCallback(async (payload) => {
        const data = await authRegister(payload)
        _persist(data.access_token, data.user)
        return data.user
    }, [_persist])

    const logout = useCallback(() => {
        localStorage.removeItem('allora_token')
        setToken(null)
        setUser(null)
        delete api.defaults.headers.common['Authorization']
    }, [])

    return (
        <AuthContext.Provider value={{ user, token, isLoading, login, register, logout }}>
            {children}
        </AuthContext.Provider>
    )
}

export function useAuth() {
    const ctx = useContext(AuthContext)
    if (!ctx) throw new Error('useAuth must be used within <AuthProvider>')
    return ctx
}
