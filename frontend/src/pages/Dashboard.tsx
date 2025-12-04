import { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { useNavigate } from 'react-router-dom'
import { Upload, File, CheckCircle, AlertCircle, FileWarning, MapPin, Plus, Trash2 } from 'lucide-react'
import Layout from '@/components/layout/Layout'
import { jobService, FileWithRegion } from '@/services'
import { useToast } from '@/components/ui/toast'

// Constantes
const VALID_REGIONS = ['RJ', 'SP1', 'SP2', 'SP3', 'NNE'] as const

const REGION_DESCRIPTIONS: Record<string, string> = {
    'RJ': 'RJ',
    'SP1': 'SP1',
    'SP2': 'SP2', 
    'SP3': 'SP3',
    'NNE': 'NNE'
}

// Cores por região
const REGION_COLORS: Record<string, string> = {
    'RJ': 'from-green-500 to-emerald-600',
    'SP1': 'from-blue-500 to-blue-600',
    'SP2': 'from-purple-500 to-purple-600',
    'SP3': 'from-orange-500 to-orange-600',
    'NNE': 'from-red-500 to-rose-600'
}

// Validação de arquivo
const validateFile = (file: File): { valid: boolean; error?: string } => {
    // Verifica tamanho (max 50MB)
    const maxSize = 50 * 1024 * 1024
    if (file.size > maxSize) {
        return { valid: false, error: 'Arquivo muito grande. Máximo: 50MB' }
    }
    
    // Verifica extensão
    const validExtensions = ['.xlsx', '.xls']
    const hasValidExt = validExtensions.some(ext => file.name.toLowerCase().endsWith(ext))
    if (!hasValidExt) {
        return { valid: false, error: 'Formato inválido. Use arquivos .xlsx ou .xls' }
    }
    
    // Verifica se não é arquivo temporário do Excel
    if (file.name.startsWith('~$')) {
        return { valid: false, error: 'Este é um arquivo temporário do Excel. Feche a planilha e tente novamente.' }
    }
    
    return { valid: true }
}

interface UploadFile {
    id: string
    file: File
    region: string
}

export default function Dashboard() {
    const [files, setFiles] = useState<UploadFile[]>([])
    const [fileError, setFileError] = useState<string | null>(null)
    const [uploading, setUploading] = useState(false)
    const [uploadSuccess, setUploadSuccess] = useState(false)
    const [uploadedJobs, setUploadedJobs] = useState<{ id: string; filename: string; region?: string }[]>([])
    const navigate = useNavigate()
    const toast = useToast()

    // Detecta região pelo nome do arquivo
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

    const onDrop = useCallback((acceptedFiles: File[], rejectedFiles: any[]) => {
        // Arquivos rejeitados pelo dropzone
        if (rejectedFiles.length > 0) {
            const rejection = rejectedFiles[0]
            if (rejection.errors?.[0]?.code === 'file-invalid-type') {
                setFileError('Formato inválido. Use arquivos .xlsx ou .xls')
            } else {
                setFileError('Arquivo não aceito')
            }
            return
        }
        
        if (acceptedFiles?.length > 0) {
            // Limite de 5 arquivos
            const remainingSlots = 5 - files.length
            if (remainingSlots <= 0) {
                toast.warning('Limite atingido', 'Máximo de 5 arquivos por upload')
                return
            }

            const filesToAdd = acceptedFiles.slice(0, remainingSlots)
            const newFiles: UploadFile[] = []

            for (const file of filesToAdd) {
                const validation = validateFile(file)
                if (!validation.valid) {
                    toast.error('Arquivo inválido', `${file.name}: ${validation.error}`)
                    continue
                }

                const detectedRegion = detectRegion(file.name)

                // Verifica se já existe arquivo com mesma região (substitui)
                const existingIndex = files.findIndex(f => f.region === detectedRegion && detectedRegion !== '')
                if (existingIndex >= 0 && detectedRegion) {
                    // Remove o arquivo anterior da mesma região
                    setFiles(prev => prev.filter(f => f.region !== detectedRegion))
                    toast.info('Substituindo', `Planilha ${detectedRegion} será substituída`)
                }

                newFiles.push({
                    id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
                    file,
                    region: detectedRegion
                })
            }

            if (newFiles.length > 0) {
                setFiles(prev => [...prev.filter(f => !newFiles.some(nf => nf.region === f.region && f.region !== '')), ...newFiles])
                setFileError(null)
                setUploadSuccess(false)
                setUploadedJobs([])
                
                const msg = newFiles.length === 1 
                    ? `${newFiles[0].file.name} adicionado`
                    : `${newFiles.length} arquivos adicionados`
                toast.info('Arquivos selecionados', msg)
            }
        }
    }, [files, toast])

    const { getRootProps, getInputProps, isDragActive } = useDropzone({
        onDrop,
        accept: {
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
            'application/vnd.ms-excel': ['.xls']
        },
        maxFiles: 5
    })

    const removeFile = (id: string) => {
        setFiles(prev => prev.filter(f => f.id !== id))
    }

    const updateFileRegion = (id: string, newRegion: string) => {
        // Verifica se já existe arquivo com essa região
        const existingWithRegion = files.find(f => f.region === newRegion && f.id !== id)
        if (existingWithRegion && newRegion) {
            toast.warning('Região já usada', `Já existe um arquivo para ${newRegion}. Remova-o primeiro.`)
            return
        }
        
        setFiles(prev => prev.map(f => 
            f.id === id ? { ...f, region: newRegion } : f
        ))
    }

    const handleUpload = async () => {
        if (files.length === 0) return

        // Verifica se todos os arquivos têm região definida
        const filesWithoutRegion = files.filter(f => !f.region)
        if (filesWithoutRegion.length > 0) {
            toast.warning('Região obrigatória', 'Defina a região para todos os arquivos antes de enviar.')
            return
        }

        setUploading(true)
        try {
            if (files.length === 1) {
                // Upload único
                const job = await jobService.upload(files[0].file, files[0].region || undefined)
                setUploadedJobs([{ id: String(job.id), filename: job.filename, region: job.region || undefined }])
            } else {
                // Upload em lote
                const filesWithRegions: FileWithRegion[] = files.map(f => ({
                    file: f.file,
                    region: f.region || undefined
                }))
                const jobs = await jobService.uploadBatch(filesWithRegions)
                setUploadedJobs(jobs.map(j => ({ id: String(j.id), filename: j.filename, region: j.region || undefined })))
            }
            
            setUploadSuccess(true)
            setFiles([])
            toast.success('Upload realizado!', `${files.length} arquivo(s) enviado(s). Planilhas anteriores das mesmas regiões foram substituídas.`)
        } catch (error: any) {
            console.error('Upload failed:', error)
            const errorMsg = error?.message || 'Erro ao enviar arquivo. Tente novamente.'
            toast.error('Erro no upload', errorMsg)
        } finally {
            setUploading(false)
        }
    }

    const getUsedRegions = () => files.map(f => f.region).filter(Boolean)

    return (
        <Layout>
            <div className="space-y-8 animate-fade-in-up">
                {/* Hero Section */}
                <div className="hero-glass">
                    <div className="relative z-10">
                        <h1 className="text-3xl font-bold text-white mb-2">
                            Portal Performance
                        </h1>
                        <p className="text-blue-100 text-lg">
                            Envie até 5 planilhas de medição para iniciar o processamento dos relatórios.
                        </p>
                    </div>
                </div>

                {/* Upload Card */}
                <div className="glass-card p-0 overflow-hidden">
                    <div className="p-6 border-b border-gray-200/50">
                        <div className="flex items-center justify-between">
                            <div>
                                <h2 className="text-xl font-bold text-[#2F4F71]">Upload de Planilhas</h2>
                                <p className="text-gray-500 mt-1">
                                    Arraste os arquivos .xlsx ou .xls aqui (máx. 5 arquivos, 50MB cada)
                                </p>
                            </div>
                            {files.length > 0 && (
                                <span className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm font-medium">
                                    {files.length}/5 arquivos
                                </span>
                            )}
                        </div>
                    </div>
                    <div className="p-6">
                        {!uploadSuccess && (
                            <>
                                {/* Dropzone */}
                                {files.length < 5 && (
                                    <div
                                        {...getRootProps()}
                                        className={`dropzone-glass ${isDragActive ? 'active' : ''} ${fileError ? '!border-red-400 !bg-red-50/50' : ''} ${files.length > 0 ? 'min-h-[120px]' : ''}`}
                                    >
                                        <input {...getInputProps()} />
                                        {fileError ? (
                                            <>
                                                <FileWarning className="mx-auto h-12 w-12 text-red-400" />
                                                <p className="mt-3 text-sm font-medium text-red-600">{fileError}</p>
                                                <p className="mt-1 text-xs text-gray-500">Clique para selecionar outro arquivo</p>
                                            </>
                                        ) : (
                                            <>
                                                <div className="w-16 h-16 mx-auto rounded-2xl bg-gradient-to-br from-[#3b82f6]/20 to-[#2563eb]/20 flex items-center justify-center">
                                                    {files.length > 0 ? (
                                                        <Plus className="h-8 w-8 text-[#3b82f6]" />
                                                    ) : (
                                                        <Upload className="h-8 w-8 text-[#3b82f6]" />
                                                    )}
                                                </div>
                                                <p className="mt-3 text-sm font-medium text-gray-700">
                                                    {isDragActive 
                                                        ? 'Solte os arquivos aqui' 
                                                        : files.length > 0 
                                                            ? 'Adicionar mais arquivos' 
                                                            : 'Arraste e solte ou clique para selecionar'}
                                                </p>
                                                <p className="mt-1 text-xs text-gray-400">
                                                    Formatos aceitos: .xlsx, .xls | Máximo: 5 arquivos
                                                </p>
                                            </>
                                        )}
                                    </div>
                                )}

                                {/* Lista de arquivos */}
                                {files.length > 0 && (
                                    <div className="mt-4 space-y-3">
                                        <h3 className="text-sm font-semibold text-gray-600 flex items-center gap-2">
                                            <File className="h-4 w-4" />
                                            Arquivos selecionados
                                        </h3>
                                        {files.map((uploadFile, index) => (
                                            <div 
                                                key={uploadFile.id} 
                                                className="flex items-center gap-4 p-4 glass-card-static border border-gray-200/50 rounded-xl"
                                            >
                                                {/* Indicador de ordem */}
                                                <div className={`w-8 h-8 rounded-lg bg-gradient-to-br ${uploadFile.region ? REGION_COLORS[uploadFile.region] || 'from-gray-400 to-gray-500' : 'from-gray-400 to-gray-500'} flex items-center justify-center text-white font-bold text-sm`}>
                                                    {index + 1}
                                                </div>
                                                
                                                {/* Info do arquivo */}
                                                <div className="flex-1 min-w-0">
                                                    <p className="text-sm font-medium text-gray-900 truncate">{uploadFile.file.name}</p>
                                                    <p className="text-xs text-gray-500">
                                                        {(uploadFile.file.size / 1024).toFixed(1)} KB
                                                    </p>
                                                </div>

                                                {/* Seletor de região */}
                                                <div className="flex items-center gap-2">
                                                    <MapPin className="h-4 w-4 text-gray-400" />
                                                    <select
                                                        value={uploadFile.region}
                                                        onChange={(e) => updateFileRegion(uploadFile.id, e.target.value)}
                                                        className={`text-sm border rounded-lg px-3 py-1.5 bg-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none ${
                                                            !uploadFile.region ? 'border-red-300 bg-red-50' : 'border-gray-200'
                                                        }`}
                                                    >
                                                        <option value="">Selecione região *</option>
                                                        {VALID_REGIONS.map(region => (
                                                            <option 
                                                                key={region} 
                                                                value={region}
                                                                disabled={getUsedRegions().includes(region) && uploadFile.region !== region}
                                                            >
                                                                {region} - {REGION_DESCRIPTIONS[region]}
                                                            </option>
                                                        ))}
                                                    </select>
                                                </div>

                                                {/* Botão remover */}
                                                <button 
                                                    className="p-2 hover:bg-red-50 rounded-lg transition-colors group"
                                                    onClick={() => removeFile(uploadFile.id)}
                                                    title="Remover arquivo"
                                                >
                                                    <Trash2 className="h-4 w-4 text-gray-400 group-hover:text-red-500" />
                                                </button>
                                            </div>
                                        ))}
                                    </div>
                                )}

                                {/* Aviso importante */}
                                {files.length > 0 && (
                                    <div className="mt-4 glass-card-static p-4 border border-amber-200 bg-amber-50/50">
                                        <h4 className="font-semibold text-amber-700 mb-2 flex items-center gap-2">
                                            <AlertCircle className="h-4 w-4" />
                                            Importante
                                        </h4>
                                        <p className="text-sm text-amber-600">
                                            Ao enviar uma planilha, a versão anterior da mesma região será <strong>substituída automaticamente</strong>. 
                                            Apenas uma planilha por região é mantida no sistema.
                                        </p>
                                    </div>
                                )}

                                {/* Dicas de validação */}
                                {files.length > 0 && (
                                    <div className="mt-4 glass-card-static p-4">
                                        <h4 className="font-semibold text-gray-700 mb-3">Antes de enviar, verifique:</h4>
                                        <ul className="space-y-2">
                                            <li className="flex items-center gap-3 text-sm text-gray-600">
                                                <div className="w-5 h-5 rounded-full bg-green-100 flex items-center justify-center">
                                                    <CheckCircle className="h-3.5 w-3.5 text-green-600" />
                                                </div>
                                                Cada planilha contém a aba "Faturamento [REGIÃO]"
                                            </li>
                                            <li className="flex items-center gap-3 text-sm text-gray-600">
                                                <div className="w-5 h-5 rounded-full bg-green-100 flex items-center justify-center">
                                                    <CheckCircle className="h-3.5 w-3.5 text-green-600" />
                                                </div>
                                                Os dados estão na estrutura esperada
                                            </li>
                                            <li className="flex items-center gap-3 text-sm text-gray-600">
                                                <div className="w-5 h-5 rounded-full bg-blue-100 flex items-center justify-center">
                                                    <MapPin className="h-3.5 w-3.5 text-blue-600" />
                                                </div>
                                                Cada arquivo está associado à região correta
                                            </li>
                                        </ul>
                                    </div>
                                )}
                            </>
                        )}

                        {uploadSuccess && (
                            <div className="flex flex-col items-center justify-center p-8 text-center glass-card-static border border-green-200/50">
                                <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-green-400 to-green-600 flex items-center justify-center mb-4">
                                    <CheckCircle className="h-8 w-8 text-white" />
                                </div>
                                <h3 className="text-xl font-bold text-gray-900">Upload realizado com sucesso!</h3>
                                <p className="text-sm text-gray-500 mt-2">
                                    {uploadedJobs.length} arquivo(s) enviado(s). Planilhas anteriores foram substituídas.
                                </p>
                                
                                {/* Lista de jobs criados */}
                                {uploadedJobs.length > 0 && (
                                    <div className="mt-4 w-full max-w-md space-y-2">
                                        {uploadedJobs.map((job, i) => (
                                            <div key={job.id} className="flex items-center gap-3 text-left bg-gray-50 px-4 py-2 rounded-lg">
                                                <div className={`w-6 h-6 rounded bg-gradient-to-br ${job.region ? REGION_COLORS[job.region] : 'from-gray-400 to-gray-500'} flex items-center justify-center text-white text-xs font-bold`}>
                                                    {i + 1}
                                                </div>
                                                <div className="flex-1 min-w-0">
                                                    <p className="text-sm font-medium text-gray-700 truncate">{job.filename}</p>
                                                    <p className="text-xs text-gray-400">
                                                        Região: {job.region} • ID: {job.id}
                                                    </p>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                )}
                                
                                <div className="mt-6 flex gap-3">
                                    <button
                                        className="btn-atlas-secondary"
                                        onClick={() => {
                                            setUploadSuccess(false)
                                            setUploadedJobs([])
                                        }}
                                    >
                                        Enviar outros
                                    </button>
                                    <button
                                        className="btn-atlas-primary"
                                        onClick={() => navigate('/execution')}
                                    >
                                        Ir para Execução
                                    </button>
                                </div>
                            </div>
                        )}

                        {files.length > 0 && !uploadSuccess && (
                            <div className="mt-6 flex justify-between items-center">
                                <button 
                                    className="text-sm text-red-500 hover:text-red-600 flex items-center gap-1"
                                    onClick={() => setFiles([])}
                                >
                                    <Trash2 className="h-4 w-4" />
                                    Limpar todos
                                </button>
                                <div className="flex gap-3">
                                    <button 
                                        className="btn-atlas-secondary"
                                        onClick={() => setFiles([])}
                                    >
                                        Cancelar
                                    </button>
                                    <button 
                                        className="btn-atlas-primary" 
                                        onClick={handleUpload} 
                                        disabled={uploading || files.some(f => !f.region)}
                                    >
                                        {uploading 
                                            ? 'Enviando...' 
                                            : files.length === 1 
                                                ? 'Enviar Planilha' 
                                                : `Enviar ${files.length} Planilhas`}
                                    </button>
                                </div>
                            </div>
                        )}
                    </div>
                </div>

                {/* Região Legend */}
                {files.length > 0 && (
                    <div className="glass-card p-4">
                        <h3 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
                            <MapPin className="h-4 w-4" />
                            Regiões disponíveis
                        </h3>
                        <div className="flex flex-wrap gap-2">
                            {VALID_REGIONS.map(region => {
                                const isUsed = getUsedRegions().includes(region)
                                return (
                                    <div 
                                        key={region}
                                        className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-sm ${
                                            isUsed 
                                                ? 'bg-gray-100 text-gray-400' 
                                                : 'bg-white border border-gray-200 text-gray-700'
                                        }`}
                                    >
                                        <div className={`w-3 h-3 rounded-full bg-gradient-to-br ${REGION_COLORS[region]} ${isUsed ? 'opacity-40' : ''}`} />
                                        <span className={isUsed ? 'line-through' : ''}>
                                            {region} - {REGION_DESCRIPTIONS[region]}
                                        </span>
                                        {isUsed && <CheckCircle className="h-3 w-3 text-green-500" />}
                                    </div>
                                )
                            })}
                        </div>
                    </div>
                )}
            </div>
        </Layout>
    )
}
