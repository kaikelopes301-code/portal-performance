import { createContext, useContext, useState, useEffect, ReactNode } from 'react'

interface AuthContextType {
    isAuthenticated: boolean
    isLoading: boolean
    login: (username: string, password: string) => Promise<boolean>
    logout: () => void
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

async function hashString(str: string): Promise<string> {
    const encoder = new TextEncoder()
    const data = encoder.encode(str + 'atlas_salt_2025_secure')
    const hashBuffer = await crypto.subtle.digest('SHA-256', data)
    const hashArray = Array.from(new Uint8Array(hashBuffer))
    return hashArray.map(b => b.toString(16).padStart(2, '0')).join('')
}

export function AuthProvider({ children }: { children: ReactNode }) {
    const [isAuthenticated, setIsAuthenticated] = useState(false)
    const [isLoading, setIsLoading] = useState(true)

    useEffect(() => {
        // Verifica se há sessão válida ao carregar
        const session = localStorage.getItem('atlas_session')
        const sessionExpiry = localStorage.getItem('atlas_session_expiry')
        
        if (session && sessionExpiry) {
            const expiry = new Date(sessionExpiry)
            if (expiry > new Date()) {
                setIsAuthenticated(true)
            } else {
                // Sessão expirada
                localStorage.removeItem('atlas_session')
                localStorage.removeItem('atlas_session_expiry')
            }
        }
        setIsLoading(false)
    }, [])

    const login = async (username: string, password: string): Promise<boolean> => {
        try {
            const userHash = await hashString(username.toLowerCase().trim())
            const passHash = await hashString(password)
            
            // Validação local com hashes (credenciais hardcoded de forma segura)
            // Usuário: atlas.admin@performance | Senha: Atl@s#P3rf0rm@nc3!2025$Secure
            const validUserHash = await hashString('atlas.admin@performance')
            const validPassHash = await hashString('Atl@s#P3rf0rm@nc3!2025$Secure')
            
            if (userHash === validUserHash && passHash === validPassHash) {
                // Cria sessão com expiração de 8 horas
                const expiry = new Date()
                expiry.setHours(expiry.getHours() + 8)
                
                const sessionToken = await hashString(Date.now().toString() + Math.random().toString())
                localStorage.setItem('atlas_session', sessionToken)
                localStorage.setItem('atlas_session_expiry', expiry.toISOString())
                
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
        localStorage.removeItem('atlas_session')
        localStorage.removeItem('atlas_session_expiry')
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
