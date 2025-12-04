import { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { api, getToken, setToken, clearToken } from '../services/api'

interface AuthContextType {
    isAuthenticated: boolean
    isLoading: boolean
    login: (username: string, password: string) => Promise<boolean>
    logout: () => void
}

interface LoginResponse {
    success: boolean
    access_token?: string
    token_type?: string
    expires_in?: number
    message?: string
}

interface AuthStatusResponse {
    authenticated: boolean
    user?: string
    message: string
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
    const [isAuthenticated, setIsAuthenticated] = useState(false)
    const [isLoading, setIsLoading] = useState(true)

    useEffect(() => {
        // Verifica se há token válido ao carregar
        const checkAuth = async () => {
            const token = getToken()
            
            if (token) {
                try {
                    // Valida o token com o backend
                    const response = await api.get<AuthStatusResponse>('/api/auth/status')
                    setIsAuthenticated(response.authenticated)
                } catch {
                    // Token inválido ou expirado
                    clearToken()
                    setIsAuthenticated(false)
                }
            }
            
            setIsLoading(false)
        }
        
        checkAuth()
    }, [])

    const login = async (username: string, password: string): Promise<boolean> => {
        try {
            const response = await api.post<LoginResponse>('/api/auth/login', {
                username: username.trim(),
                password
            })
            
            if (response.success && response.access_token) {
                // Salva o token
                setToken(response.access_token, response.expires_in || 28800) // 8 horas default
                setIsAuthenticated(true)
                return true
            }
            
            return false
        } catch (error) {
            console.error('Erro no login:', error)
            return false
        }
    }

    const logout = () => {
        // Chama o endpoint de logout (opcional, para logging)
        api.post('/api/auth/logout').catch(() => {})
        
        // Limpa o token local
        clearToken()
        setIsAuthenticated(false)
    }

    return (
        <AuthContext.Provider value={{ isAuthenticated, isLoading, login, logout }}>
            {children}
        </AuthContext.Provider>
    )
}

export function useAuth() {
    const context = useContext(AuthContext)
    if (context === undefined) {
        throw new Error('useAuth deve ser usado dentro de um AuthProvider')
    }
    return context
}
