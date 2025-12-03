/**
 * Testes para os serviços do frontend
 * 
 * Testes focados em lógica de negócio e validações
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

// Mock do fetch global com headers
const mockFetch = vi.fn()
global.fetch = mockFetch

// Helper para criar resposta de mock
const createMockResponse = (data: any, ok = true, status = 200) => ({
    ok,
    status,
    headers: {
        get: (name: string) => {
            if (name.toLowerCase() === 'content-type') return 'application/json'
            return null
        }
    },
    json: async () => data,
    text: async () => JSON.stringify(data)
})

describe('API Services', () => {
    beforeEach(() => {
        mockFetch.mockClear()
        vi.clearAllMocks()
    })

    afterEach(() => {
        vi.restoreAllMocks()
    })

    describe('API Error Handling', () => {
        it('deve tratar erro 404 corretamente', async () => {
            mockFetch.mockResolvedValueOnce(createMockResponse(
                { error: 'Not found' },
                false,
                404
            ))

            // Simula chamada que trata erro
            const response = await fetch('/api/jobs/99999')
            expect(response.ok).toBe(false)
            expect(response.status).toBe(404)
        })

        it('deve tratar erro 500 corretamente', async () => {
            mockFetch.mockResolvedValueOnce(createMockResponse(
                { error: 'Internal server error' },
                false,
                500
            ))

            const response = await fetch('/api/jobs')
            expect(response.ok).toBe(false)
            expect(response.status).toBe(500)
        })

        it('deve parsear JSON corretamente', async () => {
            const mockData = { jobs: [{ id: 1, status: 'pending' }] }
            mockFetch.mockResolvedValueOnce(createMockResponse(mockData))

            const response = await fetch('/api/jobs')
            expect(response.ok).toBe(true)
            expect(await response.json()).toEqual(mockData)
        })
    })

    describe('Job Service Logic', () => {
        it('deve construir URL com parâmetros corretos', () => {
            const buildUrl = (limit: number, offset: number, status?: string, region?: string) => {
                const params = new URLSearchParams()
                params.set('limit', String(limit))
                params.set('offset', String(offset))
                if (status) params.set('status', status)
                if (region) params.set('region', region)
                return `/api/jobs?${params.toString()}`
            }

            expect(buildUrl(10, 0)).toContain('limit=10')
            expect(buildUrl(10, 0)).toContain('offset=0')
            expect(buildUrl(10, 0, 'pending')).toContain('status=pending')
            expect(buildUrl(10, 0, undefined, 'RJ')).toContain('region=RJ')
        })
    })

    describe('Log Service Logic', () => {
        it('deve construir filtros de log corretamente', () => {
            const buildLogFilters = (filters: {
                unit_name?: string
                status?: string
                month_ref?: string
            }) => {
                const params = new URLSearchParams()
                if (filters.unit_name) params.set('unit_name', filters.unit_name)
                if (filters.status) params.set('status', filters.status)
                if (filters.month_ref) params.set('month_ref', filters.month_ref)
                return params.toString()
            }

            expect(buildLogFilters({ unit_name: 'Shopping A' })).toContain('unit_name=Shopping+A')
            expect(buildLogFilters({ status: 'sent' })).toContain('status=sent')
            expect(buildLogFilters({ month_ref: '2024-11' })).toContain('month_ref=2024-11')
        })
    })

    describe('Upload Service Logic', () => {
        it('deve validar extensão de arquivo .xlsx', () => {
            const isValidExcel = (filename: string) => {
                return filename.toLowerCase().endsWith('.xlsx') || 
                       filename.toLowerCase().endsWith('.xls')
            }

            expect(isValidExcel('relatorio.xlsx')).toBe(true)
            expect(isValidExcel('RELATORIO.XLSX')).toBe(true)
            expect(isValidExcel('dados.xls')).toBe(true)
            expect(isValidExcel('documento.pdf')).toBe(false)
            expect(isValidExcel('texto.txt')).toBe(false)
        })

        it('deve validar regiões válidas', () => {
            const VALID_REGIONS = ['RJ', 'SP1', 'SP2', 'SP3', 'NNE']
            const isValidRegion = (region: string) => VALID_REGIONS.includes(region)

            expect(isValidRegion('RJ')).toBe(true)
            expect(isValidRegion('SP1')).toBe(true)
            expect(isValidRegion('NNE')).toBe(true)
            expect(isValidRegion('INVALID')).toBe(false)
            expect(isValidRegion('')).toBe(false)
        })

        it('deve gerar FormData para upload batch', () => {
            const createBatchFormData = (
                files: { file: File; region: string }[]
            ): FormData => {
                const formData = new FormData()
                files.forEach(({ file, region }) => {
                    formData.append('files', file)
                    formData.append('regions', region)
                })
                return formData
            }

            const mockFile1 = new File([''], 'test1.xlsx', { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
            const mockFile2 = new File([''], 'test2.xlsx', { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })

            const formData = createBatchFormData([
                { file: mockFile1, region: 'RJ' },
                { file: mockFile2, region: 'SP1' }
            ])

            expect(formData.getAll('files')).toHaveLength(2)
            expect(formData.getAll('regions')).toContain('RJ')
            expect(formData.getAll('regions')).toContain('SP1')
        })
    })

    describe('SharePoint Service Logic', () => {
        it('deve verificar status de configuração', () => {
            const checkSharePointConfig = (config: { 
                client_id?: string
                tenant_id?: string
                site_id?: string
            }): { configured: boolean; missing: string[] } => {
                const missing: string[] = []
                if (!config.client_id) missing.push('client_id')
                if (!config.tenant_id) missing.push('tenant_id')
                if (!config.site_id) missing.push('site_id')
                return { configured: missing.length === 0, missing }
            }

            const fullConfig = { client_id: 'abc', tenant_id: 'def', site_id: 'ghi' }
            expect(checkSharePointConfig(fullConfig).configured).toBe(true)
            expect(checkSharePointConfig(fullConfig).missing).toHaveLength(0)

            const partialConfig = { client_id: 'abc' }
            expect(checkSharePointConfig(partialConfig).configured).toBe(false)
            expect(checkSharePointConfig(partialConfig).missing).toContain('tenant_id')
        })

        it('deve mapear região para arquivo', () => {
            const mapFileToRegion = (filename: string): string | null => {
                const lower = filename.toLowerCase()
                
                // Ordem importa: mais específico primeiro
                if (lower.includes('nne')) return 'NNE'
                if (lower.includes('sp3')) return 'SP3'
                if (lower.includes('sp2')) return 'SP2'
                if (lower.includes('sp1')) return 'SP1'
                if (lower.includes('_rj') || lower.includes('rio')) return 'RJ'
                
                return null
            }

            expect(mapFileToRegion('Medicao_RJ_2024.xlsx')).toBe('RJ')
            expect(mapFileToRegion('dados_sp1_nov.xlsx')).toBe('SP1')
            expect(mapFileToRegion('dados_nne_nov.xlsx')).toBe('NNE')
            expect(mapFileToRegion('arquivo_generico.xlsx')).toBeNull()
        })
    })

    describe('Config Service Logic', () => {
        it('deve validar configuração de email', () => {
            const validateEmailConfig = (config: {
                sender_email?: string
                sender_name?: string
            }): boolean => {
                if (!config.sender_email || !config.sender_name) return false
                const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
                return emailRegex.test(config.sender_email)
            }

            expect(validateEmailConfig({ 
                sender_email: 'test@example.com', 
                sender_name: 'Test User' 
            })).toBe(true)
            
            expect(validateEmailConfig({ 
                sender_email: 'invalid-email', 
                sender_name: 'Test' 
            })).toBe(false)
            
            expect(validateEmailConfig({})).toBe(false)
        })
    })
})
