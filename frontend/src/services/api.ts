// API Client centralizado com tratamento de erros e tipagem

// URL da API - usa variável de ambiente ou localhost para desenvolvimento
const API_URL = import.meta.env.VITE_API_URL || (
    import.meta.env.MODE === 'production' 
        ? window.location.origin 
        : 'http://localhost:8000'
)

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

async function request<T>(
    endpoint: string,
    options?: RequestInit
): Promise<T> {
    const url = `${API_URL}${endpoint}`

    const config: RequestInit = {
        ...options,
        headers: {
            'Content-Type': 'application/json',
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
