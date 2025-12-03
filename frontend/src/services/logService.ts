// Service para operações de Logs
import { api } from './api'
import type { LogListResponse, LogStats } from '@/types'

export interface LogFilters {
    unit_name?: string
    status?: 'sent' | 'failed' | 'queued'
    month_ref?: string
    date_from?: string  // YYYY-MM-DD
    date_to?: string    // YYYY-MM-DD
    is_dry_run?: boolean  // true = teste, false = envio real
    region?: string  // RJ, SP1, SP2, SP3, NNE
}

export const logService = {
    /**
     * Lista logs de envio com paginação e filtros
     */
    list: (limit = 50, skip = 0, filters?: LogFilters) => {
        const params = new URLSearchParams()
        params.set('limit', String(limit))
        params.set('skip', String(skip))
        
        if (filters) {
            if (filters.unit_name) params.set('unit_name', filters.unit_name)
            if (filters.status) params.set('status', filters.status)
            if (filters.month_ref) params.set('month_ref', filters.month_ref)
            if (filters.date_from) params.set('date_from', filters.date_from)
            if (filters.date_to) params.set('date_to', filters.date_to)
            if (filters.is_dry_run !== undefined) params.set('is_dry_run', String(filters.is_dry_run))
            if (filters.region) params.set('region', filters.region)
        }
        
        return api.get<LogListResponse>(`/api/logs/?${params.toString()}`)
    },

    /**
     * Busca logs filtrados por unidade
     */
    byUnit: (unitName: string, limit = 20) =>
        api.get<LogListResponse>(
            `/api/logs/?unit_name=${encodeURIComponent(unitName)}&limit=${limit}`
        ),

    /**
     * Busca logs filtrados por mês de referência
     */
    byMonth: (monthRef: string, limit = 50) =>
        api.get<LogListResponse>(`/api/logs/?month_ref=${monthRef}&limit=${limit}`),

    /**
     * Busca logs de um job específico
     */
    byJob: (jobId: string) =>
        api.get<LogListResponse>(`/api/logs/?job_id=${jobId}`),
    
    /**
     * Obtém estatísticas dos logs
     */
    getStats: () =>
        api.get<LogStats>('/api/logs/stats'),
    
    /**
     * Remove um log específico
     */
    delete: (logId: number) =>
        api.delete<{ message: string; id: number }>(`/api/logs/${logId}`),
    
    /**
     * Limpa logs antigos (mais de X dias)
     */
    cleanup: (days = 90) =>
        api.delete<{ message: string; deleted_count: number; cutoff_date: string }>(
            `/api/logs/cleanup?days=${days}`
        ),
}

export default logService
