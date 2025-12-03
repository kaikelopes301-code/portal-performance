import { useEffect, useState } from 'react'
import { FileText, Eye, Check, Star } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import Layout from '@/components/layout/Layout'
import { templateService } from '@/services'
import type { Template } from '@/types'

export default function TemplatesPage() {
    const [templates, setTemplates] = useState<Template[]>([])
    const [loading, setLoading] = useState(true)
    const [previewHtml, setPreviewHtml] = useState<string | null>(null)
    const [previewingId, setPreviewingId] = useState<string | null>(null)

    const fetchTemplates = async () => {
        try {
            const data = await templateService.list()
            setTemplates(data.templates)
        } catch (error) {
            console.error('Failed to fetch templates:', error)
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => {
        fetchTemplates()
    }, [])

    const handlePreview = async (templateId: string) => {
        setPreviewingId(templateId)
        try {
            const data = await templateService.preview(templateId)
            setPreviewHtml(data.html)
        } catch (error) {
            console.error('Failed to preview template:', error)
            alert('Erro ao carregar preview')
        } finally {
            setPreviewingId(null)
        }
    }

    const handleSetDefault = async (templateId: string) => {
        try {
            await templateService.setDefault(templateId)
            // Atualiza lista para refletir mudança
            fetchTemplates()
        } catch (error) {
            console.error('Failed to set default template:', error)
            alert('Erro ao definir template padrão')
        }
    }

    return (
        <Layout>
            <div className="space-y-6">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900">Templates de Email</h1>
                    <p className="mt-1 text-sm text-gray-500">
                        Gerencie os modelos de e-mail utilizados nos relatórios.
                    </p>
                </div>

                <div className="grid gap-6 md:grid-cols-2">
                    {/* Lista de Templates */}
                    <div className="space-y-4">
                        <h2 className="text-lg font-medium text-gray-900">Templates Disponíveis</h2>

                        {loading ? (
                            <div className="text-center py-8 text-gray-500">Carregando...</div>
                        ) : templates.length === 0 ? (
                            <div className="text-center py-8 text-gray-500">
                                Nenhum template encontrado.
                            </div>
                        ) : (
                            templates.map((template) => (
                                <Card key={template.id} className={template.is_active ? 'ring-2 ring-blue-500' : ''}>
                                    <CardContent className="p-4">
                                        <div className="flex items-start justify-between">
                                            <div className="flex items-start space-x-3">
                                                <div className="p-2 bg-blue-100 rounded-lg">
                                                    <FileText className="h-5 w-5 text-blue-600" />
                                                </div>
                                                <div>
                                                    <div className="flex items-center space-x-2">
                                                        <h3 className="text-sm font-medium text-gray-900">
                                                            {template.name}
                                                        </h3>
                                                        {template.is_active && (
                                                            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">
                                                                <Star className="h-3 w-3 mr-1" />
                                                                Padrão
                                                            </span>
                                                        )}
                                                    </div>
                                                    {template.description && (
                                                        <p className="text-xs text-gray-500 mt-1">
                                                            {template.description}
                                                        </p>
                                                    )}
                                                    <p className="text-xs text-gray-400 mt-1">
                                                        Assunto: {template.subject_template}
                                                    </p>
                                                </div>
                                            </div>
                                        </div>

                                        <div className="mt-4 flex items-center space-x-2">
                                            <Button
                                                variant="outline"
                                                size="sm"
                                                onClick={() => handlePreview(template.id)}
                                                disabled={previewingId === template.id}
                                            >
                                                <Eye className="h-4 w-4 mr-1" />
                                                {previewingId === template.id ? 'Carregando...' : 'Preview'}
                                            </Button>

                                            {!template.is_active && (
                                                <Button
                                                    variant="outline"
                                                    size="sm"
                                                    onClick={() => handleSetDefault(template.id)}
                                                >
                                                    <Check className="h-4 w-4 mr-1" />
                                                    Definir como Padrão
                                                </Button>
                                            )}
                                        </div>
                                    </CardContent>
                                </Card>
                            ))
                        )}
                    </div>

                    {/* Preview */}
                    <div>
                        <Card className="sticky top-6">
                            <CardHeader>
                                <CardTitle>Preview</CardTitle>
                                <CardDescription>
                                    Visualização do template selecionado
                                </CardDescription>
                            </CardHeader>
                            <CardContent>
                                {previewHtml ? (
                                    <div className="border rounded-lg overflow-hidden bg-white">
                                        <iframe
                                            srcDoc={previewHtml}
                                            className="w-full h-[500px]"
                                            title="Template Preview"
                                            sandbox="allow-same-origin"
                                        />
                                    </div>
                                ) : (
                                    <div className="flex items-center justify-center h-64 bg-gray-50 rounded-lg border-2 border-dashed border-gray-200">
                                        <p className="text-sm text-gray-500">
                                            Selecione um template para visualizar
                                        </p>
                                    </div>
                                )}
                            </CardContent>
                        </Card>
                    </div>
                </div>
            </div>
        </Layout>
    )
}
