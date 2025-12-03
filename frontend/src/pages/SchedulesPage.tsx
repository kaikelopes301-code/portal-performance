import { useEffect, useState } from 'react'
import { Calendar, Clock, Play, Pause, Plus, Trash2, RefreshCw } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import Layout from '@/components/layout/Layout'
import { scheduleService } from '@/services'
import type { Schedule, ScheduleCreateRequest, ScheduleFrequency } from '@/types'

export default function SchedulesPage() {
    const [schedules, setSchedules] = useState<Schedule[]>([])
    const [loading, setLoading] = useState(true)
    const [showForm, setShowForm] = useState(false)
    const [formData, setFormData] = useState<ScheduleCreateRequest>({
        name: '',
        description: '',
        region: '',
        units: [],
        frequency: 'monthly',
        day_of_month: 1,
        time: '08:00',
        auto_send_email: false,
    })
    const [unitsInput, setUnitsInput] = useState('')

    const fetchSchedules = async () => {
        try {
            const data = await scheduleService.list()
            setSchedules(data.schedules)
        } catch (error) {
            console.error('Failed to fetch schedules:', error)
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => {
        fetchSchedules()
    }, [])

    const handleToggleStatus = async (schedule: Schedule) => {
        try {
            if (schedule.status === 'active') {
                await scheduleService.pause(schedule.id)
            } else {
                await scheduleService.resume(schedule.id)
            }
            fetchSchedules()
        } catch (error) {
            console.error('Failed to toggle schedule:', error)
            alert('Erro ao alterar status do agendamento')
        }
    }

    const handleRunNow = async (scheduleId: string) => {
        try {
            await scheduleService.runNow(scheduleId)
            alert('Execução iniciada!')
            fetchSchedules()
        } catch (error) {
            console.error('Failed to run schedule:', error)
            alert('Erro ao executar agendamento')
        }
    }

    const handleDelete = async (scheduleId: string) => {
        if (!confirm('Tem certeza que deseja excluir este agendamento?')) return

        try {
            await scheduleService.delete(scheduleId)
            fetchSchedules()
        } catch (error) {
            console.error('Failed to delete schedule:', error)
            alert('Erro ao excluir agendamento')
        }
    }

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        try {
            const data = {
                ...formData,
                units: unitsInput.split(',').map(u => u.trim()).filter(Boolean),
            }
            await scheduleService.create(data)
            setShowForm(false)
            setFormData({
                name: '',
                description: '',
                region: '',
                units: [],
                frequency: 'monthly',
                day_of_month: 1,
                time: '08:00',
                auto_send_email: false,
            })
            setUnitsInput('')
            fetchSchedules()
        } catch (error) {
            console.error('Failed to create schedule:', error)
            alert('Erro ao criar agendamento')
        }
    }

    const getFrequencyLabel = (frequency: ScheduleFrequency) => {
        const labels: Record<ScheduleFrequency, string> = {
            daily: 'Diário',
            weekly: 'Semanal',
            monthly: 'Mensal',
        }
        return labels[frequency]
    }

    const formatNextRun = (nextRun?: string) => {
        if (!nextRun) return 'Não agendado'
        return new Date(nextRun).toLocaleString('pt-BR')
    }

    return (
        <Layout>
            <div className="space-y-6">
                <div className="flex justify-between items-center">
                    <div>
                        <h1 className="text-2xl font-bold text-gray-900">Agendamentos</h1>
                        <p className="mt-1 text-sm text-gray-500">
                            Configure execuções automáticas de processamento.
                        </p>
                    </div>
                    <div className="flex space-x-2">
                        <Button variant="outline" size="sm" onClick={fetchSchedules}>
                            <RefreshCw className="h-4 w-4 mr-2" />
                            Atualizar
                        </Button>
                        <Button onClick={() => setShowForm(!showForm)}>
                            <Plus className="h-4 w-4 mr-2" />
                            Novo Agendamento
                        </Button>
                    </div>
                </div>

                {/* Formulário de Criação */}
                {showForm && (
                    <Card>
                        <CardHeader>
                            <CardTitle>Novo Agendamento</CardTitle>
                            <CardDescription>
                                Preencha os dados para criar um agendamento automático.
                            </CardDescription>
                        </CardHeader>
                        <CardContent>
                            <form onSubmit={handleSubmit} className="space-y-4">
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    <div className="space-y-2">
                                        <label className="text-sm font-medium text-gray-700">Nome</label>
                                        <Input
                                            value={formData.name}
                                            onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                                            placeholder="Ex: Medição Mensal Sul"
                                            required
                                        />
                                    </div>

                                    <div className="space-y-2">
                                        <label className="text-sm font-medium text-gray-700">Região</label>
                                        <Input
                                            value={formData.region}
                                            onChange={(e) => setFormData(prev => ({ ...prev, region: e.target.value }))}
                                            placeholder="Ex: sudeste, sul, nordeste"
                                            required
                                        />
                                    </div>

                                    <div className="space-y-2 md:col-span-2">
                                        <label className="text-sm font-medium text-gray-700">Unidades</label>
                                        <Input
                                            value={unitsInput}
                                            onChange={(e) => setUnitsInput(e.target.value)}
                                            placeholder="Shopping Leblon, Norte Shopping, Carioca Shopping"
                                        />
                                        <p className="text-xs text-gray-500">Separe por vírgulas</p>
                                    </div>

                                    <div className="space-y-2">
                                        <label className="text-sm font-medium text-gray-700">Frequência</label>
                                        <select
                                            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                                            value={formData.frequency}
                                            onChange={(e) => setFormData(prev => ({
                                                ...prev,
                                                frequency: e.target.value as ScheduleFrequency
                                            }))}
                                        >
                                            <option value="daily">Diário</option>
                                            <option value="weekly">Semanal</option>
                                            <option value="monthly">Mensal</option>
                                        </select>
                                    </div>

                                    {formData.frequency === 'monthly' && (
                                        <div className="space-y-2">
                                            <label className="text-sm font-medium text-gray-700">Dia do Mês</label>
                                            <Input
                                                type="number"
                                                min={1}
                                                max={28}
                                                value={formData.day_of_month || 1}
                                                onChange={(e) => setFormData(prev => ({
                                                    ...prev,
                                                    day_of_month: parseInt(e.target.value)
                                                }))}
                                            />
                                        </div>
                                    )}

                                    {formData.frequency === 'weekly' && (
                                        <div className="space-y-2">
                                            <label className="text-sm font-medium text-gray-700">Dia da Semana</label>
                                            <select
                                                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                                                value={formData.day_of_week || 0}
                                                onChange={(e) => setFormData(prev => ({
                                                    ...prev,
                                                    day_of_week: parseInt(e.target.value)
                                                }))}
                                            >
                                                <option value={0}>Segunda</option>
                                                <option value={1}>Terça</option>
                                                <option value={2}>Quarta</option>
                                                <option value={3}>Quinta</option>
                                                <option value={4}>Sexta</option>
                                                <option value={5}>Sábado</option>
                                                <option value={6}>Domingo</option>
                                            </select>
                                        </div>
                                    )}

                                    <div className="space-y-2">
                                        <label className="text-sm font-medium text-gray-700">Horário</label>
                                        <Input
                                            type="time"
                                            value={formData.time}
                                            onChange={(e) => setFormData(prev => ({ ...prev, time: e.target.value }))}
                                        />
                                    </div>

                                    <div className="space-y-2 flex items-center">
                                        <label className="flex items-center space-x-2 cursor-pointer">
                                            <input
                                                type="checkbox"
                                                checked={formData.auto_send_email}
                                                onChange={(e) => setFormData(prev => ({
                                                    ...prev,
                                                    auto_send_email: e.target.checked
                                                }))}
                                                className="rounded border-gray-300"
                                            />
                                            <span className="text-sm text-gray-700">Enviar e-mail automaticamente</span>
                                        </label>
                                    </div>
                                </div>

                                <div className="flex justify-end space-x-2 pt-4">
                                    <Button type="button" variant="outline" onClick={() => setShowForm(false)}>
                                        Cancelar
                                    </Button>
                                    <Button type="submit">
                                        Criar Agendamento
                                    </Button>
                                </div>
                            </form>
                        </CardContent>
                    </Card>
                )}

                {/* Lista de Agendamentos */}
                <div className="grid gap-4">
                    {loading ? (
                        <div className="text-center py-12 text-gray-500">Carregando...</div>
                    ) : schedules.length === 0 ? (
                        <div className="text-center py-12 text-gray-500">
                            Nenhum agendamento encontrado.
                        </div>
                    ) : (
                        schedules.map((schedule) => (
                            <Card key={schedule.id}>
                                <CardContent className="p-6">
                                    <div className="flex items-start justify-between">
                                        <div className="flex items-start space-x-4">
                                            <div className={`p-2 rounded-full ${schedule.status === 'active' ? 'bg-green-100' : 'bg-gray-100'
                                                }`}>
                                                <Calendar className={`h-5 w-5 ${schedule.status === 'active' ? 'text-green-600' : 'text-gray-400'
                                                    }`} />
                                            </div>
                                            <div>
                                                <h3 className="text-sm font-medium text-gray-900">{schedule.name}</h3>
                                                {schedule.description && (
                                                    <p className="text-xs text-gray-500 mt-1">{schedule.description}</p>
                                                )}
                                                <div className="mt-2 flex flex-wrap items-center gap-4 text-xs text-gray-500">
                                                    <span className="flex items-center">
                                                        <Clock className="mr-1.5 h-3.5 w-3.5" />
                                                        {getFrequencyLabel(schedule.frequency)} às {schedule.time}
                                                    </span>
                                                    <span>Região: {schedule.region}</span>
                                                    <span>{schedule.units.length} unidade(s)</span>
                                                    <span>Execuções: {schedule.run_count}</span>
                                                </div>
                                                <div className="mt-2 text-xs text-gray-500">
                                                    <span className="font-medium">Próxima execução:</span>{' '}
                                                    {formatNextRun(schedule.next_run)}
                                                </div>
                                            </div>
                                        </div>

                                        <div className="flex items-center space-x-2">
                                            <div className={`px-2.5 py-0.5 rounded-full text-xs font-medium border ${schedule.status === 'active'
                                                    ? 'bg-green-50 text-green-700 border-green-200'
                                                    : 'bg-gray-50 text-gray-700 border-gray-200'
                                                }`}>
                                                {schedule.status === 'active' ? 'Ativo' : 'Pausado'}
                                            </div>
                                        </div>
                                    </div>

                                    <div className="mt-4 flex items-center space-x-2 border-t pt-4">
                                        <Button
                                            variant="outline"
                                            size="sm"
                                            onClick={() => handleToggleStatus(schedule)}
                                        >
                                            {schedule.status === 'active' ? (
                                                <>
                                                    <Pause className="h-4 w-4 mr-1" />
                                                    Pausar
                                                </>
                                            ) : (
                                                <>
                                                    <Play className="h-4 w-4 mr-1" />
                                                    Ativar
                                                </>
                                            )}
                                        </Button>

                                        <Button
                                            variant="outline"
                                            size="sm"
                                            onClick={() => handleRunNow(schedule.id)}
                                        >
                                            <Play className="h-4 w-4 mr-1" />
                                            Executar Agora
                                        </Button>

                                        <Button
                                            variant="outline"
                                            size="sm"
                                            className="text-red-600 hover:text-red-700 hover:bg-red-50"
                                            onClick={() => handleDelete(schedule.id)}
                                        >
                                            <Trash2 className="h-4 w-4 mr-1" />
                                            Excluir
                                        </Button>
                                    </div>
                                </CardContent>
                            </Card>
                        ))
                    )}
                </div>
            </div>
        </Layout>
    )
}
