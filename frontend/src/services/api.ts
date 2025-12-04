// API Client centralizado com tratamento de erros e tipagem

// URL da API - usa variável de ambiente ou localhost para desenvolvimento
const API_URL = import.meta.env.VITE_API_URL || (
    import.meta.env.MODE === 'production' 
        ? window.location.origin 
        : 'http://localhost:8000'
)

// Chaves do localStorage para tokens
const TOKEN_KEY = 'atlas_token'
const TOKEN_EXPIRY_KEY = 'atlas_token_expiry'

class ApiError extends Error {
    constructor(
        public status: number,
        public statusText: string,
        public data?: unknown
    ) {
        super(`API Error: ${status} ${statusText}`)
        this.name = 'ApiError'
    }
}

// Funções para gerenciar o token
export function getToken(): string | null {
    const token = localStorage.getItem(TOKEN_KEY)
    const expiry = localStorage.getItem(TOKEN_EXPIRY_KEY)
    
    if (!token || !expiry) return null
    
    // Verifica se o token expirou
    if (new Date(expiry) < new Date()) {
        clearToken()
        return null
    }
    
    return token
}

export function setToken(token: string, expiresIn: number): void {
    const expiry = new Date()
    expiry.setSeconds(expiry.getSeconds() + expiresIn)
    
    localStorage.setItem(TOKEN_KEY, token)
    localStorage.setItem(TOKEN_EXPIRY_KEY, expiry.toISOString())
}

export function clearToken(): void {
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(TOKEN_EXPIRY_KEY)
}

async function request<T>(
    endpoint: string,
    options?: RequestInit
): Promise<T> {
    const url = `${API_URL}${endpoint}`
    
    // Obtém o token se existir
    const token = getToken()

    const config: RequestInit = {
        ...options,
        headers: {
            'Content-Type': 'application/json',
            ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
            ...options?.headers,
        },
    }

    // Remove Content-Type for FormData (browser sets it automatically with boundary)
    if (options?.body instanceof FormData) {
        delete (config.headers as Record<string, string>)['Content-Type']
    }

    const response = await fetch(url, config)

    if (!response.ok) {
        let errorData
        try {
            errorData = await response.json()
        } catch {
            errorData = null
        }
        
        // Se receber 401, limpa o token
        if (response.status === 401) {
            clearToken()
        }
        
        throw new ApiError(response.status, response.statusText, errorData)
    }

    // Handle empty responses
    const contentType = response.headers.get('content-type')
    if (contentType?.includes('application/json')) {
        return response.json()
    }

    return response.text() as unknown as T
}

// HTTP Method helpers
export const api = {
    get: <T>(endpoint: string) => request<T>(endpoint, { method: 'GET' }),

    post: <T>(endpoint: string, data?: unknown) =>
        request<T>(endpoint, {
            method: 'POST',
            body: data instanceof FormData ? data : JSON.stringify(data),
        }),

    put: <T>(endpoint: string, data: unknown) =>
        request<T>(endpoint, {
            method: 'PUT',
            body: JSON.stringify(data),
        }),

    patch: <T>(endpoint: string, data: unknown) =>
        request<T>(endpoint, {
            method: 'PATCH',
            body: JSON.stringify(data),
        }),

    delete: <T>(endpoint: string) => request<T>(endpoint, { method: 'DELETE' }),
}

export { ApiError }
export default api
