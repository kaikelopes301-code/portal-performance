// Service para operações de Configuração
import { api } from './api'
import type { AppConfig, DefaultsConfig, RegionConfig, UnitConfig } from '@/types'

export const configService = {
    /**
     * Busca configuração completa
     */
    getAll: () =>
        api.get<AppConfig>('/api/config/'),

    /**
     * Busca configurações padrão
     */
    getDefaults: () =>
        api.get<DefaultsConfig>('/api/config/defaults'),

    /**
     * Lista todas as regiões configuradas
     */
    listRegions: () =>
        api.get<{ regions: Record<string, RegionConfig>; count: number }>('/api/config/regions'),

    /**
     * Busca configuração de uma região
     */
    getRegion: (regionCode: string) =>
        api.get<RegionConfig>(`/api/config/regions/${regionCode}`),

    /**
     * Atualiza configuração de uma região
     */
    updateRegion: (regionCode: string, data: Partial<RegionConfig>) =>
        api.put<RegionConfig>(`/api/config/regions/${regionCode}`, data),

    /**
     * Lista todas as unidades configuradas
     */
    listUnits: () =>
        api.get<{ units: Record<string, UnitConfig>; count: number }>('/api/config/units'),

    /**
     * Busca configuração de uma unidade
     */
    getUnit: (unitName: string) =>
        api.get<UnitConfig>(`/api/config/units/${encodeURIComponent(unitName)}`),

    /**
     * Atualiza configuração de uma unidade
     */
    updateUnit: (unitName: string, data: Partial<UnitConfig>) =>
        api.put<UnitConfig>(`/api/config/units/${encodeURIComponent(unitName)}`, data),

    /**
     * Busca configuração efetiva (cascata: unit > region > defaults)
     */
    getEffectiveConfig: (unitName: string) =>
        api.get<UnitConfig>(`/api/config/units/${encodeURIComponent(unitName)}/effective`),

    /**
     * Lista colunas disponíveis para seleção
     */
    getAvailableColumns: () =>
        api.get<{ columns: string[] }>('/api/config/columns/available'),
}

export default configService
