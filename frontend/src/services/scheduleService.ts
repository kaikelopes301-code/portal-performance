// Service para operações de Agendamentos
import { api } from './api'
import type { Schedule, ScheduleListResponse, ScheduleCreateRequest } from '@/types'

export const scheduleService = {
    /**
     * Lista todos os agendamentos
     */
    list: () =>
        api.get<ScheduleListResponse>('/api/schedules/'),

    /**
     * Busca um agendamento específico
     */
    get: (scheduleId: string) =>
        api.get<Schedule>(`/api/schedules/${scheduleId}`),

    /**
     * Cria um novo agendamento
     */
    create: (data: ScheduleCreateRequest) =>
        api.post<Schedule>('/api/schedules/', data),

    /**
     * Atualiza um agendamento
     */
    update: (scheduleId: string, data: Partial<ScheduleCreateRequest>) =>
        api.put<Schedule>(`/api/schedules/${scheduleId}`, data),

    /**
     * Remove um agendamento
     */
    delete: (scheduleId: string) =>
        api.delete<{ message: string }>(`/api/schedules/${scheduleId}`),

    /**
     * Pausa um agendamento
     */
    pause: (scheduleId: string) =>
        api.post<Schedule>(`/api/schedules/${scheduleId}/pause`),

    /**
     * Retoma um agendamento pausado
     */
    resume: (scheduleId: string) =>
        api.post<Schedule>(`/api/schedules/${scheduleId}/resume`),

    /**
     * Executa um agendamento manualmente
     */
    runNow: (scheduleId: string) =>
        api.post<{ message: string; job_id?: string }>(`/api/schedules/${scheduleId}/run`),

    /**
     * Lista execuções de um agendamento
     */
    getExecutions: (scheduleId: string) =>
        api.get<{ executions: unknown[] }>(`/api/schedules/${scheduleId}/executions`),

    /**
     * Lista agendamentos pendentes (próximos a executar)
     */
    getPending: () =>
        api.get<{ schedules: Schedule[] }>('/api/schedules/pending'),
}

export default scheduleService
