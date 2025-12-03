import { useState, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { 
    Send, ChevronRight, ChevronDown, CheckCircle2, Loader2, AlertCircle, 
    Building2, FileText, Play, Eye, Zap, Calendar, Users, 
    CheckCheck, XCircle, RotateCcw, Sparkles
} from 'lucide-react'
import Layout from '@/components/layout/Layout'
import { useToast } from '@/components/ui/toast'
import { cn } from '@/utils/cn'
import { REGIONS_DATA as UNITS_DATA, TOTAL_UNITS, Unit as UnitType, Region as RegionType } from '@/data/units'
import { api } from '@/services'
import config from '@/config'

interface ExecuteResponse {
    success: boolean
    unit: string
    region: string
    month: string
    html_path?: string
    preview_url?: string
    rows_count: number
    emails_found: string[]
    emails_sent_to: string[]
    summary: Record<string, unknown>
    error?: string
}

interface UnitState {
    id: string
    name: string
    email: string
    region: string
    selected: boolean
    status: 'pending' | 'processing' | 'sending' | 'sent' | 'error'
    errorMessage?: string
    previewUrl?: string
    rowsCount?: number
}

interface RegionState {
    code: string
    name: string
    units: UnitState[]
    expanded: boolean
}

const initializeRegions = (): RegionState[] => {
    return UNITS_DATA.map((region: RegionType) => ({
        code: region.code,
        name: region.name,
        expanded: false,
        units: region.units.map((unit: UnitType) => ({
            ...unit,
            selected: false,
            status: 'pending' as const,
        }))
    }))
}

const formatMonth = (month: string): string => {
    const [year, monthNum] = month.split('-')
    const months = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 
                    'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
    return `${months[parseInt(monthNum) - 1]} ${year}`
}

const getCurrentMonth = (): string => {
    const now = new Date()
    return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`
}

// Cores por região
const REGION_COLORS: Record<string, { gradient: string, bg: string, text: string, border: string }> = {
    'RJ': { gradient: 'from-emerald-500 to-green-600', bg: 'bg-emerald-50', text: 'text-emerald-700', border: 'border-emerald-200' },
    'SP1': { gradient: 'from-blue-500 to-indigo-600', bg: 'bg-blue-50', text: 'text-blue-700', border: 'border-blue-200' },
    'SP2': { gradient: 'from-violet-500 to-purple-600', bg: 'bg-violet-50', text: 'text-violet-700', border: 'border-violet-200' },
    'SP3': { gradient: 'from-amber-500 to-orange-600', bg: 'bg-amber-50', text: 'text-amber-700', border: 'border-amber-200' },
    'NNE': { gradient: 'from-rose-500 to-red-600', bg: 'bg-rose-50', text: 'text-rose-700', border: 'border-rose-200' }
}

export default function ExecutionPage() {
    const navigate = useNavigate()
    const { success, error, warning } = useToast()
    const [regions, setRegions] = useState<RegionState[]>(initializeRegions)
    const [isExecuting, setIsExecuting] = useState(false)
    const [executionMode, setExecutionMode] = useState<'send' | 'dryrun' | null>(null)
    const [currentMonth, setCurrentMonth] = useState(getCurrentMonth)
    const [progress, setProgress] = useState({ current: 0, total: 0, percentage: 0 })
    const [executionLog, setExecutionLog] = useState<string[]>([])
    const [generatedFiles, setGeneratedFiles] = useState<string[]>([])

    // Stats calculados
    const stats = useMemo(() => {
        let selected = 0, sent = 0, errors = 0, pending = 0
        regions.forEach(r => {
            r.units.forEach(u => {
                if (u.selected) selected++
                if (u.status === 'sent') sent++
                if (u.status === 'error') errors++
                if (u.status === 'pending' && u.selected) pending++
            })
        })
        return { selected, sent, errors, pending, total: TOTAL_UNITS }
    }, [regions])

    const toggleRegion = (regionCode: string) => {
        setRegions(prev => prev.map(r => 
            r.code === regionCode ? { ...r, expanded: !r.expanded } : r
        ))
    }

    const toggleUnit = (regionCode: string, unitId: string) => {
        if (isExecuting) return
        setRegions(prev => prev.map(r => 
            r.code === regionCode 
                ? { ...r, units: r.units.map(u => 
                    u.id === unitId ? { ...u, selected: !u.selected } : u
                )}
                : r
        ))
    }

    const toggleAllInRegion = (regionCode: string) => {
        if (isExecuting) return
        setRegions(prev => {
            const region = prev.find(r => r.code === regionCode)
            if (!region) return prev
            const allSelected = region.units.every(u => u.selected)
            return prev.map(r => 
                r.code === regionCode 
                    ? { ...r, units: r.units.map(u => ({ ...u, selected: !allSelected })) }
                    : r
            )
        })
    }

    const selectAll = () => {
        if (isExecuting) return
        const allSelected = regions.every(r => r.units.every(u => u.selected))
        setRegions(prev => prev.map(r => ({
            ...r,
            units: r.units.map(u => ({ ...u, selected: !allSelected }))
        })))
    }

    const executeProcess = async (mode: 'send' | 'dryrun') => {
        const selectedUnits: { region: string, unit: UnitState }[] = []
        regions.forEach(r => {
            r.units.filter(u => u.selected).forEach(u => {
                selectedUnits.push({ region: r.code, unit: u })
            })
        })

        if (selectedUnits.length === 0) {
            error('Nenhuma unidade selecionada', 'Selecione pelo menos uma unidade para processar.')
            return
        }

        setIsExecuting(true)
        setExecutionMode(mode)
        setProgress({ current: 0, total: selectedUnits.length, percentage: 0 })
        setGeneratedFiles([])
        
        const modeText = mode === 'dryrun' ? '🔍 DRY RUN' : '📧 ENVIO REAL'
        const logLines = [
            `━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`,
            `${modeText} - ${new Date().toLocaleTimeString()}`,
            `📅 Referência: ${formatMonth(currentMonth)}`,
            `📊 Unidades: ${selectedUnits.length}`,
            `━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`,
            ''
        ]
        setExecutionLog(logLines)

        setRegions(prev => prev.map(r => ({
            ...r,
            units: r.units.map(u => ({ ...u, status: u.selected ? 'pending' as const : u.status }))
        })))

        const newGeneratedFiles: string[] = []

        for (let i = 0; i < selectedUnits.length; i++) {
            const { region, unit } = selectedUnits[i]
            
            setRegions(prev => prev.map(r => 
                r.code === region 
                    ? { ...r, units: r.units.map(u => 
                        u.id === unit.id ? { ...u, status: 'processing' as const } : u
                    )}
                    : r
            ))

            setExecutionLog(prev => [...prev, `⏳ [${i + 1}/${selectedUnits.length}] ${unit.name}...`])

            try {
                let emailSettings = {
                    senderEmail: undefined as string | undefined,
                    senderName: undefined as string | undefined,
                    replyTo: undefined as string | undefined,
                    additionalCc: '',
                    mandatoryCc: config.email.mandatoryCc,
                }
                try {
                    const saved = localStorage.getItem('emailSettings')
                    if (saved) {
                        const parsed = JSON.parse(saved)
                        emailSettings = { ...emailSettings, ...parsed }
                    }
                } catch { /* usa defaults */ }
                
                const ccEmails = emailSettings.additionalCc
                    ? emailSettings.additionalCc.split(',').map(e => e.trim()).filter(Boolean)
                    : undefined
                
                const payload = {
                    region: region,
                    unit: unit.name,
                    month: currentMonth,
                    dry_run: mode === 'dryrun',
                    send_email: mode === 'send',
                    sender_email: emailSettings.senderEmail,
                    sender_name: emailSettings.senderName,
                    reply_to: emailSettings.replyTo,
                    cc_emails: ccEmails,
                    mandatory_cc: emailSettings.mandatoryCc,
                }
                
                const response = await api.post<ExecuteResponse>('/api/process/execute', payload)

                if (response.success) {
                    const fileName = response.html_path?.split(/[/\\]/).pop() || `${unit.name}_${currentMonth}.html`
                    newGeneratedFiles.push(fileName)
                    setGeneratedFiles([...newGeneratedFiles])

                    setRegions(prev => prev.map(r => 
                        r.code === region 
                            ? { ...r, units: r.units.map(u => 
                                u.id === unit.id 
                                    ? { 
                                        ...u, 
                                        status: 'sent' as const,
                                        previewUrl: response.preview_url,
                                        rowsCount: response.rows_count,
                                    } 
                                    : u
                            )}
                            : r
                    ))

                    const emailInfo = mode === 'send' && response.emails_sent_to.length > 0
                        ? ` → ${response.emails_sent_to.join(', ')}`
                        : ''

                    setExecutionLog(prev => {
                        const updated = [...prev]
                        updated[updated.length - 1] = `✅ [${i + 1}/${selectedUnits.length}] ${unit.name} (${response.rows_count} linhas)${emailInfo}`
                        return updated
                    })
                } else {
                    throw new Error(response.error || 'Erro desconhecido')
                }
            } catch (err) {
                const errorMsg = err instanceof Error ? err.message : 'Erro desconhecido'
                
                setRegions(prev => prev.map(r => 
                    r.code === region 
                        ? { ...r, units: r.units.map(u => 
                            u.id === unit.id 
                                ? { ...u, status: 'error' as const, errorMessage: errorMsg } 
                                : u
                        )}
                        : r
                ))

                setExecutionLog(prev => {
                    const updated = [...prev]
                    updated[updated.length - 1] = `❌ [${i + 1}/${selectedUnits.length}] ${unit.name} - ${errorMsg}`
                    return updated
                })
            }

            setProgress({
                current: i + 1,
                total: selectedUnits.length,
                percentage: Math.round(((i + 1) / selectedUnits.length) * 100)
            })
        }

        const successCount = newGeneratedFiles.length
        const totalCount = selectedUnits.length
        
        setExecutionLog(prev => [...prev, 
            '',
            '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━',
            `🏁 CONCLUÍDO: ${successCount}/${totalCount} processados`,
            `⏱️  Finalizado: ${new Date().toLocaleTimeString()}`,
            '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━',
        ])

        setIsExecuting(false)
        setExecutionMode(null)

        if (successCount === totalCount) {
            success('Processamento concluído!', 
                mode === 'send' ? `${successCount} emails enviados` : `${successCount} HTMLs gerados`)
        } else if (successCount > 0) {
            warning('Processamento parcial', `${successCount}/${totalCount} processados`)
        } else {
            error('Falha no processamento', 'Nenhuma unidade processada')
        }
    }

    const resetExecution = () => {
        setRegions(initializeRegions())
        setExecutionLog([])
        setGeneratedFiles([])
        setProgress({ current: 0, total: 0, percentage: 0 })
    }

    return (
        <Layout>
            <div className="space-y-6 animate-fade-in-up">
                {/* Header Hero */}
                <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-[#1e3a5f] via-[#2d4a6f] to-[#3b5998] p-8 text-white">
                    <div className="absolute inset-0 bg-white/5"></div>
                    <div className="relative z-10">
                        <div className="flex items-center gap-3 mb-4">
                            <div className="w-12 h-12 rounded-2xl bg-white/20 backdrop-blur flex items-center justify-center">
                                <Zap className="h-6 w-6" />
                            </div>
                            <div>
                                <h1 className="text-2xl font-bold">Central de Execução</h1>
                                <p className="text-white/70 text-sm">Processe e envie relatórios de medição</p>
                            </div>
                        </div>
                        
                        {/* Stats Cards */}
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
                            <div className="bg-white/10 backdrop-blur rounded-xl p-4 border border-white/20">
                                <div className="flex items-center gap-2 text-white/60 text-sm mb-1">
                                    <Users className="h-4 w-4" />
                                    Selecionadas
                                </div>
                                <div className="text-2xl font-bold">{stats.selected}</div>
                            </div>
                            <div className="bg-white/10 backdrop-blur rounded-xl p-4 border border-white/20">
                                <div className="flex items-center gap-2 text-white/60 text-sm mb-1">
                                    <CheckCheck className="h-4 w-4" />
                                    Enviados
                                </div>
                                <div className="text-2xl font-bold text-green-300">{stats.sent}</div>
                            </div>
                            <div className="bg-white/10 backdrop-blur rounded-xl p-4 border border-white/20">
                                <div className="flex items-center gap-2 text-white/60 text-sm mb-1">
                                    <XCircle className="h-4 w-4" />
                                    Erros
                                </div>
                                <div className="text-2xl font-bold text-red-300">{stats.errors}</div>
                            </div>
                            <div className="bg-white/10 backdrop-blur rounded-xl p-4 border border-white/20">
                                <div className="flex items-center gap-2 text-white/60 text-sm mb-1">
                                    <Building2 className="h-4 w-4" />
                                    Total
                                </div>
                                <div className="text-2xl font-bold">{stats.total}</div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Controles */}
                <div className="glass-card p-6">
                    <div className="flex flex-wrap items-center justify-between gap-4">
                        <div className="flex items-center gap-6">
                            {/* Mês de Referência */}
                            <div className="flex items-center gap-3">
                                <div className="w-10 h-10 rounded-xl bg-blue-100 flex items-center justify-center">
                                    <Calendar className="h-5 w-5 text-blue-600" />
                                </div>
                                <div>
                                    <label className="text-xs font-medium text-gray-500 uppercase tracking-wide">Mês Referência</label>
                                    <input
                                        type="month"
                                        value={currentMonth}
                                        onChange={(e) => setCurrentMonth(e.target.value)}
                                        className="block w-full px-3 py-1.5 border-0 bg-transparent text-lg font-semibold text-gray-900 focus:outline-none focus:ring-0"
                                        disabled={isExecuting}
                                    />
                                </div>
                            </div>

                            <div className="h-10 w-px bg-gray-200"></div>

                            {/* Seleção Rápida */}
                            <button
                                onClick={selectAll}
                                disabled={isExecuting}
                                className={cn(
                                    "flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition-all",
                                    regions.every(r => r.units.every(u => u.selected))
                                        ? "bg-blue-100 text-blue-700 hover:bg-blue-200"
                                        : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                                )}
                            >
                                <CheckCheck className="h-4 w-4" />
                                {regions.every(r => r.units.every(u => u.selected)) 
                                    ? 'Desmarcar Todas' 
                                    : 'Selecionar Todas'}
                            </button>
                        </div>

                        {/* Ações */}
                        <div className="flex items-center gap-3">
                            {executionLog.length > 0 && !isExecuting && (
                                <button
                                    onClick={resetExecution}
                                    className="flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium bg-gray-100 text-gray-700 hover:bg-gray-200 transition-all"
                                >
                                    <RotateCcw className="h-4 w-4" />
                                    Limpar
                                </button>
                            )}
                            <button
                                onClick={() => executeProcess('dryrun')}
                                disabled={isExecuting || stats.selected === 0}
                                className="flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-medium bg-amber-100 text-amber-700 hover:bg-amber-200 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                <Eye className="h-4 w-4" />
                                Testar (Dry Run)
                            </button>
                            <button
                                onClick={() => executeProcess('send')}
                                disabled={isExecuting || stats.selected === 0}
                                className="flex items-center gap-2 px-6 py-2.5 rounded-xl text-sm font-semibold bg-gradient-to-r from-blue-600 to-indigo-600 text-white hover:from-blue-700 hover:to-indigo-700 shadow-lg shadow-blue-500/25 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                {isExecuting ? (
                                    <>
                                        <Loader2 className="h-4 w-4 animate-spin" />
                                        Processando...
                                    </>
                                ) : (
                                    <>
                                        <Send className="h-4 w-4" />
                                        Enviar Emails
                                    </>
                                )}
                            </button>
                        </div>
                    </div>

                    {/* Progress Bar */}
                    {isExecuting && (
                        <div className="mt-6 p-4 bg-blue-50 rounded-xl border border-blue-100">
                            <div className="flex justify-between text-sm mb-2">
                                <span className="font-medium text-blue-700 flex items-center gap-2">
                                    <Sparkles className="h-4 w-4" />
                                    {executionMode === 'dryrun' ? 'Gerando HTMLs...' : 'Enviando emails...'}
                                </span>
                                <span className="text-blue-600 font-mono">
                                    {progress.current}/{progress.total} ({progress.percentage}%)
                                </span>
                            </div>
                            <div className="h-3 bg-blue-200 rounded-full overflow-hidden">
                                <div 
                                    className="h-full bg-gradient-to-r from-blue-500 to-indigo-500 transition-all duration-500 ease-out rounded-full"
                                    style={{ width: `${progress.percentage}%` }}
                                />
                            </div>
                        </div>
                    )}
                </div>

                {/* Grid de Regiões */}
                <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4">
                    {regions.map(region => {
                        const colors = REGION_COLORS[region.code] || REGION_COLORS['RJ']
                        const selectedInRegion = region.units.filter(u => u.selected).length
                        const sentInRegion = region.units.filter(u => u.status === 'sent').length
                        const errorInRegion = region.units.filter(u => u.status === 'error').length
                        const allSelected = region.units.every(u => u.selected)
                        
                        return (
                            <div key={region.code} className="glass-card overflow-hidden group">
                                {/* Header da Região */}
                                <div 
                                    className={cn(
                                        "cursor-pointer p-4 bg-gradient-to-r transition-all duration-300",
                                        colors.gradient
                                    )}
                                    onClick={() => toggleRegion(region.code)}
                                >
                                    <div className="flex items-center justify-between text-white">
                                        <div className="flex items-center gap-3">
                                            <div className="w-10 h-10 rounded-xl bg-white/20 backdrop-blur flex items-center justify-center font-bold">
                                                {region.code}
                                            </div>
                                            <div>
                                                <div className="font-semibold">{region.name}</div>
                                                <div className="text-white/70 text-sm">{region.units.length} unidades</div>
                                            </div>
                                        </div>
                                        <div className="flex items-center gap-2">
                                            {selectedInRegion > 0 && (
                                                <span className="px-2 py-0.5 bg-white/20 rounded-full text-xs backdrop-blur">
                                                    {selectedInRegion} selecionadas
                                                </span>
                                            )}
                                            {sentInRegion > 0 && (
                                                <span className="px-2 py-0.5 bg-green-400/30 rounded-full text-xs flex items-center gap-1">
                                                    <CheckCircle2 className="h-3 w-3" /> {sentInRegion}
                                                </span>
                                            )}
                                            {errorInRegion > 0 && (
                                                <span className="px-2 py-0.5 bg-red-400/30 rounded-full text-xs flex items-center gap-1">
                                                    <AlertCircle className="h-3 w-3" /> {errorInRegion}
                                                </span>
                                            )}
                                            {region.expanded ? (
                                                <ChevronDown className="h-5 w-5 transition-transform" />
                                            ) : (
                                                <ChevronRight className="h-5 w-5 transition-transform" />
                                            )}
                                        </div>
                                    </div>
                                </div>

                                {/* Lista de Unidades */}
                                {region.expanded && (
                                    <div className="border-t border-gray-100">
                                        <div className={cn("p-2 flex justify-between items-center", colors.bg)}>
                                            <button
                                                onClick={(e) => { e.stopPropagation(); toggleAllInRegion(region.code) }}
                                                disabled={isExecuting}
                                                className={cn("text-xs font-medium px-3 py-1 rounded-lg transition-colors", colors.text, "hover:bg-white/50")}
                                            >
                                                {allSelected ? 'Desmarcar todas' : 'Selecionar todas'}
                                            </button>
                                        </div>
                                        <div className="max-h-[280px] overflow-y-auto">
                                            {region.units.map(unit => (
                                                <div
                                                    key={unit.id}
                                                    className={cn(
                                                        "flex items-center justify-between p-3 border-b border-gray-50 last:border-0 cursor-pointer transition-all duration-200",
                                                        unit.selected && colors.bg,
                                                        unit.status === 'sent' && "bg-green-50",
                                                        unit.status === 'error' && "bg-red-50",
                                                        unit.status === 'processing' && "bg-blue-50 animate-pulse",
                                                        isExecuting && "cursor-not-allowed",
                                                        !isExecuting && "hover:bg-gray-50"
                                                    )}
                                                    onClick={() => toggleUnit(region.code, unit.id)}
                                                >
                                                    <div className="flex items-center gap-3">
                                                        <div className={cn(
                                                            "w-5 h-5 rounded-md border-2 flex items-center justify-center transition-all",
                                                            unit.selected 
                                                                ? `bg-gradient-to-r ${colors.gradient} border-transparent` 
                                                                : "border-gray-300 bg-white"
                                                        )}>
                                                            {unit.selected && <CheckCircle2 className="h-3 w-3 text-white" />}
                                                        </div>
                                                        <div>
                                                            <div className="font-medium text-sm text-gray-900">{unit.name}</div>
                                                            <div className="text-xs text-gray-500">{unit.email}</div>
                                                        </div>
                                                    </div>
                                                    <div className="flex items-center gap-2">
                                                        {unit.status === 'processing' && (
                                                            <Loader2 className="h-4 w-4 text-blue-500 animate-spin" />
                                                        )}
                                                        {unit.status === 'sent' && (
                                                            <div className="flex items-center gap-1">
                                                                <CheckCircle2 className="h-4 w-4 text-green-500" />
                                                                {unit.previewUrl && (
                                                                    <a 
                                                                        href={unit.previewUrl} 
                                                                        target="_blank" 
                                                                        rel="noopener noreferrer"
                                                                        onClick={(e) => e.stopPropagation()}
                                                                        className="p-1 rounded-lg hover:bg-green-100 transition-colors"
                                                                    >
                                                                        <Eye className="h-3.5 w-3.5 text-green-600" />
                                                                    </a>
                                                                )}
                                                            </div>
                                                        )}
                                                        {unit.status === 'error' && (
                                                            <div className="flex items-center gap-1" title={unit.errorMessage}>
                                                                <AlertCircle className="h-4 w-4 text-red-500" />
                                                            </div>
                                                        )}
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}
                            </div>
                        )
                    })}
                </div>

                {/* Log de Execução */}
                {executionLog.length > 0 && (
                    <div className="glass-card overflow-hidden">
                        <div className="p-4 border-b border-gray-100 flex items-center gap-3">
                            <div className="w-8 h-8 rounded-lg bg-gray-900 flex items-center justify-center">
                                <FileText className="h-4 w-4 text-gray-100" />
                            </div>
                            <h3 className="font-semibold text-gray-900">Log de Execução</h3>
                        </div>
                        <div className="bg-gray-900 text-gray-100 p-4 font-mono text-sm max-h-[300px] overflow-y-auto">
                            {executionLog.map((line, i) => (
                                <div key={i} className={cn(
                                    "py-0.5 leading-relaxed",
                                    line.startsWith('✅') && "text-green-400",
                                    line.startsWith('❌') && "text-red-400",
                                    line.startsWith('⏳') && "text-blue-400",
                                    line.startsWith('🏁') && "text-purple-400 font-bold",
                                    line.startsWith('━') && "text-gray-600"
                                )}>
                                    {line || '\u00A0'}
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* Resumo Final */}
                {!isExecuting && (stats.sent > 0 || stats.errors > 0) && (
                    <div className="glass-card p-6 bg-gradient-to-r from-gray-50 to-white">
                        <div className="flex items-center justify-between">
                            <div className="flex items-center gap-8">
                                <div className="text-center">
                                    <div className="text-4xl font-bold text-green-600">{stats.sent}</div>
                                    <div className="text-sm text-gray-500 mt-1">Enviados</div>
                                </div>
                                <div className="h-12 w-px bg-gray-200"></div>
                                <div className="text-center">
                                    <div className="text-4xl font-bold text-red-600">{stats.errors}</div>
                                    <div className="text-sm text-gray-500 mt-1">Erros</div>
                                </div>
                                <div className="h-12 w-px bg-gray-200"></div>
                                <div className="text-center">
                                    <div className="text-4xl font-bold text-blue-600">{generatedFiles.length}</div>
                                    <div className="text-sm text-gray-500 mt-1">HTMLs gerados</div>
                                </div>
                            </div>
                            <div className="flex gap-3">
                                <button 
                                    onClick={() => navigate('/preview')}
                                    className="flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-medium bg-gray-100 text-gray-700 hover:bg-gray-200 transition-all"
                                >
                                    <Eye className="h-4 w-4" />
                                    Ver Previews
                                </button>
                                <button 
                                    onClick={resetExecution}
                                    className="flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold bg-gradient-to-r from-blue-600 to-indigo-600 text-white hover:from-blue-700 hover:to-indigo-700 shadow-lg shadow-blue-500/25 transition-all"
                                >
                                    <Play className="h-4 w-4" />
                                    Nova Execução
                                </button>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </Layout>
    )
}
