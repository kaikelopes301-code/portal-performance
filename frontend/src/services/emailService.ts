/**
 * Serviço centralizado para operações de email
 * Gerencia envio de emails, preview e edição de HTMLs
 */

import { api } from './api'
import config from '@/config'

// Tipos
export interface HtmlFileInfo {
    filename: string
    unit_name: string
    month: string
    region: string
    full_path: string
}

export interface EditableTexts {
    subject: string      // Título no HTML (h1)
    greeting: string     // Saudação
    intro: string        // Texto introdutório
    observation: string  // Observação/alerta
}

export interface SendEmailRequest {
    email_subject: string           // Assunto do email (linha de assunto)
    recipients?: string[]           // Destinatários (opcional - extrai do HTML)
    cc_emails?: string[]            // CCs adicionais
    mandatory_cc?: string           // CC obrigatório
    sender_email?: string           // Email remetente
    sender_name?: string            // Nome remetente
}

export interface SendEmailResponse {
    success: boolean
    message?: string
    emails_sent_to?: string[]
    cc_emails?: string[]
    subject?: string
    error?: string
}

export interface PreviewStats {
    total_files: number
    total_size: string
    regions: string[]
    months: string[]
    last_generated: string | null
    output_path: string
}

// Funções auxiliares
const formatMonthForSubject = (monthStr: string): string => {
    if (!monthStr) return ''
    const [year, month] = monthStr.split('-')
    const months = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
                    'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
    const monthIndex = parseInt(month) - 1
    return `${months[monthIndex]}/${year}`
}

export const generateDefaultSubject = (unitName: string, month: string): string => {
    const mesRef = formatMonthForSubject(month)
    return `Medição ${unitName} - ${mesRef}`
}

// Serviço
export const emailService = {
    /**
     * Lista todos os arquivos HTML gerados
     */
    listFiles: async (): Promise<HtmlFileInfo[]> => {
        return api.get<HtmlFileInfo[]>('/preview/files')
    },

    /**
     * Obtém o conteúdo HTML de um arquivo
     */
    getHtmlContent: async (filename: string): Promise<string> => {
        const response = await fetch(`${config.apiUrl}/preview/files/${encodeURIComponent(filename)}`)
        if (!response.ok) throw new Error('Arquivo não encontrado')
        return response.text()
    },

    /**
     * Obtém os textos editáveis de um arquivo HTML
     */
    getEditableTexts: async (filename: string): Promise<EditableTexts> => {
        return api.get<EditableTexts>(`/preview/files/${encodeURIComponent(filename)}/texts`)
    },

    /**
     * Atualiza os textos editáveis de um arquivo HTML
     */
    updateEditableTexts: async (filename: string, texts: Partial<EditableTexts>): Promise<{ success: boolean; changes: string[] }> => {
        return api.post(`/preview/files/${encodeURIComponent(filename)}/texts`, texts)
    },

    /**
     * Envia email usando o HTML atual (com edições)
     * Este é o método principal para envio de emails do Preview
     */
    sendFromPreview: async (filename: string, request: SendEmailRequest): Promise<SendEmailResponse> => {
        return api.post<SendEmailResponse>(`/preview/files/${encodeURIComponent(filename)}/send`, {
            ...request,
            mandatory_cc: request.mandatory_cc || config.email.mandatoryCc
        })
    },

    /**
     * Obtém estatísticas dos arquivos HTML
     */
    getStats: async (): Promise<PreviewStats> => {
        return api.get<PreviewStats>('/preview/stats')
    },

    /**
     * Lista meses disponíveis
     */
    getAvailableMonths: async (): Promise<string[]> => {
        return api.get<string[]>('/preview/months')
    },

    /**
     * Lista regiões com contagem de arquivos
     */
    getRegions: async (): Promise<{ code: string; count: number }[]> => {
        return api.get<{ code: string; count: number }[]>('/preview/regions')
    }
}

export default emailService
