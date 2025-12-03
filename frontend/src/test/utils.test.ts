/**
 * Testes para utilitários
 */
import { describe, it, expect } from 'vitest'

// Funções utilitárias que podem ser testadas
describe('Utilities', () => {
    describe('File Validation', () => {
        const validateFile = (file: { name: string; size: number }): { valid: boolean; error?: string } => {
            const maxSize = 50 * 1024 * 1024
            if (file.size > maxSize) {
                return { valid: false, error: 'Arquivo muito grande. Máximo: 50MB' }
            }
            
            const validExtensions = ['.xlsx', '.xls']
            const hasValidExt = validExtensions.some(ext => file.name.toLowerCase().endsWith(ext))
            if (!hasValidExt) {
                return { valid: false, error: 'Formato inválido. Use arquivos .xlsx ou .xls' }
            }
            
            if (file.name.startsWith('~$')) {
                return { valid: false, error: 'Este é um arquivo temporário do Excel.' }
            }
            
            return { valid: true }
        }

        it('deve aceitar arquivo xlsx válido', () => {
            const result = validateFile({ name: 'test.xlsx', size: 1024 })
            expect(result.valid).toBe(true)
        })

        it('deve aceitar arquivo xls válido', () => {
            const result = validateFile({ name: 'test.xls', size: 1024 })
            expect(result.valid).toBe(true)
        })

        it('deve rejeitar arquivo muito grande', () => {
            const result = validateFile({ name: 'test.xlsx', size: 60 * 1024 * 1024 })
            expect(result.valid).toBe(false)
            expect(result.error).toContain('Máximo')
        })

        it('deve rejeitar extensão inválida', () => {
            const result = validateFile({ name: 'test.txt', size: 1024 })
            expect(result.valid).toBe(false)
            expect(result.error).toContain('Formato inválido')
        })

        it('deve rejeitar arquivo temporário do Excel', () => {
            const result = validateFile({ name: '~$test.xlsx', size: 1024 })
            expect(result.valid).toBe(false)
            expect(result.error).toContain('temporário')
        })
    })

    describe('Region Detection', () => {
        const detectRegion = (filename: string): string => {
            const upperName = filename.toUpperCase()
            if (upperName.includes('_RJ') || upperName.includes(' RJ') || upperName.includes('-RJ')) return 'RJ'
            if (upperName.includes('_SP1') || upperName.includes(' SP1') || upperName.includes('-SP1')) return 'SP1'
            if (upperName.includes('_SP2') || upperName.includes(' SP2') || upperName.includes('-SP2')) return 'SP2'
            if (upperName.includes('_SP3') || upperName.includes(' SP3') || upperName.includes('-SP3')) return 'SP3'
            if (upperName.includes('_NNE') || upperName.includes(' NNE') || upperName.includes('-NNE') || 
                upperName.includes('NORTE') || upperName.includes('NORDESTE')) return 'NNE'
            return ''
        }

        it('deve detectar RJ no nome do arquivo', () => {
            expect(detectRegion('Medicao_RJ_2024.xlsx')).toBe('RJ')
            expect(detectRegion('Planilha RJ.xlsx')).toBe('RJ')
            expect(detectRegion('data-RJ-nov.xlsx')).toBe('RJ')
        })

        it('deve detectar SP1 no nome do arquivo', () => {
            expect(detectRegion('Medicao_SP1_2024.xlsx')).toBe('SP1')
            expect(detectRegion('Planilha SP1.xlsx')).toBe('SP1')
        })

        it('deve detectar SP2 no nome do arquivo', () => {
            expect(detectRegion('Medicao_SP2_2024.xlsx')).toBe('SP2')
        })

        it('deve detectar SP3 no nome do arquivo', () => {
            expect(detectRegion('Medicao_SP3_2024.xlsx')).toBe('SP3')
        })

        it('deve detectar NNE no nome do arquivo', () => {
            expect(detectRegion('Medicao_NNE_2024.xlsx')).toBe('NNE')
            expect(detectRegion('Medicao_Norte_2024.xlsx')).toBe('NNE')
            expect(detectRegion('Medicao_Nordeste_2024.xlsx')).toBe('NNE')
        })

        it('deve retornar vazio para arquivos sem região', () => {
            expect(detectRegion('Medicao_2024.xlsx')).toBe('')
            expect(detectRegion('Planilha.xlsx')).toBe('')
        })
    })

    describe('Date Formatting', () => {
        const formatDate = (dateStr: string): string => {
            const date = new Date(dateStr)
            return date.toLocaleDateString('pt-BR', {
                day: '2-digit',
                month: '2-digit',
                year: 'numeric'
            })
        }

        it('deve formatar data ISO corretamente', () => {
            const result = formatDate('2024-11-15T10:30:00Z')
            expect(result).toMatch(/15\/11\/2024/)
        })
    })

    describe('File Size Formatting', () => {
        const formatFileSize = (bytes: number): string => {
            if (bytes < 1024) return `${bytes} B`
            if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
            return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
        }

        it('deve formatar bytes', () => {
            expect(formatFileSize(500)).toBe('500 B')
        })

        it('deve formatar kilobytes', () => {
            expect(formatFileSize(1500)).toBe('1.5 KB')
        })

        it('deve formatar megabytes', () => {
            expect(formatFileSize(1500000)).toBe('1.4 MB')
        })
    })
})
