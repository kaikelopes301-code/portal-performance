// Service para integração com SharePoint
import { api } from './api'

// === Types ===

export interface SharePointStatus {
    configured: boolean
    connected: boolean
    folder_path?: string
    site_id?: string
    drive_id?: string
    last_sync?: string
    error?: string
}

export interface SharePointFile {
    id: string
    name: string
    size: number
    created_at?: string
    modified_at?: string
    web_url?: string
}

export interface SharePointSyncRequest {
    folder_path?: string
    region_mapping?: Record<string, string>
}

export interface SharePointSyncResult {
    success: boolean
    files_synced: number
    files: Array<{
        original_name: string
        local_path: string
        region?: string
        modified_at?: string
    }>
    jobs_created: number[]
    error?: string
}

export interface SharePointFolderInfo {
    exists: boolean
    path: string
    id?: string
    name?: string
    web_url?: string
    created_at?: string
    modified_at?: string
    child_count?: number
}

export interface SharePointConnectionTest {
    success: boolean
    token_valid?: boolean
    files_found?: number
    folder_path?: string
    error?: string
    required_vars?: string[]
}

export interface ParseLinkResponse {
    valid: boolean
    site_host?: string
    site_name?: string
    file_name?: string
    region?: string
    error?: string
}

export interface ImportLinkRequest {
    url: string
    region?: string
}

export interface ImportLinkResponse {
    success: boolean
    filename?: string
    region?: string
    job_id?: number
    local_path?: string
    error?: string
}

export interface PresetLinksResponse {
    links: Record<string, string>
    description: string
}

// === Service ===

export const sharePointService = {
    /**
     * Obtém o status de configuração do SharePoint
     */
    getStatus: () =>
        api.get<SharePointStatus>('/api/sharepoint/status'),

    /**
     * Lista arquivos disponíveis no SharePoint
     */
    listFiles: (folderPath?: string) => {
        const params = folderPath ? `?folder_path=${encodeURIComponent(folderPath)}` : ''
        return api.get<SharePointFile[]>(`/api/sharepoint/files${params}`)
    },

    /**
     * Obtém informações de uma pasta
     */
    getFolderInfo: (folderPath?: string) => {
        const params = folderPath ? `?folder_path=${encodeURIComponent(folderPath)}` : ''
        return api.get<SharePointFolderInfo>(`/api/sharepoint/folder-info${params}`)
    },

    /**
     * Sincroniza arquivos do SharePoint e cria jobs
     */
    sync: (request: SharePointSyncRequest) =>
        api.post<SharePointSyncResult>('/api/sharepoint/sync', request),

    /**
     * Sincroniza todos os arquivos da pasta padrão
     */
    syncFolder: (folderPath?: string, regionMapping?: Record<string, string>) =>
        api.post<SharePointSyncResult>('/api/sharepoint/sync', {
            folder_path: folderPath,
            region_mapping: regionMapping
        }),

    /**
     * Baixa um arquivo específico
     */
    downloadFile: (fileId: string, region?: string) => {
        const params = region ? `?region=${encodeURIComponent(region)}` : ''
        return api.post<{ success: boolean; local_path: string; job_id: number }>(
            `/api/sharepoint/download/${fileId}${params}`
        )
    },

    /**
     * Testa a conexão com o SharePoint
     */
    testConnection: () =>
        api.get<SharePointConnectionTest>('/api/sharepoint/test-connection'),

    /**
     * Analisa um link do SharePoint
     */
    parseLink: (url: string) =>
        api.post<ParseLinkResponse>(`/api/sharepoint/parse-link?url=${encodeURIComponent(url)}`),

    /**
     * Importa planilha a partir de um link do SharePoint
     */
    importFromLink: (url: string, region?: string) =>
        api.post<ImportLinkResponse>('/api/sharepoint/import-link', { url, region }),

    /**
     * Obtém os links pré-configurados por região
     */
    getPresetLinks: () =>
        api.get<PresetLinksResponse>('/api/sharepoint/preset-links'),

    /**
     * Importa planilha pré-configurada de uma região
     */
    importPreset: (region: string) =>
        api.post<ImportLinkResponse>(`/api/sharepoint/import-preset/${region}`),
}

export default sharePointService
