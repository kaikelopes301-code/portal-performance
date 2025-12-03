/**
 * Configuração centralizada do aplicativo
 * 
 * Em produção, as variáveis de ambiente devem ser definidas:
 * - VITE_API_URL: URL da API backend (ex: https://api.seudominio.com)
 * - VITE_ENV: Ambiente atual (development, staging, production)
 */

// Determinar o ambiente
const ENV = import.meta.env.VITE_ENV || import.meta.env.MODE || 'development'

// URL da API baseada no ambiente
const getApiUrl = (): string => {
    // Se houver variável de ambiente definida, usar ela
    if (import.meta.env.VITE_API_URL) {
        return import.meta.env.VITE_API_URL
    }
    
    // Em produção, usar URL relativa ou configurada
    if (ENV === 'production') {
        // Em produção, assumir que API está no mesmo domínio
        return window.location.origin
    }
    
    // Em desenvolvimento, usar localhost
    return 'http://localhost:8000'
}

export const config = {
    // Ambiente
    env: ENV,
    isDevelopment: ENV === 'development',
    isProduction: ENV === 'production',
    
    // API
    apiUrl: getApiUrl(),
    
    // Email
    email: {
        mandatoryCc: 'consultoria@atlasinovacoes.com.br',
        defaultSenderName: 'Portal Performance',
    },
    
    // Timeouts
    timeouts: {
        apiRequest: 30000, // 30 segundos
        emailSend: 60000,  // 60 segundos para envio de email
    },
    
    // Mensagens padrão
    messages: {
        emailSentSuccess: 'Email enviado com sucesso!',
        emailSentError: 'Falha ao enviar email. Tente novamente.',
        noRecipientsError: 'Nenhum destinatário encontrado no HTML.',
        loadingError: 'Erro ao carregar dados. Verifique a conexão.',
    }
}

export default config
