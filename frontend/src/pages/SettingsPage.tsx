import { useState, useEffect, useMemo } from 'react'
import { 
    Save, RefreshCw, Check, Calendar, Columns, Mail, Eye, EyeOff, 
    Building2, Globe, ChevronDown, ChevronRight, Search, X,
    AlertCircle, Info, Settings2
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import Layout from '@/components/layout/Layout'
import { useToast } from '@/components/ui/toast'
import { cn } from '@/utils/cn'
import { STANDARD_COLUMNS, EXTRA_COLUMNS, REGIONS_DATA, ColumnConfig, Unit } from '@/data/units'
import { api } from '@/services/api'
import appConfig from '@/config'

// ============================================================================
// TYPES
// ============================================================================

interface ColumnState {
    id: string
    name: string
    enabled: boolean
}

interface ConfigResponse {
    defaults: {
        visible_columns?: string[]
        month_reference?: string
        copy?: Record<string, string>
    }
    regions: Record<string, {
        visible_columns?: string[]
        copy?: Record<string, string>
    }>
    units: Record<string, {
        visible_columns?: string[]
        copy?: Record<string, string>
        month_reference?: string
    }>
}

interface EmailSettings {
    provider: 'sendgrid' | 'smtp'
    senderName: string
    senderEmail: string
    replyTo: string
    mandatoryCc: string // Email da consultoria - sempre em cópia
    additionalCc: string
    testMode: boolean
}

interface MonthSettings {
    // Mês de referência para faturamento = mês anterior (-1)
    billingReferenceOffset: number
    // Mês de emissão da NF = mês atual (0) - este é o mês de referência dos dados
    invoiceMonthOffset: number
    // Para modo fixo
    useFixedMonth: boolean
    fixedMonth: string
}

type ConfigScope = 'global' | { type: 'region'; code: string } | { type: 'unit'; name: string }

// ============================================================================
// CONSTANTS
// ============================================================================

const DEFAULT_EMAIL_SETTINGS: EmailSettings = {
    provider: 'sendgrid',
    senderName: appConfig.email.defaultSenderName,
    senderEmail: 'financeiro@atlasinovacoes.com.br',
    replyTo: 'financeiro@atlasinovacoes.com.br',
    mandatoryCc: appConfig.email.mandatoryCc,
    additionalCc: '',
    testMode: false,
}

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

const getCurrentMonth = () => {
    const now = new Date()
    return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`
}

const getMonthWithOffset = (offset: number) => {
    const now = new Date()
    now.setMonth(now.getMonth() + offset)
    return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`
}

const formatMonthDisplay = (monthStr: string) => {
    const [year, month] = monthStr.split('-')
    const months = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 
                   'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
    return `${months[parseInt(month) - 1]} de ${year}`
}

// ============================================================================
// COMPONENT
// ============================================================================

export default function SettingsPage() {
    const { success, info, error: errorToast } = useToast()
    
    // Loading states
    const [initialLoading, setInitialLoading] = useState(true)
    const [saving, setSaving] = useState(false)
    
    // Active tab
    const [activeTab, setActiveTab] = useState<'columns' | 'month' | 'email'>('columns')
    
    // Current scope being edited
    const [scope, setScope] = useState<ConfigScope>('global')
    const [searchQuery, setSearchQuery] = useState('')
    
    // Expanded sections in column config
    const [expandedRegions, setExpandedRegions] = useState<string[]>([])
    
    // Config data from backend
    const [configData, setConfigData] = useState<ConfigResponse | null>(null)
    
    // Column states
    const [extraColumns, setExtraColumns] = useState<ColumnState[]>(() => 
        EXTRA_COLUMNS.map((col: ColumnConfig) => ({
            id: col.id,
            name: col.name,
            enabled: false
        }))
    )
    
    // Month settings
    const [monthSettings, setMonthSettings] = useState<MonthSettings>({
        billingReferenceOffset: -1, // Mês anterior
        invoiceMonthOffset: 0, // Mês atual
        useFixedMonth: false,
        fixedMonth: getCurrentMonth(),
    })
    
    // Email settings
    const [emailSettings, setEmailSettings] = useState<EmailSettings>(DEFAULT_EMAIL_SETTINGS)
    
    // Track which units/regions have custom configs
    const [customizedUnits, setCustomizedUnits] = useState<string[]>([])
    const [customizedRegions, setCustomizedRegions] = useState<string[]>([])

    // ========================================================================
    // COMPUTED VALUES
    // ========================================================================
    
    const scopeLabel = useMemo(() => {
        if (scope === 'global') return 'Configuração Global (Padrão)'
        if (scope.type === 'region') return `Região: ${scope.code}`
        return `Unidade: ${scope.name}`
    }, [scope])
    
    const activeExtrasCount = extraColumns.filter(c => c.enabled).length
    
    // Filter units by search
    const filteredRegions = useMemo(() => {
        if (!searchQuery) return REGIONS_DATA
        const query = searchQuery.toLowerCase()
        return REGIONS_DATA.map(region => ({
            ...region,
            units: region.units.filter((u: Unit) => 
                u.name.toLowerCase().includes(query) ||
                region.name.toLowerCase().includes(query)
            )
        })).filter(r => r.units.length > 0 || r.name.toLowerCase().includes(query))
    }, [searchQuery])
    
    // Current billing and invoice months
    const billingMonth = monthSettings.useFixedMonth 
        ? monthSettings.fixedMonth 
        : getMonthWithOffset(monthSettings.billingReferenceOffset)
    
    const invoiceMonth = monthSettings.useFixedMonth
        ? (() => {
            const [year, month] = monthSettings.fixedMonth.split('-').map(Number)
            const d = new Date(year, month - 1)
            d.setMonth(d.getMonth() + 1)
            return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`
        })()
        : getMonthWithOffset(monthSettings.invoiceMonthOffset)

    // ========================================================================
    // DATA LOADING
    // ========================================================================
    
    useEffect(() => {
        loadConfig()
    }, [])
    
    const loadConfig = async () => {
        setInitialLoading(true)
        try {
            const config = await api.get<ConfigResponse>('/api/config/')
            setConfigData(config)
            
            // Set customized units/regions
            setCustomizedUnits(Object.keys(config.units || {}))
            setCustomizedRegions(Object.keys(config.regions || {}))
            
            // Load column settings from defaults
            if (config.defaults.visible_columns) {
                setExtraColumns(EXTRA_COLUMNS.map((col: ColumnConfig) => ({
                    id: col.id,
                    name: col.name,
                    enabled: config.defaults.visible_columns?.includes(col.name) ?? false
                })))
            }
            
            // Load month reference
            if (config.defaults.month_reference) {
                const ref = config.defaults.month_reference
                if (ref === 'auto') {
                    setMonthSettings(prev => ({ ...prev, useFixedMonth: false }))
                } else if (ref.match(/^\d{4}-\d{2}$/)) {
                    setMonthSettings(prev => ({ ...prev, useFixedMonth: true, fixedMonth: ref }))
                }
            }
            
            // Load saved email settings from localStorage
            const savedEmail = localStorage.getItem('emailSettings')
            if (savedEmail) {
                try {
                    const parsed = JSON.parse(savedEmail)
                    setEmailSettings({
                        ...DEFAULT_EMAIL_SETTINGS,
                        ...parsed,
                        mandatoryCc: appConfig.email.mandatoryCc, // Always enforce
                    })
                } catch {
                    // Use defaults
                }
            }
            
        } catch (err) {
            console.error('Erro ao carregar config:', err)
            errorToast('Erro ao carregar', 'Não foi possível carregar as configurações')
        } finally {
            setInitialLoading(false)
        }
    }
    
    const loadScopeConfig = (newScope: ConfigScope) => {
        if (!configData) return
        
        if (newScope === 'global') {
            // Load global defaults
            if (configData.defaults.visible_columns) {
                setExtraColumns(EXTRA_COLUMNS.map((col: ColumnConfig) => ({
                    id: col.id,
                    name: col.name,
                    enabled: configData.defaults.visible_columns?.includes(col.name) ?? false
                })))
            }
        } else if (newScope.type === 'region') {
            const regionConfig = configData.regions[newScope.code]
            if (regionConfig?.visible_columns) {
                setExtraColumns(EXTRA_COLUMNS.map((col: ColumnConfig) => ({
                    id: col.id,
                    name: col.name,
                    enabled: regionConfig.visible_columns?.includes(col.name) ?? false
                })))
            } else {
                // Inherit from defaults
                setExtraColumns(EXTRA_COLUMNS.map((col: ColumnConfig) => ({
                    id: col.id,
                    name: col.name,
                    enabled: configData.defaults.visible_columns?.includes(col.name) ?? false
                })))
            }
        } else if (newScope.type === 'unit') {
            const unitConfig = configData.units[newScope.name]
            if (unitConfig?.visible_columns) {
                setExtraColumns(EXTRA_COLUMNS.map((col: ColumnConfig) => ({
                    id: col.id,
                    name: col.name,
                    enabled: unitConfig.visible_columns?.includes(col.name) ?? false
                })))
            } else {
                // Inherit from defaults
                setExtraColumns(EXTRA_COLUMNS.map((col: ColumnConfig) => ({
                    id: col.id,
                    name: col.name,
                    enabled: configData.defaults.visible_columns?.includes(col.name) ?? false
                })))
            }
        }
    }

    // ========================================================================
    // ACTIONS
    // ========================================================================
    
    const toggleExtraColumn = (columnId: string) => {
        setExtraColumns(prev => prev.map(c => 
            c.id === columnId ? { ...c, enabled: !c.enabled } : c
        ))
    }
    
    const toggleAllExtras = (enable: boolean) => {
        setExtraColumns(prev => prev.map(c => ({ ...c, enabled: enable })))
    }
    
    const handleScopeChange = (newScope: ConfigScope) => {
        setScope(newScope)
        loadScopeConfig(newScope)
    }
    
    const toggleRegionExpand = (regionCode: string) => {
        setExpandedRegions(prev => 
            prev.includes(regionCode)
                ? prev.filter(r => r !== regionCode)
                : [...prev, regionCode]
        )
    }
    
    const saveSettings = async () => {
        setSaving(true)
        try {
            // Build visible columns list
            const enabledExtraNames = extraColumns.filter(c => c.enabled).map(c => c.name)
            const visibleColumns = [
                ...STANDARD_COLUMNS.map((c: ColumnConfig) => c.name),
                ...enabledExtraNames
            ]
            
            // Determine month reference value
            const monthReference = monthSettings.useFixedMonth 
                ? monthSettings.fixedMonth 
                : 'auto'
            
            if (scope === 'global') {
                // Save global defaults
                await api.put('/api/config/defaults', {
                    visible_columns: visibleColumns,
                    month_reference: monthReference,
                })
            } else if (scope.type === 'region') {
                // Save region config
                await api.put(`/api/config/regions/${encodeURIComponent(scope.code)}`, {
                    visible_columns: visibleColumns,
                })
                if (!customizedRegions.includes(scope.code)) {
                    setCustomizedRegions(prev => [...prev, scope.code])
                }
            } else if (scope.type === 'unit') {
                // Save unit config
                await api.put(`/api/config/units/${encodeURIComponent(scope.name)}`, {
                    visible_columns: visibleColumns,
                    month_reference: monthReference,
                })
                if (!customizedUnits.includes(scope.name)) {
                    setCustomizedUnits(prev => [...prev, scope.name])
                }
            }
            
            // Save email settings to localStorage (and will be sent with execute requests)
            localStorage.setItem('emailSettings', JSON.stringify(emailSettings))
            
            // Reload config
            await loadConfig()
            
            success('Configurações salvas!', 'As alterações foram aplicadas com sucesso.')
        } catch (err) {
            const msg = err instanceof Error ? err.message : 'Erro desconhecido'
            errorToast('Erro ao salvar', msg)
        } finally {
            setSaving(false)
        }
    }
    
    const resetToDefault = async () => {
        if (scope === 'global') {
            // Reset columns to standard only
            setExtraColumns(EXTRA_COLUMNS.map((col: ColumnConfig) => ({
                id: col.id,
                name: col.name,
                enabled: false
            })))
            setMonthSettings({
                billingReferenceOffset: -1,
                invoiceMonthOffset: 0,
                useFixedMonth: false,
                fixedMonth: getCurrentMonth(),
            })
            info('Configurações resetadas', 'As configurações foram restauradas ao padrão.')
        } else if (scope.type === 'region' || scope.type === 'unit') {
            // Delete custom config and inherit from parent
            try {
                if (scope.type === 'region') {
                    // API doesn't have delete for regions, so just clear columns
                    await api.put(`/api/config/regions/${encodeURIComponent(scope.code)}`, {
                        visible_columns: null,
                    })
                    setCustomizedRegions(prev => prev.filter(r => r !== scope.code))
                } else {
                    await api.delete(`/api/config/units/${encodeURIComponent(scope.name)}`)
                    setCustomizedUnits(prev => prev.filter(u => u !== scope.name))
                }
                handleScopeChange('global')
                success('Configuração removida', 'A configuração personalizada foi removida.')
            } catch {
                errorToast('Erro', 'Não foi possível remover a configuração.')
            }
        }
    }

    // ========================================================================
    // RENDER
    // ========================================================================
    
    if (initialLoading) {
        return (
            <Layout>
                <div className="flex items-center justify-center min-h-[60vh]">
                    <div className="bg-white/10 backdrop-blur-md border border-white/20 p-8 rounded-2xl shadow-xl flex flex-col items-center gap-4">
                        <div className="relative">
                            <div className="w-12 h-12 border-4 border-blue-500/30 border-t-blue-500 rounded-full animate-spin"></div>
                            <div className="absolute inset-0 flex items-center justify-center">
                                <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
                            </div>
                        </div>
                        <span className="text-gray-500 dark:text-gray-400 font-medium tracking-wide animate-pulse">Carregando configurações...</span>
                    </div>
                </div>
            </Layout>
        )
    }

    return (
        <Layout>
            <div className="space-y-6">
                {/* Header */}
                <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                    <div>
                        <h1 className="text-2xl font-bold text-gray-900">Configurações</h1>
                        <p className="mt-1 text-sm text-gray-500">
                            Configure colunas, mês de referência e opções de email para os relatórios.
                        </p>
                    </div>
                    <div className="flex gap-2">
                        <Button variant="outline" onClick={resetToDefault} disabled={saving}>
                            <RefreshCw className="h-4 w-4 mr-2" />
                            {scope === 'global' ? 'Resetar' : 'Remover Personalização'}
                        </Button>
                        <Button onClick={saveSettings} disabled={saving}>
                            {saving ? (
                                <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                            ) : (
                                <Save className="h-4 w-4 mr-2" />
                            )}
                            Salvar Configurações
                        </Button>
                    </div>
                </div>

                {/* Tabs */}
                <div className="flex border-b border-gray-200">
                    {[
                        { id: 'columns' as const, label: 'Colunas do Relatório', icon: Columns, badge: `${STANDARD_COLUMNS.length}+${activeExtrasCount}` },
                        { id: 'month' as const, label: 'Mês de Referência', icon: Calendar },
                        { id: 'email' as const, label: 'Configurações de Email', icon: Mail },
                    ].map(tab => (
                        <button
                            key={tab.id}
                            onClick={() => setActiveTab(tab.id)}
                            className={cn(
                                "flex items-center gap-2 px-6 py-4 border-b-2 transition-colors font-medium",
                                activeTab === tab.id 
                                    ? "border-blue-500 text-blue-600 bg-blue-50/50" 
                                    : "border-transparent text-gray-500 hover:text-gray-700 hover:bg-gray-50"
                            )}
                        >
                            <tab.icon className="h-5 w-5" />
                            {tab.label}
                            {tab.badge && (
                                <span className="px-2 py-0.5 bg-blue-100 text-blue-700 text-xs rounded-full font-medium">
                                    {tab.badge}
                                </span>
                            )}
                        </button>
                    ))}
                </div>

                {/* ============================================================ */}
                {/* TAB: COLUMNS */}
                {/* ============================================================ */}
                {activeTab === 'columns' && (
                    <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
                        {/* Left: Scope Selector */}
                        <div className="xl:col-span-1 space-y-4">
                            <Card>
                                <CardHeader className="pb-3">
                                    <CardTitle className="text-base flex items-center gap-2">
                                        <Settings2 className="h-5 w-5 text-blue-600" />
                                        Escopo da Configuração
                                    </CardTitle>
                                    <CardDescription>
                                        Escolha se a configuração será global ou específica
                                    </CardDescription>
                                </CardHeader>
                                <CardContent className="space-y-3">
                                    {/* Global Option */}
                                    <button
                                        onClick={() => handleScopeChange('global')}
                                        className={cn(
                                            "w-full p-3 rounded-lg border-2 text-left transition-all flex items-center gap-3",
                                            scope === 'global'
                                                ? "border-blue-500 bg-blue-50"
                                                : "border-gray-200 hover:border-blue-300 hover:bg-gray-50"
                                        )}
                                    >
                                        <Globe className={cn(
                                            "h-5 w-5",
                                            scope === 'global' ? "text-blue-600" : "text-gray-400"
                                        )} />
                                        <div className="flex-1">
                                            <p className="font-medium text-gray-900">Configuração Global</p>
                                            <p className="text-xs text-gray-500">Aplica a todas as unidades</p>
                                        </div>
                                        {scope === 'global' && <Check className="h-5 w-5 text-blue-600" />}
                                    </button>
                                    
                                    {/* Search */}
                                    <div className="relative">
                                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                                        <input
                                            type="text"
                                            placeholder="Buscar região ou unidade..."
                                            value={searchQuery}
                                            onChange={(e) => setSearchQuery(e.target.value)}
                                            className="w-full pl-9 pr-8 py-2 text-sm border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                                        />
                                        {searchQuery && (
                                            <button 
                                                onClick={() => setSearchQuery('')}
                                                className="absolute right-3 top-1/2 -translate-y-1/2"
                                            >
                                                <X className="h-4 w-4 text-gray-400 hover:text-gray-600" />
                                            </button>
                                        )}
                                    </div>
                                    
                                    {/* Regions and Units */}
                                    <div className="max-h-[400px] overflow-y-auto space-y-1 border rounded-lg p-2 bg-gray-50">
                                        {filteredRegions.map(region => (
                                            <div key={region.code}>
                                                {/* Region Header */}
                                                <button
                                                    onClick={() => toggleRegionExpand(region.code)}
                                                    className={cn(
                                                        "w-full p-2 rounded flex items-center gap-2 text-left transition-colors",
                                                        typeof scope === 'object' && scope.type === 'region' && scope.code === region.code
                                                            ? "bg-blue-100 text-blue-800"
                                                            : "hover:bg-gray-100"
                                                    )}
                                                >
                                                    {expandedRegions.includes(region.code) 
                                                        ? <ChevronDown className="h-4 w-4 text-gray-500" />
                                                        : <ChevronRight className="h-4 w-4 text-gray-500" />
                                                    }
                                                    <span className="font-medium text-sm flex-1">{region.name}</span>
                                                    <span className="text-xs text-gray-400">{region.units.length}</span>
                                                    {customizedRegions.includes(region.code) && (
                                                        <span className="w-2 h-2 bg-amber-500 rounded-full" title="Personalizado" />
                                                    )}
                                                </button>
                                                
                                                {/* Region Units */}
                                                {expandedRegions.includes(region.code) && (
                                                    <div className="ml-4 space-y-0.5 mt-1">
                                                        {/* Region config option */}
                                                        <button
                                                            onClick={() => handleScopeChange({ type: 'region', code: region.code })}
                                                            className={cn(
                                                                "w-full p-2 rounded text-left text-xs flex items-center gap-2",
                                                                typeof scope === 'object' && scope.type === 'region' && scope.code === region.code
                                                                    ? "bg-blue-100 text-blue-800"
                                                                    : "text-blue-600 hover:bg-blue-50"
                                                            )}
                                                        >
                                                            <Settings2 className="h-3.5 w-3.5" />
                                                            Configurar toda a região
                                                        </button>
                                                        
                                                        {region.units.map((unit: Unit) => (
                                                            <button
                                                                key={unit.id}
                                                                onClick={() => handleScopeChange({ type: 'unit', name: unit.name })}
                                                                className={cn(
                                                                    "w-full p-2 rounded text-left text-sm flex items-center gap-2 transition-colors",
                                                                    typeof scope === 'object' && scope.type === 'unit' && scope.name === unit.name
                                                                        ? "bg-blue-100 text-blue-800"
                                                                        : "hover:bg-gray-100"
                                                                )}
                                                            >
                                                                <Building2 className="h-3.5 w-3.5 text-gray-400" />
                                                                <span className="flex-1 truncate">{unit.name}</span>
                                                                {customizedUnits.includes(unit.name) && (
                                                                    <span className="w-2 h-2 bg-amber-500 rounded-full" title="Personalizado" />
                                                                )}
                                                            </button>
                                                        ))}
                                                    </div>
                                                )}
                                            </div>
                                        ))}
                                    </div>
                                    
                                    {/* Current scope indicator */}
                                    <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
                                        <p className="text-xs text-blue-600 font-medium">Editando:</p>
                                        <p className="text-sm text-blue-800 font-semibold">{scopeLabel}</p>
                                    </div>
                                </CardContent>
                            </Card>
                        </div>
                        
                        {/* Right: Columns Configuration */}
                        <div className="xl:col-span-2 space-y-6">
                            {/* Standard Columns */}
                            <Card>
                                <CardHeader className="bg-gradient-to-r from-blue-50 to-blue-100/50 border-b">
                                    <div className="flex items-center justify-between">
                                        <div>
                                            <CardTitle className="text-lg flex items-center gap-2">
                                                <div className="w-3 h-3 rounded-full bg-blue-500"></div>
                                                Colunas Padrão
                                            </CardTitle>
                                            <CardDescription>
                                                {STANDARD_COLUMNS.length} colunas sempre presentes em todos os relatórios
                                            </CardDescription>
                                        </div>
                                        <div className="flex items-center gap-2 px-3 py-1.5 bg-blue-100 text-blue-700 rounded-full text-sm font-medium">
                                            <Check className="h-4 w-4" />
                                            Sempre Ativas
                                        </div>
                                    </div>
                                </CardHeader>
                                <CardContent className="p-0">
                                    <div className="grid grid-cols-1 md:grid-cols-2 divide-y md:divide-y-0 md:divide-x">
                                        {[0, 1].map(colIdx => (
                                            <div key={colIdx} className="divide-y">
                                                {STANDARD_COLUMNS
                                                    .slice(colIdx * Math.ceil(STANDARD_COLUMNS.length / 2), (colIdx + 1) * Math.ceil(STANDARD_COLUMNS.length / 2))
                                                    .map((col: ColumnConfig, idx: number) => (
                                                    <div 
                                                        key={col.id}
                                                        className="flex items-center gap-3 p-3 hover:bg-gray-50"
                                                    >
                                                        <div className="w-6 h-6 rounded bg-blue-100 text-blue-700 flex items-center justify-center text-xs font-bold">
                                                            {colIdx * Math.ceil(STANDARD_COLUMNS.length / 2) + idx + 1}
                                                        </div>
                                                        <div className="flex-1 min-w-0">
                                                            <p className="font-medium text-sm text-gray-900">{col.name}</p>
                                                            <p className="text-xs text-gray-500 truncate">{col.description}</p>
                                                        </div>
                                                        <Eye className="h-4 w-4 text-green-500" />
                                                    </div>
                                                ))}
                                            </div>
                                        ))}
                                    </div>
                                </CardContent>
                            </Card>

                            {/* Extra Columns */}
                            <Card>
                                <CardHeader className="bg-gradient-to-r from-amber-50 to-amber-100/50 border-b">
                                    <div className="flex items-center justify-between">
                                        <div>
                                            <CardTitle className="text-lg flex items-center gap-2">
                                                <div className="w-3 h-3 rounded-full bg-amber-500"></div>
                                                Colunas Extras
                                            </CardTitle>
                                            <CardDescription>
                                                {activeExtrasCount} de {EXTRA_COLUMNS.length} colunas opcionais ativadas
                                            </CardDescription>
                                        </div>
                                        <div className="flex gap-2">
                                            <Button 
                                                variant="outline" 
                                                size="sm"
                                                onClick={() => toggleAllExtras(true)}
                                            >
                                                <Eye className="h-4 w-4 mr-1" />
                                                Ativar Todas
                                            </Button>
                                            <Button 
                                                variant="outline" 
                                                size="sm"
                                                onClick={() => toggleAllExtras(false)}
                                            >
                                                <EyeOff className="h-4 w-4 mr-1" />
                                                Desativar Todas
                                            </Button>
                                        </div>
                                    </div>
                                </CardHeader>
                                <CardContent className="p-0">
                                    <div className="grid grid-cols-1 md:grid-cols-2">
                                        {extraColumns.map((col) => {
                                            const colInfo = EXTRA_COLUMNS.find((c: ColumnConfig) => c.id === col.id)
                                            return (
                                                <div 
                                                    key={col.id}
                                                    onClick={() => toggleExtraColumn(col.id)}
                                                    className={cn(
                                                        "flex items-center gap-3 p-4 cursor-pointer transition-all border-b border-r last:border-r-0",
                                                        col.enabled 
                                                            ? "bg-amber-50 hover:bg-amber-100" 
                                                            : "bg-white hover:bg-gray-50"
                                                    )}
                                                >
                                                    <button
                                                        className={cn(
                                                            "w-10 h-6 rounded-full relative transition-colors",
                                                            col.enabled ? "bg-amber-500" : "bg-gray-300"
                                                        )}
                                                    >
                                                        <div className={cn(
                                                            "w-5 h-5 rounded-full bg-white shadow absolute top-0.5 transition-transform",
                                                            col.enabled ? "translate-x-4" : "translate-x-0.5"
                                                        )} />
                                                    </button>
                                                    <div className="flex-1 min-w-0">
                                                        <p className={cn(
                                                            "font-medium text-sm",
                                                            col.enabled ? "text-gray-900" : "text-gray-600"
                                                        )}>
                                                            {col.name}
                                                        </p>
                                                        <p className="text-xs text-gray-500 truncate">
                                                            {colInfo?.description}
                                                        </p>
                                                    </div>
                                                </div>
                                            )
                                        })}
                                    </div>
                                </CardContent>
                            </Card>
                        </div>
                    </div>
                )}

                {/* ============================================================ */}
                {/* TAB: MONTH REFERENCE */}
                {/* ============================================================ */}
                {activeTab === 'month' && (
                    <div className="max-w-3xl mx-auto space-y-6">
                        {/* Info Card */}
                        <Card className="border-blue-200 bg-blue-50">
                            <CardContent className="p-4">
                                <div className="flex gap-3">
                                    <Info className="h-5 w-5 text-blue-600 flex-shrink-0 mt-0.5" />
                                    <div className="text-sm text-blue-800">
                                        <p className="font-semibold mb-1">Como funciona o mês de referência:</p>
                                        <ul className="list-disc list-inside space-y-1 text-blue-700">
                                            <li><strong>Mês de emissão da NF</strong> = Mês atual (este é o mês de referência real dos dados)</li>
                                            <li><strong>Mês de referência para faturamento</strong> = Mês anterior (-1)</li>
                                        </ul>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                        
                        <Card>
                            <CardHeader>
                                <CardTitle className="flex items-center gap-2">
                                    <Calendar className="h-5 w-5 text-blue-600" />
                                    Configuração do Mês de Referência
                                </CardTitle>
                                <CardDescription>
                                    Defina como o sistema calcula os meses nas medições
                                </CardDescription>
                            </CardHeader>
                            <CardContent className="space-y-6">
                                {/* Mode Selection */}
                                <div className="grid grid-cols-2 gap-4">
                                    <button
                                        onClick={() => setMonthSettings(prev => ({ ...prev, useFixedMonth: false }))}
                                        className={cn(
                                            "p-4 rounded-xl border-2 text-left transition-all",
                                            !monthSettings.useFixedMonth
                                                ? "border-blue-500 bg-blue-50 ring-2 ring-blue-200"
                                                : "border-gray-200 hover:border-gray-300"
                                        )}
                                    >
                                        <div className="flex items-center gap-3 mb-3">
                                            <div className={cn(
                                                "w-5 h-5 rounded-full border-2 flex items-center justify-center",
                                                !monthSettings.useFixedMonth ? "border-blue-500 bg-blue-500" : "border-gray-300"
                                            )}>
                                                {!monthSettings.useFixedMonth && <Check className="h-3 w-3 text-white" />}
                                            </div>
                                            <span className="font-semibold text-gray-900">Automático</span>
                                        </div>
                                        <p className="text-sm text-gray-600">
                                            Calcula automaticamente baseado na data atual. Ideal para uso contínuo.
                                        </p>
                                    </button>
                                    
                                    <button
                                        onClick={() => setMonthSettings(prev => ({ ...prev, useFixedMonth: true }))}
                                        className={cn(
                                            "p-4 rounded-xl border-2 text-left transition-all",
                                            monthSettings.useFixedMonth
                                                ? "border-blue-500 bg-blue-50 ring-2 ring-blue-200"
                                                : "border-gray-200 hover:border-gray-300"
                                        )}
                                    >
                                        <div className="flex items-center gap-3 mb-3">
                                            <div className={cn(
                                                "w-5 h-5 rounded-full border-2 flex items-center justify-center",
                                                monthSettings.useFixedMonth ? "border-blue-500 bg-blue-500" : "border-gray-300"
                                            )}>
                                                {monthSettings.useFixedMonth && <Check className="h-3 w-3 text-white" />}
                                            </div>
                                            <span className="font-semibold text-gray-900">Mês Fixo</span>
                                        </div>
                                        <p className="text-sm text-gray-600">
                                            Define um mês específico. Útil para reprocessamentos.
                                        </p>
                                    </button>
                                </div>
                                
                                {/* Fixed Month Selector */}
                                {monthSettings.useFixedMonth && (
                                    <div className="p-4 bg-gray-50 rounded-lg border">
                                        <label className="block text-sm font-medium text-gray-700 mb-2">
                                            Selecione o mês de referência para faturamento:
                                        </label>
                                        <input
                                            type="month"
                                            value={monthSettings.fixedMonth}
                                            onChange={(e) => setMonthSettings(prev => ({ ...prev, fixedMonth: e.target.value }))}
                                            className="w-full max-w-xs p-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-lg"
                                        />
                                    </div>
                                )}
                                
                                {/* Preview */}
                                <div className="grid grid-cols-2 gap-4">
                                    <div className="p-4 bg-gradient-to-br from-emerald-50 to-emerald-100 border border-emerald-200 rounded-xl">
                                        <div className="flex items-center gap-2 text-emerald-700 mb-2">
                                            <Calendar className="h-4 w-4" />
                                            <span className="text-xs font-medium uppercase tracking-wide">Mês de Referência para Faturamento</span>
                                        </div>
                                        <p className="text-2xl font-bold text-emerald-800">
                                            {formatMonthDisplay(billingMonth)}
                                        </p>
                                        <p className="text-xs text-emerald-600 mt-1">Competência da medição</p>
                                    </div>
                                    
                                    <div className="p-4 bg-gradient-to-br from-blue-50 to-blue-100 border border-blue-200 rounded-xl">
                                        <div className="flex items-center gap-2 text-blue-700 mb-2">
                                            <Calendar className="h-4 w-4" />
                                            <span className="text-xs font-medium uppercase tracking-wide">Mês de Emissão da NF</span>
                                        </div>
                                        <p className="text-2xl font-bold text-blue-800">
                                            {formatMonthDisplay(invoiceMonth)}
                                        </p>
                                        <p className="text-xs text-blue-600 mt-1">Mês atual (referência dos dados)</p>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                    </div>
                )}

                {/* ============================================================ */}
                {/* TAB: EMAIL */}
                {/* ============================================================ */}
                {activeTab === 'email' && (
                    <div className="max-w-3xl mx-auto space-y-6">
                        {/* Provider Selection */}
                        <Card>
                            <CardHeader>
                                <CardTitle className="flex items-center gap-2">
                                    <Mail className="h-5 w-5 text-blue-600" />
                                    Serviço de Envio
                                </CardTitle>
                                <CardDescription>
                                    Escolha o provedor de email para envio das medições
                                </CardDescription>
                            </CardHeader>
                            <CardContent>
                                <div className="grid grid-cols-2 gap-4">
                                    <button
                                        onClick={() => setEmailSettings(prev => ({ ...prev, provider: 'sendgrid' }))}
                                        className={cn(
                                            "p-4 rounded-xl border-2 text-left transition-all",
                                            emailSettings.provider === 'sendgrid'
                                                ? "border-blue-500 bg-blue-50 ring-2 ring-blue-200"
                                                : "border-gray-200 hover:border-gray-300"
                                        )}
                                    >
                                        <div className="flex items-center justify-between mb-2">
                                            <span className="font-bold text-lg text-gray-900">SendGrid</span>
                                            {emailSettings.provider === 'sendgrid' && (
                                                <span className="px-2 py-0.5 bg-green-100 text-green-700 text-xs rounded-full font-medium">
                                                    Selecionado
                                                </span>
                                            )}
                                        </div>
                                        <p className="text-sm text-gray-600">
                                            Serviço profissional de email. Alta entregabilidade e rastreamento.
                                        </p>
                                        <p className="text-xs text-blue-600 mt-2 font-medium">✓ Recomendado</p>
                                    </button>
                                    
                                    <button
                                        onClick={() => setEmailSettings(prev => ({ ...prev, provider: 'smtp' }))}
                                        className={cn(
                                            "p-4 rounded-xl border-2 text-left transition-all",
                                            emailSettings.provider === 'smtp'
                                                ? "border-blue-500 bg-blue-50 ring-2 ring-blue-200"
                                                : "border-gray-200 hover:border-gray-300"
                                        )}
                                    >
                                        <div className="flex items-center justify-between mb-2">
                                            <span className="font-bold text-lg text-gray-900">SMTP</span>
                                            {emailSettings.provider === 'smtp' && (
                                                <span className="px-2 py-0.5 bg-green-100 text-green-700 text-xs rounded-full font-medium">
                                                    Selecionado
                                                </span>
                                            )}
                                        </div>
                                        <p className="text-sm text-gray-600">
                                            Servidor de email próprio. Requer configuração manual.
                                        </p>
                                    </button>
                                </div>
                            </CardContent>
                        </Card>
                        
                        {/* Sender Configuration */}
                        <Card>
                            <CardHeader>
                                <CardTitle>Configurações do Remetente</CardTitle>
                                <CardDescription>
                                    Defina o nome e email que aparecerão como remetente
                                </CardDescription>
                            </CardHeader>
                            <CardContent className="space-y-4">
                                <div className="grid grid-cols-2 gap-4">
                                    <div className="space-y-2">
                                        <label className="text-sm font-medium text-gray-700">Nome do Remetente</label>
                                        <input
                                            type="text"
                                            value={emailSettings.senderName}
                                            onChange={(e) => setEmailSettings(prev => ({ ...prev, senderName: e.target.value }))}
                                            className="w-full p-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                                            placeholder="Ex: Equipe Financeira"
                                        />
                                    </div>
                                    <div className="space-y-2">
                                        <label className="text-sm font-medium text-gray-700">Email do Remetente</label>
                                        <input
                                            type="email"
                                            value={emailSettings.senderEmail}
                                            onChange={(e) => setEmailSettings(prev => ({ ...prev, senderEmail: e.target.value }))}
                                            className="w-full p-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                                            placeholder="Ex: financeiro@empresa.com"
                                        />
                                    </div>
                                </div>
                                
                                <div className="space-y-2">
                                    <label className="text-sm font-medium text-gray-700">Responder Para (Reply-To)</label>
                                    <input
                                        type="email"
                                        value={emailSettings.replyTo}
                                        onChange={(e) => setEmailSettings(prev => ({ ...prev, replyTo: e.target.value }))}
                                        className="w-full p-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                                        placeholder="Deixe vazio para usar o email do remetente"
                                    />
                                    <p className="text-xs text-gray-500">
                                        Email que receberá as respostas. Se vazio, usa o email do remetente.
                                    </p>
                                </div>
                            </CardContent>
                        </Card>
                        
                        {/* CC Configuration */}
                        <Card>
                            <CardHeader>
                                <CardTitle>Emails em Cópia (CC)</CardTitle>
                                <CardDescription>
                                    Configure quem receberá cópia de todos os emails enviados
                                </CardDescription>
                            </CardHeader>
                            <CardContent className="space-y-4">
                                {/* Mandatory CC */}
                                <div className="p-4 bg-amber-50 border border-amber-200 rounded-lg">
                                    <div className="flex items-start gap-3">
                                        <AlertCircle className="h-5 w-5 text-amber-600 flex-shrink-0 mt-0.5" />
                                        <div className="flex-1">
                                            <p className="font-medium text-amber-800">Cópia Obrigatória (Consultoria)</p>
                                            <p className="text-sm text-amber-700 mt-1">
                                                Este email sempre receberá cópia de todos os envios:
                                            </p>
                                            <div className="mt-2 p-2 bg-white rounded border border-amber-300 font-mono text-sm text-amber-900">
                                                {emailSettings.mandatoryCc}
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                
                                {/* Additional CC */}
                                <div className="space-y-2">
                                    <label className="text-sm font-medium text-gray-700">Emails Adicionais em Cópia</label>
                                    <input
                                        type="text"
                                        value={emailSettings.additionalCc}
                                        onChange={(e) => setEmailSettings(prev => ({ ...prev, additionalCc: e.target.value }))}
                                        className="w-full p-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                                        placeholder="email1@exemplo.com, email2@exemplo.com"
                                    />
                                    <p className="text-xs text-gray-500">
                                        Separe múltiplos emails por vírgula. Estes emails também receberão cópia de todos os envios.
                                    </p>
                                </div>
                            </CardContent>
                        </Card>
                        
                        {/* Test Mode */}
                        <Card>
                            <CardHeader>
                                <CardTitle>Modo de Teste</CardTitle>
                            </CardHeader>
                            <CardContent>
                                <div 
                                    onClick={() => setEmailSettings(prev => ({ ...prev, testMode: !prev.testMode }))}
                                    className={cn(
                                        "flex items-center justify-between p-4 rounded-lg border-2 cursor-pointer transition-all",
                                        emailSettings.testMode 
                                            ? "border-amber-400 bg-amber-50" 
                                            : "border-gray-200 hover:border-gray-300"
                                    )}
                                >
                                    <div className="flex items-start gap-3">
                                        <AlertCircle className={cn(
                                            "h-5 w-5 mt-0.5",
                                            emailSettings.testMode ? "text-amber-600" : "text-gray-400"
                                        )} />
                                        <div>
                                            <p className="font-medium text-gray-900">Ativar Modo de Teste</p>
                                            <p className="text-sm text-gray-600 mt-1">
                                                Quando ativado, todos os emails serão enviados apenas para o remetente configurado, 
                                                ignorando os destinatários reais. Útil para testar o sistema antes de enviar de verdade.
                                            </p>
                                        </div>
                                    </div>
                                    <button
                                        className={cn(
                                            "w-14 h-7 rounded-full transition-colors relative flex-shrink-0",
                                            emailSettings.testMode ? "bg-amber-500" : "bg-gray-300"
                                        )}
                                    >
                                        <div className={cn(
                                            "w-6 h-6 rounded-full bg-white shadow absolute top-0.5 transition-transform",
                                            emailSettings.testMode ? "translate-x-7" : "translate-x-0.5"
                                        )} />
                                    </button>
                                </div>
                            </CardContent>
                        </Card>
                    </div>
                )}
            </div>
        </Layout>
    )
}
