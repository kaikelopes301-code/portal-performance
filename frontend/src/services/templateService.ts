// Service para operações de Templates de Email
import { api } from './api'
import type { Template, TemplateListResponse, TemplatePreview } from '@/types'

export const templateService = {
    /**
     * Lista todos os templates disponíveis
     */
    list: () =>
        api.get<TemplateListResponse>('/api/templates/'),

    /**
     * Busca um template específico
     */
    get: (templateId: string) =>
        api.get<Template>(`/api/templates/${templateId}`),

    /**
     * Atualiza um template
     */
    update: (templateId: string, data: Partial<Template>) =>
        api.put<Template>(`/api/templates/${templateId}`, data),

    /**
     * Busca o conteúdo HTML do template
     */
    getContent: (templateId: string) =>
        api.get<{ content: string; filename: string }>(`/api/templates/${templateId}/content`),

    /**
     * Gera preview do template com dados de exemplo
     */
    preview: (templateId: string, sampleData?: Record<string, string>) => {
        const params = sampleData
            ? `?${new URLSearchParams(sampleData).toString()}`
            : ''
        return api.get<TemplatePreview>(`/api/templates/${templateId}/preview${params}`)
    },

    /**
     * Define um template como padrão
     */
    setDefault: (templateId: string) =>
        api.post<{ message: string }>(`/api/templates/default/${templateId}`),

    /**
     * Busca o template padrão atual
     */
    getDefault: () =>
        api.get<Template>('/api/templates/default'),
}

export default templateService
