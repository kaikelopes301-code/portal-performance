import { useState, useEffect, useRef } from 'react'
import { Eye, RefreshCw, Mail, FileText, FolderOpen, Calendar, Search, ExternalLink, Edit3, Save, X, Send, Type } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import Layout from '@/components/layout/Layout'
import { useToast } from '@/components/ui/toast'
import { cn } from '@/utils/cn'
import { REGIONS_DATA } from '@/data/units'
import { emailService, generateDefaultSubject } from '@/services'
import type { HtmlFileInfo, EditableTexts } from '@/services'
import config from '@/config'

interface RegionInfo {
    code: string
    count: number
}

export default function PreviewPage() {
    const { success, error: showError, info, warning } = useToast()
    const [loading, setLoading] = useState(false)
    const [files, setFiles] = useState<HtmlFileInfo[]>([])
    const [regions, setRegions] = useState<RegionInfo[]>([])
    const [selectedFile, setSelectedFile] = useState<HtmlFileInfo | null>(null)
    const [previewHtml, setPreviewHtml] = useState<string>('')
    const [searchTerm, setSearchTerm] = useState('')
    const [selectedRegion, setSelectedRegion] = useState<string>('all')
    const [selectedMonth, setSelectedMonth] = useState<string>('all')
    const iframeRef = useRef<HTMLIFrameElement>(null)
    
    // Estado para edição de textos
    const [isEditMode, setIsEditMode] = useState(false)
    const [editableTexts, setEditableTexts] = useState<EditableTexts>({
        subject: '',
        greeting: '',
        intro: '',
        observation: ''
    })
    const [savingTexts, setSavingTexts] = useState(false)
    const [sendingEmail, setSendingEmail] = useState(false)
    
    // Estado para assunto do email (separado do título do HTML)
    const [emailSubject, setEmailSubject] = useState<string>('')

    // Lista de meses disponíveis (derivada dos arquivos)
    const availableMonths = [...new Set(files.map(f => f.month))].sort().reverse()

    // Carregar arquivos e regiões ao montar
    useEffect(() => {
        loadFiles()
    }, [])

    // Carregar lista de arquivos da API
    const loadFiles = async () => {
        setLoading(true)
        try {
            const [filesData, regionsData] = await Promise.all([
                emailService.listFiles(),
                emailService.getRegions()
            ])

            setFiles(filesData)
            setRegions(regionsData)

            if (filesData.length > 0) {
                info('Arquivos carregados', `${filesData.length} HTMLs encontrados`)
            } else {
                info('Pasta vazia', 'Nenhum arquivo HTML encontrado. Execute o processamento primeiro.')
            }
        } catch (err) {
            console.error('Erro ao carregar arquivos:', err)
            showError('Erro ao carregar', config.messages.loadingError)
        } finally {
            setLoading(false)
        }
    }

    // Carregar preview de um arquivo específico
    const loadPreview = async (file: HtmlFileInfo) => {
        setLoading(true)
        setSelectedFile(file)

        try {
            const html = await emailService.getHtmlContent(file.filename)
            setPreviewHtml(html)
            
            // Gerar assunto padrão do email
            setEmailSubject(generateDefaultSubject(file.unit_name, file.month))
            
            success('Preview carregado', `Visualizando: ${file.unit_name}`)
        } catch (err) {
            console.error('Erro ao carregar preview:', err)
            showError('Erro', 'Não foi possível carregar o preview do arquivo')
            setPreviewHtml('')
        } finally {
            setLoading(false)
        }
    }

    // Abrir em nova aba
    const openInNewTab = () => {
        if (!selectedFile) return
        const url = `${config.apiUrl}/preview/files/${encodeURIComponent(selectedFile.filename)}`
        window.open(url, '_blank')
    }
    // Carregar textos editáveis
    const loadEditableTexts = async (file: HtmlFileInfo) => {
        try {
            const texts = await emailService.getEditableTexts(file.filename)
            setEditableTexts(texts)
        } catch (err) {
            console.error('Erro ao carregar textos:', err)
            showError('Erro', 'Não foi possível carregar os textos para edição')
        }
    }

    // Salvar textos editados
    const saveEditableTexts = async () => {
        if (!selectedFile) return
        
        setSavingTexts(true)
        try {
            const result = await emailService.updateEditableTexts(selectedFile.filename, editableTexts)
            
            if (result.success) {
                success('Textos salvos!', `Alterações: ${result.changes.join(', ')}`)
                // Recarregar o preview com as alterações
                await loadPreview(selectedFile)
                setIsEditMode(false)
            }
        } catch (err) {
            console.error('Erro ao salvar textos:', err)
            showError('Erro ao salvar', 'Não foi possível salvar as alterações')
        } finally {
            setSavingTexts(false)
        }
    }

    // Entrar no modo de edição
    const enterEditMode = async () => {
        if (!selectedFile) return
        await loadEditableTexts(selectedFile)
        setIsEditMode(true)
    }

    // Cancelar edição
    const cancelEditMode = () => {
        setIsEditMode(false)
    }

    // Enviar email usando o HTML existente (editado) com subject customizado
    const sendEmailWithExistingHtml = async () => {
        if (!selectedFile) return
        
        if (!emailSubject.trim()) {
            showError('Erro', 'Informe o assunto do email')
            return
        }
        
        // Confirmação com detalhes
        const confirmMessage = `📧 ENVIAR EMAIL\n\n` +
            `📋 Assunto: ${emailSubject}\n` +
            `🏢 Unidade: ${selectedFile.unit_name}\n` +
            `📅 Mês: ${selectedFile.month}\n\n` +
            `⚠️ O HTML atual (com suas edições) será enviado.\n\n` +
            `Deseja continuar?`
        
        if (!window.confirm(confirmMessage)) {
            return
        }
        
        setSendingEmail(true)
        try {
            const result = await emailService.sendFromPreview(selectedFile.filename, {
                email_subject: emailSubject
            })
            
            if (result.success && result.emails_sent_to?.length) {
                success(config.messages.emailSentSuccess, `Enviado para: ${result.emails_sent_to.join(', ')}`)
            } else if (result.success) {
                warning('Aviso', config.messages.noRecipientsError)
            } else {
                showError('Erro', result.error || config.messages.emailSentError)
            }
        } catch (err) {
            console.error('Erro ao enviar email:', err)
            showError('Erro', config.messages.emailSentError)
        } finally {
            setSendingEmail(false)
        }
    }

    // Filtrar arquivos
    const filteredFiles = files.filter(file => {
        const matchesSearch = file.unit_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                              file.filename.toLowerCase().includes(searchTerm.toLowerCase())
        const matchesRegion = selectedRegion === 'all' || file.region === selectedRegion
        const matchesMonth = selectedMonth === 'all' || file.month === selectedMonth
        return matchesSearch && matchesRegion && matchesMonth
    })

    // Agrupar por região para exibição
    const groupedByRegion = filteredFiles.reduce<Record<string, HtmlFileInfo[]>>((acc, file) => {
        if (!acc[file.region]) {
            acc[file.region] = []
        }
        acc[file.region].push(file)
        return acc
    }, {})

    // Formatar mês para exibição
    const formatMonth = (monthStr: string) => {
        if (!monthStr || monthStr === 'all') return 'Todos'
        const [year, month] = monthStr.split('-')
        const months = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
                       'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
        return `${months[parseInt(month) - 1]} ${year}`
    }

    // Obter nome da região
    const getRegionName = (code: string) => {
        const region = REGIONS_DATA.find(r => r.code === code)
        return region?.name || code
    }

    return (
        <Layout>
            <div className="space-y-6">
                {/* Header */}
                <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                    <div>
                        <h1 className="text-2xl font-bold text-gray-900">Preview de Relatórios</h1>
                        <p className="mt-1 text-sm text-gray-500">
                            Visualize os HTMLs reais gerados pela pipeline. Pasta: <code className="bg-gray-100 px-1 rounded">output_html/</code>
                        </p>
                    </div>
                    <Button onClick={loadFiles} disabled={loading} variant="outline">
                        <RefreshCw className={cn("h-4 w-4 mr-2", loading && "animate-spin")} />
                        Atualizar Lista
                    </Button>
                </div>

                {/* Stats */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <Card>
                        <CardContent className="p-4">
                            <div className="flex items-center gap-3">
                                <div className="p-2 bg-blue-100 rounded-lg">
                                    <FileText className="h-5 w-5 text-blue-600" />
                                </div>
                                <div>
                                    <p className="text-2xl font-bold text-gray-900">{files.length}</p>
                                    <p className="text-xs text-gray-500">Arquivos HTML</p>
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                    <Card>
                        <CardContent className="p-4">
                            <div className="flex items-center gap-3">
                                <div className="p-2 bg-green-100 rounded-lg">
                                    <FolderOpen className="h-5 w-5 text-green-600" />
                                </div>
                                <div>
                                    <p className="text-2xl font-bold text-gray-900">{regions.length}</p>
                                    <p className="text-xs text-gray-500">Regiões</p>
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                    <Card>
                        <CardContent className="p-4">
                            <div className="flex items-center gap-3">
                                <div className="p-2 bg-purple-100 rounded-lg">
                                    <Calendar className="h-5 w-5 text-purple-600" />
                                </div>
                                <div>
                                    <p className="text-2xl font-bold text-gray-900">{availableMonths.length}</p>
                                    <p className="text-xs text-gray-500">Meses</p>
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                    <Card>
                        <CardContent className="p-4">
                            <div className="flex items-center gap-3">
                                <div className="p-2 bg-amber-100 rounded-lg">
                                    <Eye className="h-5 w-5 text-amber-600" />
                                </div>
                                <div>
                                    <p className="text-2xl font-bold text-gray-900">{filteredFiles.length}</p>
                                    <p className="text-xs text-gray-500">Filtrados</p>
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                </div>

                {/* Filtros */}
                <Card>
                    <CardContent className="p-4">
                        <div className="flex flex-col md:flex-row gap-4">
                            {/* Search */}
                            <div className="flex-1 relative">
                                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                                <input
                                    type="text"
                                    placeholder="Buscar por unidade..."
                                    value={searchTerm}
                                    onChange={(e) => setSearchTerm(e.target.value)}
                                    className="w-full pl-10 pr-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                                />
                            </div>

                            {/* Region Filter */}
                            <select
                                value={selectedRegion}
                                onChange={(e) => setSelectedRegion(e.target.value)}
                                className="px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                            >
                                <option value="all">Todas as Regiões</option>
                                {regions.map(region => (
                                    <option key={region.code} value={region.code}>
                                        {getRegionName(region.code)} ({region.count})
                                    </option>
                                ))}
                            </select>

                            {/* Month Filter */}
                            <select
                                value={selectedMonth}
                                onChange={(e) => setSelectedMonth(e.target.value)}
                                className="px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                            >
                                <option value="all">Todos os Meses</option>
                                {availableMonths.map(month => (
                                    <option key={month} value={month}>
                                        {formatMonth(month)}
                                    </option>
                                ))}
                            </select>
                        </div>
                    </CardContent>
                </Card>

                {/* Main Content */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    {/* Lista de Arquivos */}
                    <div className="lg:col-span-1">
                        <Card className="h-[600px] flex flex-col">
                            <CardHeader className="border-b py-3">
                                <CardTitle className="text-sm font-medium">
                                    Arquivos Disponíveis ({filteredFiles.length})
                                </CardTitle>
                            </CardHeader>
                            <CardContent className="flex-1 overflow-auto p-0">
                                {loading && files.length === 0 ? (
                                    <div className="flex items-center justify-center h-full">
                                        <RefreshCw className="h-6 w-6 animate-spin text-gray-400" />
                                    </div>
                                ) : filteredFiles.length === 0 ? (
                                    <div className="flex flex-col items-center justify-center h-full text-gray-400">
                                        <FileText className="h-12 w-12 mb-2" />
                                        <p>Nenhum arquivo encontrado</p>
                                        <p className="text-xs mt-1">Execute a pipeline para gerar HTMLs</p>
                                    </div>
                                ) : (
                                    <div className="divide-y">
                                        {Object.entries(groupedByRegion).map(([regionCode, regionFiles]) => (
                                            <div key={regionCode}>
                                                <div className="px-3 py-2 bg-gray-50 border-b sticky top-0">
                                                    <span className="text-xs font-medium text-gray-500">
                                                        {getRegionName(regionCode)} ({regionFiles.length})
                                                    </span>
                                                </div>
                                                {regionFiles.map(file => (
                                                    <button
                                                        key={file.filename}
                                                        onClick={() => loadPreview(file)}
                                                        className={cn(
                                                            "w-full text-left px-3 py-2 hover:bg-gray-50 transition-colors border-l-2",
                                                            selectedFile?.filename === file.filename
                                                                ? "bg-blue-50 border-l-blue-500"
                                                                : "border-l-transparent"
                                                        )}
                                                    >
                                                        <p className="font-medium text-sm text-gray-900 truncate">
                                                            {file.unit_name}
                                                        </p>
                                                        <p className="text-xs text-gray-500">
                                                            {formatMonth(file.month)}
                                                        </p>
                                                    </button>
                                                ))}
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </CardContent>
                        </Card>
                    </div>

                    {/* Preview Panel */}
                    <div className="lg:col-span-2">
                        <Card className="h-[600px] flex flex-col">
                            <CardHeader className="border-b py-3 flex-shrink-0">
                                <div className="flex items-center justify-between">
                                    <div>
                                        <CardTitle className="text-sm font-medium">
                                            {selectedFile ? selectedFile.unit_name : 'Selecione um arquivo'}
                                        </CardTitle>
                                        {selectedFile && (
                                            <CardDescription className="text-xs">
                                                {selectedFile.filename}
                                            </CardDescription>
                                        )}
                                    </div>
                                    {selectedFile && (
                                        <>
                                            <div className="flex gap-2">
                                                {!isEditMode ? (
                                                    <Button
                                                        variant="outline"
                                                        size="sm"
                                                        onClick={enterEditMode}
                                                        className="text-blue-600 border-blue-200 hover:bg-blue-50"
                                                    >
                                                        <Edit3 className="h-4 w-4 mr-1" />
                                                        Editar Textos
                                                    </Button>
                                                ) : (
                                                    <>
                                                        <Button
                                                            variant="outline"
                                                            size="sm"
                                                            onClick={cancelEditMode}
                                                            disabled={savingTexts}
                                                        >
                                                            <X className="h-4 w-4 mr-1" />
                                                            Cancelar
                                                        </Button>
                                                        <Button
                                                            size="sm"
                                                            onClick={saveEditableTexts}
                                                            disabled={savingTexts}
                                                            className="bg-green-600 hover:bg-green-700"
                                                        >
                                                            <Save className="h-4 w-4 mr-1" />
                                                            {savingTexts ? 'Salvando...' : 'Salvar'}
                                                        </Button>
                                                    </>
                                                )}
                                                <Button
                                                    variant="outline"
                                                    size="sm"
                                                    onClick={openInNewTab}
                                                >
                                                    <ExternalLink className="h-4 w-4 mr-1" />
                                                    Nova Aba
                                                </Button>
                                            </div>
                                            {/* Campo de assunto do email e botão de envio */}
                                            {!isEditMode && (
                                                <div className="flex items-center gap-2 mt-2 w-full">
                                                    <Mail className="h-4 w-4 text-gray-500 flex-shrink-0" />
                                                    <input
                                                        type="text"
                                                        value={emailSubject}
                                                        onChange={(e) => setEmailSubject(e.target.value)}
                                                        placeholder="Assunto do email..."
                                                        className="flex-1 px-3 py-1.5 text-sm border border-gray-600 rounded bg-gray-800 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
                                                    />
                                                    <Button
                                                        size="sm"
                                                        onClick={sendEmailWithExistingHtml}
                                                        disabled={sendingEmail || !emailSubject.trim()}
                                                        className="bg-blue-600 hover:bg-blue-700 flex-shrink-0"
                                                    >
                                                        <Send className="h-4 w-4 mr-1" />
                                                        {sendingEmail ? 'Enviando...' : 'Enviar Email'}
                                                    </Button>
                                                </div>
                                            )}
                                        </>
                                    )}
                                </div>
                            </CardHeader>
                            <CardContent className="flex-1 p-0 overflow-hidden">
                                {!selectedFile ? (
                                    <div className="flex flex-col items-center justify-center h-full text-gray-400">
                                        <Eye className="h-16 w-16 mb-4" />
                                        <p className="text-lg">Selecione um arquivo para visualizar</p>
                                        <p className="text-sm mt-1">Clique em um item da lista à esquerda</p>
                                    </div>
                                ) : loading ? (
                                    <div className="flex items-center justify-center h-full">
                                        <RefreshCw className="h-8 w-8 animate-spin text-blue-500" />
                                    </div>
                                ) : isEditMode ? (
                                    // Painel de Edição
                                    <div className="h-full flex">
                                        {/* Formulário de edição */}
                                        <div className="w-1/2 p-4 overflow-auto border-r bg-gray-50">
                                            <div className="space-y-4">
                                                <div className="flex items-center gap-2 mb-4 pb-3 border-b">
                                                    <Type className="h-5 w-5 text-blue-600" />
                                                    <h3 className="font-semibold text-gray-900">Editar Textos do Email</h3>
                                                </div>
                                                
                                                {/* Subject */}
                                                <div>
                                                    <label className="block text-sm font-medium text-gray-700 mb-1">
                                                        Assunto do Email
                                                    </label>
                                                    <input
                                                        type="text"
                                                        value={editableTexts.subject}
                                                        onChange={(e) => setEditableTexts(prev => ({ ...prev, subject: e.target.value }))}
                                                        className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                                                        placeholder="Assunto do email..."
                                                    />
                                                </div>
                                                
                                                {/* Greeting */}
                                                <div>
                                                    <label className="block text-sm font-medium text-gray-700 mb-1">
                                                        Saudação
                                                    </label>
                                                    <input
                                                        type="text"
                                                        value={editableTexts.greeting}
                                                        onChange={(e) => setEditableTexts(prev => ({ ...prev, greeting: e.target.value }))}
                                                        className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                                                        placeholder="Ex: Prezados gestores,"
                                                    />
                                                </div>
                                                
                                                {/* Intro */}
                                                <div>
                                                    <label className="block text-sm font-medium text-gray-700 mb-1">
                                                        Texto de Introdução
                                                    </label>
                                                    <textarea
                                                        value={editableTexts.intro}
                                                        onChange={(e) => setEditableTexts(prev => ({ ...prev, intro: e.target.value }))}
                                                        rows={3}
                                                        className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm resize-none"
                                                        placeholder="Texto introdutório do email..."
                                                    />
                                                </div>
                                                
                                                {/* Observation */}
                                                <div>
                                                    <label className="block text-sm font-medium text-gray-700 mb-1">
                                                        Observação / Alerta
                                                    </label>
                                                    <textarea
                                                        value={editableTexts.observation}
                                                        onChange={(e) => setEditableTexts(prev => ({ ...prev, observation: e.target.value }))}
                                                        rows={3}
                                                        className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm resize-none"
                                                        placeholder="Texto de observação ou alerta..."
                                                    />
                                                </div>
                                                
                                                <div className="pt-2 border-t">
                                                    <p className="text-xs text-gray-500">
                                                        💡 As alterações serão salvas diretamente no arquivo HTML.
                                                        Isso afetará o conteúdo que será enviado por email.
                                                    </p>
                                                </div>
                                            </div>
                                        </div>
                                        
                                        {/* Preview lado a lado */}
                                        <div className="w-1/2">
                                            <iframe
                                                ref={iframeRef}
                                                srcDoc={previewHtml}
                                                title="Preview"
                                                className="w-full h-full border-0"
                                                sandbox="allow-same-origin"
                                            />
                                        </div>
                                    </div>
                                ) : (
                                    <iframe
                                        ref={iframeRef}
                                        srcDoc={previewHtml}
                                        title="Preview"
                                        className="w-full h-full border-0"
                                        sandbox="allow-same-origin"
                                    />
                                )}
                            </CardContent>
                        </Card>
                    </div>
                </div>

                {/* Info Footer */}
                <div className="bg-blue-50 border border-blue-100 rounded-lg p-4">
                    <div className="flex items-start gap-3">
                        <div className="p-2 bg-blue-100 rounded-lg">
                            <Mail className="h-5 w-5 text-blue-600" />
                        </div>
                        <div>
                            <h3 className="font-medium text-blue-900">Como funciona?</h3>
                            <p className="text-sm text-blue-700 mt-1">
                                Os arquivos listados são os HTMLs <strong>reais</strong> gerados pela pipeline de processamento. 
                                Eles são salvos na pasta <code className="bg-blue-100 px-1 rounded">output_html/</code> e são 
                                exatamente os mesmos que serão enviados por email para os gestores das unidades.
                            </p>
                            <p className="text-sm text-blue-700 mt-2">
                                <strong>Dica:</strong> Use o botão "Dry Run" na aba Execução para gerar novos HTMLs sem enviar emails.
                            </p>
                        </div>
                    </div>
                </div>
            </div>
        </Layout>
    )
}
