import { useEffect, useState } from 'react'
import { CheckCircle, Clock, AlertCircle, RefreshCw } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import Layout from '@/components/layout/Layout'
import { jobService } from '@/services'
import type { Job } from '@/types'

export default function ProcessPage() {
    const [jobs, setJobs] = useState<Job[]>([])
    const [loading, setLoading] = useState(true)

    const fetchJobs = async () => {
        try {
            const data = await jobService.list(20, 0)
            setJobs(data.jobs || [])
        } catch (error) {
            console.error('Failed to fetch jobs:', error)
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => {
        fetchJobs()
        const interval = setInterval(fetchJobs, 5000) // Poll a cada 5s
        return () => clearInterval(interval)
    }, [])

    const getStatusIcon = (status: string) => {
        switch (status) {
            case 'completed': return <CheckCircle className="h-5 w-5 text-green-500" />
            case 'processing': return <RefreshCw className="h-5 w-5 text-blue-500 animate-spin" />
            case 'failed': return <AlertCircle className="h-5 w-5 text-red-500" />
            default: return <Clock className="h-5 w-5 text-gray-400" />
        }
    }

    const getStatusLabel = (status: string) => {
        const labels: Record<string, string> = {
            pending: 'Pendente',
            processing: 'Processando',
            completed: 'Concluído',
            failed: 'Falhou'
        }
        return labels[status] || status
    }

    return (
        <Layout>
            <div className="space-y-6">
                <div className="flex justify-between items-center">
                    <div>
                        <h1 className="text-2xl font-bold text-gray-900">Processamento</h1>
                        <p className="mt-1 text-sm text-gray-500">
                            Acompanhe o status das planilhas enviadas.
                        </p>
                    </div>
                    <Button variant="outline" size="sm" onClick={fetchJobs}>
                        <RefreshCw className="h-4 w-4 mr-2" />
                        Atualizar
                    </Button>
                </div>

                <div className="grid gap-4">
                    {jobs.map((job) => (
                        <Card key={job.id}>
                            <CardContent className="p-6 flex items-center justify-between">
                                <div className="flex items-center space-x-4">
                                    <div className="p-2 bg-gray-100 rounded-full">
                                        {getStatusIcon(job.status)}
                                    </div>
                                    <div>
                                        <h3 className="text-sm font-medium text-gray-900">{job.filename}</h3>
                                        <p className="text-xs text-gray-500">
                                            Enviado em {new Date(job.created_at).toLocaleString()}
                                        </p>
                                    </div>
                                </div>

                                <div className="flex items-center space-x-6">
                                    {job.result_summary && (
                                        <div className="text-right hidden sm:block">
                                            <p className="text-sm font-medium text-gray-900">
                                                {job.result_summary.row_count} linhas
                                            </p>
                                            <p className="text-xs text-gray-500">
                                                Total: {new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(job.result_summary.sum_valor_mensal_final)}
                                            </p>
                                        </div>
                                    )}

                                    <div className={`px-3 py-1 rounded-full text-xs font-medium border
                    ${job.status === 'completed' ? 'bg-green-50 text-green-700 border-green-200' :
                                            job.status === 'failed' ? 'bg-red-50 text-red-700 border-red-200' :
                                                'bg-gray-50 text-gray-700 border-gray-200'}`}>
                                        {getStatusLabel(job.status)}
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                    ))}

                    {!loading && jobs.length === 0 && (
                        <div className="text-center py-12 text-gray-500">
                            Nenhum processamento encontrado.
                        </div>
                    )}
                </div>
            </div>
        </Layout>
    )
}
