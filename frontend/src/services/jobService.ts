// Service para operações de Jobs/Upload
import { api } from './api'
import type { Job, JobListResponse } from '@/types'

// Tipo para upload com região
export interface FileWithRegion {
    file: File
    region?: string
}

// Tipo para resposta de regiões
export interface RegionsResponse {
    regions: string[]
    description: Record<string, string>
}

export const jobService = {
    /**
     * Lista jobs com paginação
     */
    list: (limit = 20, offset = 0) =>
        api.get<JobListResponse>(`/api/jobs?limit=${limit}&offset=${offset}`),

    /**
     * Busca um job específico
     */
    get: (jobId: string) =>
        api.get<Job>(`/api/jobs/${jobId}`),

    /**
     * Lista regiões válidas para upload
     */
    getRegions: () =>
        api.get<RegionsResponse>('/api/upload/regions'),

    /**
     * Upload de arquivo Excel (único)
     */
    upload: async (file: File, region?: string): Promise<Job> => {
        const formData = new FormData()
        formData.append('file', file)
        if (region) {
            formData.append('region', region)
        }
        return api.post<Job>('/api/upload/', formData)
    },

    /**
     * Upload de múltiplos arquivos Excel (até 5)
     */
    uploadBatch: async (filesWithRegions: FileWithRegion[]): Promise<Job[]> => {
        const formData = new FormData()
        
        // Adiciona cada arquivo
        filesWithRegions.forEach(({ file }) => {
            formData.append('files', file)
        })
        
        // Adiciona as regiões como string separada por vírgula
        const regions = filesWithRegions.map(f => f.region || '').join(',')
        if (regions.replace(/,/g, '').length > 0) {
            formData.append('regions', regions)
        }
        
        return api.post<Job[]>('/api/upload/batch', formData)
    },

    /**
     * Processa um job (extração e geração de HTMLs)
     */
    process: (jobId: string) =>
        api.post<Job>(`/api/process/${jobId}`),

    /**
     * Busca metadados extraídos do job
     */
    getMetadata: (jobId: string) =>
        api.get<{ units: string[]; month_ref: string; row_count: number }>(
            `/api/process/${jobId}/metadata`
        ),

    /**
     * Busca resultado processado
     */
    getResult: (jobId: string) =>
        api.get<{ job_id: string; units: Record<string, unknown>; generated_files: string[] }>(
            `/api/process/${jobId}/result`
        ),

    /**
     * Preview do HTML gerado
     */
    previewResult: (jobId: string, unitName?: string) => {
        const params = unitName ? `?unit_name=${encodeURIComponent(unitName)}` : ''
        return api.get<{ html: string; unit_name: string }>(
            `/api/process/${jobId}/result/preview${params}`
        )
    },
}

export default jobService
