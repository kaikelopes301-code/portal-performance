/**
 * Testes para tipos e interfaces
 */
import { describe, it, expect } from 'vitest'
import type { Job, JobStatus } from './index'

describe('Types', () => {
    describe('Job', () => {
        it('deve aceitar job válido com campos obrigatórios', () => {
            const job: Job = {
                id: '1',
                filename: 'test.xlsx',
                status: 'pending',
                created_at: '2024-01-01T00:00:00Z'
            }

            expect(job.id).toBe('1')
            expect(job.status).toBe('pending')
        })

        it('deve aceitar job com região', () => {
            const job: Job = {
                id: '1',
                filename: 'test.xlsx',
                status: 'completed',
                region: 'RJ',
                created_at: '2024-01-01T00:00:00Z'
            }

            expect(job.region).toBe('RJ')
        })

        it('deve aceitar todos os status válidos', () => {
            const statuses: JobStatus[] = ['pending', 'processing', 'completed', 'failed']

            statuses.forEach(status => {
                const job: Job = {
                    id: '1',
                    filename: 'test.xlsx',
                    status,
                    created_at: '2024-01-01T00:00:00Z'
                }
                expect(job.status).toBe(status)
            })
        })

        it('deve aceitar campos opcionais', () => {
            const job: Job = {
                id: '1',
                filename: 'test.xlsx',
                status: 'completed',
                created_at: '2024-01-01T00:00:00Z',
                region: 'SP1',
                month_ref: '2024-11',
                updated_at: '2024-01-02T00:00:00Z',
                error_message: undefined,
                result_summary: {
                    row_count: 100,
                    unit_count: 5,
                    sum_valor_mensal_final: 50000
                }
            }

            expect(job.result_summary?.row_count).toBe(100)
        })
    })
})
