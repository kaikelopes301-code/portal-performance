import { useEffect, useState, useCallback } from 'react'
import { 
    Mail, Calendar, Search, Filter, Trash2, RefreshCw, 
    ChevronLeft, ChevronRight, CheckCircle, XCircle, Clock,
    BarChart3, Building2, AlertTriangle, TestTube2, Send, MapPin
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import Layout from '@/components/layout/Layout'
import { logService, type LogFilters } from '@/services/logService'
import { useToast } from '@/components/ui/toast'
import { cn } from '@/utils/cn'
import type { EmailLog, LogStats } from '@/types'

const ITEMS_PER_PAGE = 20
const REGIONS = ['RJ', 'SP1', 'SP2', 'SP3', 'NNE']

export default function HistoryPage() {
    const { success, error: errorToast } = useToast()
    
    // Data state
    const [logs, setLogs] = useState<EmailLog[]>([])
    const [stats, setStats] = useState<LogStats | null>(null)
    const [loading, setLoading] = useState(true)
    const [total, setTotal] = useState(0)
    
    // Pagination state
    const [page, setPage] = useState(0)
    
    // Filter state
    const [showFilters, setShowFilters] = useState(false)
    const [searchTerm, setSearchTerm] = useState('')
    const [statusFilter, setStatusFilter] = useState<string>('')
    const [typeFilter, setTypeFilter] = useState<string>('')  // 'dry_run', 'real', ''
    const [regionFilter, setRegionFilter] = useState<string>('')
    const [dateFrom, setDateFrom] = useState('')
    const [dateTo, setDateTo] = useState('')
    
    // Cleanup modal
    const [showCleanupModal, setShowCleanupModal] = useState(false)
    const [cleanupDays, setCleanupDays] = useState(90)
    const [cleanupLoading, setCleanupLoading] = useState(false)

    const fetchLogs = useCallback(async () => {
        setLoading(true)
        try {
            const activeFilters: LogFilters = {}
            if (searchTerm) activeFilters.unit_name = searchTerm
            if (statusFilter) activeFilters.status = statusFilter as 'sent' | 'failed' | 'queued'
            if (dateFrom) activeFilters.date_from = dateFrom
            if (dateTo) activeFilters.date_to = dateTo
            if (regionFilter) activeFilters.region = regionFilter
            if (typeFilter === 'dry_run') activeFilters.is_dry_run = true
            if (typeFilter === 'real') activeFilters.is_dry_run = false
            
            const response = await logService.list(ITEMS_PER_PAGE, page * ITEMS_PER_PAGE, activeFilters)
            setLogs(response.items || [])
            setTotal(response.total || 0)
        } catch (err) {
            console.error('Failed to fetch logs:', err)
            errorToast('Erro ao carregar', 'Não foi possível carregar o histórico')
            setLogs([])
        } finally {
            setLoading(false)
        }
    }, [page, searchTerm, statusFilter, typeFilter, regionFilter, dateFrom, dateTo, errorToast])

    const fetchStats = useCallback(async () => {
        try {
            const data = await logService.getStats()
            setStats(data)
        } catch (err) {
            console.error('Failed to fetch stats:', err)
        }
    }, [])

    useEffect(() => {
        fetchLogs()
    }, [fetchLogs])

    useEffect(() => {
        fetchStats()
    }, [fetchStats])

    const handleSearch = () => {
        setPage(0)
        fetchLogs()
    }

    const handleClearFilters = () => {
        setSearchTerm('')
        setStatusFilter('')
        setTypeFilter('')
        setRegionFilter('')
        setDateFrom('')
        setDateTo('')
        setPage(0)
    }

    const handleDeleteLog = async (logId: number) => {
        if (!confirm('Tem certeza que deseja remover este registro?')) return
        
        try {
            await logService.delete(logId)
            success('Removido', 'Registro excluído com sucesso')
            fetchLogs()
            fetchStats()
        } catch (err) {
            errorToast('Erro', 'Não foi possível remover o registro')
        }
    }

    const handleCleanup = async () => {
        setCleanupLoading(true)
        try {
            const result = await logService.cleanup(cleanupDays)
            success('Limpeza concluída', result.message)
            setShowCleanupModal(false)
            fetchLogs()
            fetchStats()
        } catch (err) {
            errorToast('Erro', 'Não foi possível realizar a limpeza')
        } finally {
            setCleanupLoading(false)
        }
    }

    const totalPages = Math.ceil(total / ITEMS_PER_PAGE)

    const getStatusIcon = (status: string) => {
        switch (status) {
            case 'sent': return <CheckCircle className="h-4 w-4 text-green-500" />
            case 'failed': return <XCircle className="h-4 w-4 text-red-500" />
            default: return <Clock className="h-4 w-4 text-yellow-500" />
        }
    }

    const getStatusLabel = (status: string) => {
        switch (status) {
            case 'sent': return 'Enviado'
            case 'failed': return 'Falha'
            case 'queued': return 'Na Fila'
            default: return status
        }
    }

    return (
        <Layout>
            <div className="space-y-6 animate-fade-in-up">
                {/* Header */}
                <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                    <div>
                        <h1 className="text-2xl font-bold text-[#2F4F71]">Histórico de Envios</h1>
                        <p className="mt-1 text-sm text-gray-500">
                            Registro de todos os e-mails disparados pelo sistema.
                        </p>
                    </div>
                    <div className="flex items-center gap-2">
                        <Button 
                            variant="outline" 
                            size="sm" 
                            onClick={() => setShowFilters(!showFilters)}
                            className={cn(showFilters && "bg-blue-50 border-blue-300")}
                        >
                            <Filter className="h-4 w-4 mr-2" />
                            Filtros
                        </Button>
                        <Button 
                            variant="outline" 
                            size="sm" 
                            onClick={() => setShowCleanupModal(true)}
                            className="text-red-600 hover:bg-red-50 hover:border-red-300"
                        >
                            <Trash2 className="h-4 w-4 mr-2" />
                            Limpeza
                        </Button>
                        <Button variant="outline" size="sm" onClick={() => { fetchLogs(); fetchStats() }}>
                            <RefreshCw className={cn("h-4 w-4 mr-2", loading && "animate-spin")} />
                            Atualizar
                        </Button>
                    </div>
                </div>

                {/* Stats Cards */}
                {stats && (
                    <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-4">
                        <div className="glass-card p-4 flex items-center gap-3">
                            <div className="p-2 rounded-lg bg-blue-100">
                                <BarChart3 className="h-5 w-5 text-blue-600" />
                            </div>
                            <div>
                                <p className="text-xs text-gray-500">Total</p>
                                <p className="text-xl font-bold text-[#2F4F71]">{stats.total}</p>
                            </div>
                        </div>
                        <div className="glass-card p-4 flex items-center gap-3">
                            <div className="p-2 rounded-lg bg-green-100">
                                <Send className="h-5 w-5 text-green-600" />
                            </div>
                            <div>
                                <p className="text-xs text-gray-500">Envios Reais</p>
                                <p className="text-xl font-bold text-green-600">{stats.real_sends}</p>
                            </div>
                        </div>
                        <div className="glass-card p-4 flex items-center gap-3">
                            <div className="p-2 rounded-lg bg-orange-100">
                                <TestTube2 className="h-5 w-5 text-orange-600" />
                            </div>
                            <div>
                                <p className="text-xs text-gray-500">Dry Runs</p>
                                <p className="text-xl font-bold text-orange-600">{stats.dry_runs}</p>
                            </div>
                        </div>
                        <div className="glass-card p-4 flex items-center gap-3">
                            <div className="p-2 rounded-lg bg-emerald-100">
                                <CheckCircle className="h-5 w-5 text-emerald-600" />
                            </div>
                            <div>
                                <p className="text-xs text-gray-500">Enviados</p>
                                <p className="text-xl font-bold text-emerald-600">{stats.sent}</p>
                            </div>
                        </div>
                        <div className="glass-card p-4 flex items-center gap-3">
                            <div className="p-2 rounded-lg bg-red-100">
                                <XCircle className="h-5 w-5 text-red-600" />
                            </div>
                            <div>
                                <p className="text-xs text-gray-500">Falhas</p>
                                <p className="text-xl font-bold text-red-600">{stats.failed}</p>
                            </div>
                        </div>
                        <div className="glass-card p-4 flex items-center gap-3">
                            <div className="p-2 rounded-lg bg-purple-100">
                                <Calendar className="h-5 w-5 text-purple-600" />
                            </div>
                            <div>
                                <p className="text-xs text-gray-500">Últimos 7 dias</p>
                                <p className="text-xl font-bold text-purple-600">{stats.recent_7_days}</p>
                            </div>
                        </div>
                        <div className="glass-card p-4 flex items-center gap-3">
                            <div className="p-2 rounded-lg bg-amber-100">
                                <Building2 className="h-5 w-5 text-amber-600" />
                            </div>
                            <div>
                                <p className="text-xs text-gray-500">Unidades</p>
                                <p className="text-xl font-bold text-amber-600">{stats.unique_units}</p>
                            </div>
                        </div>
                    </div>
                )}

                {/* Filters Panel */}
                {showFilters && (
                    <div className="glass-card p-4 animate-fade-in-up">
                        <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Buscar Unidade</label>
                                <div className="relative">
                                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                                    <input
                                        type="text"
                                        placeholder="Nome da unidade..."
                                        value={searchTerm}
                                        onChange={(e) => setSearchTerm(e.target.value)}
                                        onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                                        className="w-full pl-10 pr-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                    />
                                </div>
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Tipo</label>
                                <select
                                    value={typeFilter}
                                    onChange={(e) => setTypeFilter(e.target.value)}
                                    className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                >
                                    <option value="">Todos</option>
                                    <option value="real">🚀 Envio Real</option>
                                    <option value="dry_run">🧪 Dry Run (Teste)</option>
                                </select>
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
                                <select
                                    value={statusFilter}
                                    onChange={(e) => setStatusFilter(e.target.value)}
                                    className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                >
                                    <option value="">Todos</option>
                                    <option value="sent">Enviados</option>
                                    <option value="failed">Falhas</option>
                                    <option value="queued">Na Fila</option>
                                </select>
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Região</label>
                                <select
                                    value={regionFilter}
                                    onChange={(e) => setRegionFilter(e.target.value)}
                                    className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                >
                                    <option value="">Todas</option>
                                    {REGIONS.map(r => (
                                        <option key={r} value={r}>{r}</option>
                                    ))}
                                </select>
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Data Inicial</label>
                                <input
                                    type="date"
                                    value={dateFrom}
                                    onChange={(e) => setDateFrom(e.target.value)}
                                    className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Data Final</label>
                                <input
                                    type="date"
                                    value={dateTo}
                                    onChange={(e) => setDateTo(e.target.value)}
                                    className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                />
                            </div>
                        </div>
                        <div className="flex justify-end gap-2 mt-4">
                            <Button variant="ghost" size="sm" onClick={handleClearFilters}>
                                Limpar Filtros
                            </Button>
                            <Button size="sm" onClick={handleSearch}>
                                <Search className="h-4 w-4 mr-2" />
                                Aplicar
                            </Button>
                        </div>
                    </div>
                )}

                {/* Logs List */}
                <div className="space-y-3">
                    {loading ? (
                        <div className="flex items-center justify-center py-12">
                            <div className="flex flex-col items-center gap-4">
                                <RefreshCw className="h-8 w-8 animate-spin text-blue-500" />
                                <span className="text-gray-500">Carregando histórico...</span>
                            </div>
                        </div>
                    ) : logs.length === 0 ? (
                        <div className="text-center py-16">
                            <Mail className="mx-auto h-12 w-12 text-gray-300" />
                            <h3 className="mt-4 text-lg font-medium text-gray-900">Nenhum registro encontrado</h3>
                            <p className="mt-2 text-sm text-gray-500">
                                {searchTerm || statusFilter || dateFrom || dateTo
                                    ? 'Tente ajustar os filtros de busca.'
                                    : 'Os envios de e-mail aparecerão aqui.'}
                            </p>
                        </div>
                    ) : (
                        logs.map((log) => (
                            <div 
                                key={log.id} 
                                className="glass-card p-4 hover:shadow-lg transition-shadow group"
                            >
                                <div className="flex items-start justify-between gap-4">
                                    <div className="flex items-start gap-4 flex-1">
                                        <div className={cn(
                                            "p-2.5 rounded-xl",
                                            log.is_dry_run && "bg-orange-100",
                                            !log.is_dry_run && log.status === 'sent' && "bg-green-100",
                                            !log.is_dry_run && log.status === 'failed' && "bg-red-100",
                                            !log.is_dry_run && log.status !== 'sent' && log.status !== 'failed' && "bg-yellow-100"
                                        )}>
                                            {log.is_dry_run ? (
                                                <TestTube2 className="h-5 w-5 text-orange-600" />
                                            ) : (
                                                <Mail className={cn(
                                                    "h-5 w-5",
                                                    log.status === 'sent' && "text-green-600",
                                                    log.status === 'failed' && "text-red-600",
                                                    log.status !== 'sent' && log.status !== 'failed' && "text-yellow-600"
                                                )} />
                                            )}
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <div className="flex items-center gap-2">
                                                <h3 className="text-sm font-semibold text-gray-900 truncate">{log.subject}</h3>
                                                {log.is_dry_run && (
                                                    <span className="px-2 py-0.5 text-xs font-medium bg-orange-100 text-orange-700 rounded-full border border-orange-200">
                                                        TESTE
                                                    </span>
                                                )}
                                            </div>
                                            <div className="mt-1 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-gray-500">
                                                <span className="flex items-center">
                                                    <Calendar className="mr-1 h-3.5 w-3.5" />
                                                    {log.sent_at ? new Date(log.sent_at).toLocaleString('pt-BR') : '-'}
                                                </span>
                                                <span className="flex items-center">
                                                    <Building2 className="mr-1 h-3.5 w-3.5" />
                                                    {log.unit_name}
                                                </span>
                                                {log.region && (
                                                    <span className="flex items-center">
                                                        <MapPin className="mr-1 h-3.5 w-3.5" />
                                                        {log.region}
                                                    </span>
                                                )}
                                                <span className="font-medium text-blue-600">Ref: {log.month_ref}</span>
                                            </div>
                                            <div className="mt-2 text-xs text-gray-500 truncate">
                                                <span className="font-medium">Para:</span>{' '}
                                                {log.recipient_list ? log.recipient_list.split(';').slice(0, 3).join(', ') : '-'}
                                                {log.recipient_list && log.recipient_list.split(';').length > 3 && '...'}
                                            </div>
                                            {log.error_message && (
                                                <div className="mt-2 text-xs text-red-600 flex items-center gap-1">
                                                    <AlertTriangle className="h-3 w-3" />
                                                    {log.error_message}
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                    
                                    <div className="flex items-center gap-3">
                                        {/* Badge de tipo */}
                                        <div className={cn(
                                            "px-2 py-1 rounded-full text-xs font-medium",
                                            log.is_dry_run 
                                                ? "bg-orange-50 text-orange-700 border border-orange-200"
                                                : "bg-green-50 text-green-700 border border-green-200"
                                        )}>
                                            {log.is_dry_run ? '🧪 Dry Run' : '🚀 Enviado'}
                                        </div>
                                        {/* Badge de status */}
                                        <div className={cn(
                                            "px-3 py-1 rounded-full text-xs font-medium flex items-center gap-1.5",
                                            log.status === 'sent' && "bg-green-50 text-green-700 border border-green-200",
                                            log.status === 'failed' && "bg-red-50 text-red-700 border border-red-200",
                                            log.status !== 'sent' && log.status !== 'failed' && "bg-yellow-50 text-yellow-700 border border-yellow-200"
                                        )}>
                                            {getStatusIcon(log.status)}
                                            {getStatusLabel(log.status)}
                                        </div>
                                        <button
                                            onClick={() => handleDeleteLog(log.id)}
                                            className="p-1.5 rounded-lg text-gray-400 hover:text-red-500 hover:bg-red-50 opacity-0 group-hover:opacity-100 transition-all"
                                            title="Remover registro"
                                        >
                                            <Trash2 className="h-4 w-4" />
                                        </button>
                                    </div>
                                </div>
                            </div>
                        ))
                    )}
                </div>

                {/* Pagination */}
                {totalPages > 1 && (
                    <div className="flex items-center justify-between pt-4 border-t border-gray-200">
                        <span className="text-sm text-gray-500">
                            Mostrando {page * ITEMS_PER_PAGE + 1} - {Math.min((page + 1) * ITEMS_PER_PAGE, total)} de {total} registros
                        </span>
                        <div className="flex items-center gap-2">
                            <Button
                                variant="outline"
                                size="sm"
                                onClick={() => setPage(p => Math.max(0, p - 1))}
                                disabled={page === 0}
                            >
                                <ChevronLeft className="h-4 w-4" />
                            </Button>
                            <span className="text-sm font-medium px-3">
                                {page + 1} / {totalPages}
                            </span>
                            <Button
                                variant="outline"
                                size="sm"
                                onClick={() => setPage(p => Math.min(totalPages - 1, p + 1))}
                                disabled={page >= totalPages - 1}
                            >
                                <ChevronRight className="h-4 w-4" />
                            </Button>
                        </div>
                    </div>
                )}

                {/* Cleanup Modal */}
                {showCleanupModal && (
                    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm animate-fade-in">
                        <div className="bg-white rounded-2xl shadow-xl p-6 w-full max-w-md mx-4 animate-fade-in-up">
                            <div className="flex items-center gap-3 mb-4">
                                <div className="p-2 rounded-lg bg-red-100">
                                    <Trash2 className="h-5 w-5 text-red-600" />
                                </div>
                                <h2 className="text-lg font-semibold text-gray-900">Limpeza de Histórico</h2>
                            </div>
                            
                            <p className="text-sm text-gray-600 mb-4">
                                Esta ação removerá permanentemente todos os registros de log mais antigos que o período especificado.
                            </p>
                            
                            <div className="mb-6">
                                <label className="block text-sm font-medium text-gray-700 mb-2">
                                    Remover registros mais antigos que:
                                </label>
                                <select
                                    value={cleanupDays}
                                    onChange={(e) => setCleanupDays(Number(e.target.value))}
                                    className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
                                >
                                    <option value={7}>7 dias</option>
                                    <option value={30}>30 dias</option>
                                    <option value={60}>60 dias</option>
                                    <option value={90}>90 dias</option>
                                    <option value={180}>180 dias</option>
                                    <option value={365}>1 ano</option>
                                </select>
                            </div>
                            
                            <div className="flex justify-end gap-3">
                                <Button 
                                    variant="ghost" 
                                    onClick={() => setShowCleanupModal(false)}
                                    disabled={cleanupLoading}
                                >
                                    Cancelar
                                </Button>
                                <Button 
                                    onClick={handleCleanup}
                                    disabled={cleanupLoading}
                                    className="bg-red-600 hover:bg-red-700 text-white"
                                >
                                    {cleanupLoading ? (
                                        <>
                                            <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                                            Limpando...
                                        </>
                                    ) : (
                                        <>
                                            <Trash2 className="h-4 w-4 mr-2" />
                                            Confirmar Limpeza
                                        </>
                                    )}
                                </Button>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </Layout>
    )
}
