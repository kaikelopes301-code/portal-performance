import { useState, useEffect } from 'react'
import { Save, RefreshCw } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import Layout from '@/components/layout/Layout'
import { configService } from '@/services'

export default function ConfigPage() {
    const [loading, setLoading] = useState(false)
    const [fetching, setFetching] = useState(true)

    const [config, setConfig] = useState({
        emailSubject: '',
        emailGreeting: '',
        emailIntro: '',
        senderName: '',
        senderEmail: ''
    })

    const fetchConfig = async () => {
        setFetching(true)
        try {
            const data = await configService.getAll()
            // Mapear dados da API para o estado local
            setConfig({
                emailSubject: data.defaults?.copy_texts?.subject_template || '',
                emailGreeting: data.defaults?.copy_texts?.greeting || '',
                emailIntro: data.defaults?.copy_texts?.intro || '',
                senderName: '', // Será preenchido quando tivermos email config
                senderEmail: ''
            })
        } catch (error) {
            console.error('Failed to fetch config:', error)
        } finally {
            setFetching(false)
        }
    }

    useEffect(() => {
        fetchConfig()
    }, [])

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const { name, value } = e.target
        setConfig(prev => ({ ...prev, [name]: value }))
    }

    const handleSave = async () => {
        setLoading(true)
        try {
            // Por enquanto apenas simula o save
            // TODO: Implementar chamada real quando endpoint estiver completo
            await new Promise(resolve => setTimeout(resolve, 500))
            alert('Configurações salvas!')
        } catch (error) {
            console.error('Failed to save config:', error)
            alert('Erro ao salvar configurações')
        } finally {
            setLoading(false)
        }
    }

    return (
        <Layout>
            <div className="space-y-6">
                <div className="flex justify-between items-center">
                    <div>
                        <h1 className="text-2xl font-bold text-gray-900">Configurações</h1>
                        <p className="mt-1 text-sm text-gray-500">
                            Personalize os textos dos e-mails e informações do remetente.
                        </p>
                    </div>
                    <Button variant="outline" size="sm" onClick={fetchConfig} disabled={fetching}>
                        <RefreshCw className={`h-4 w-4 mr-2 ${fetching ? 'animate-spin' : ''}`} />
                        Atualizar
                    </Button>
                </div>

                {fetching ? (
                    <div className="text-center py-12 text-gray-500">Carregando configurações...</div>
                ) : (
                    <div className="grid gap-6">
                    <Card>
                        <CardHeader>
                            <CardTitle>Remetente</CardTitle>
                            <CardDescription>
                                Informações que aparecerão no cabeçalho dos e-mails enviados.
                            </CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div className="space-y-2">
                                    <label className="text-sm font-medium text-gray-700">Nome de Exibição</label>
                                    <Input
                                        name="senderName"
                                        value={config.senderName}
                                        onChange={handleChange}
                                        placeholder="Ex: Financeiro Atlas"
                                    />
                                </div>
                                <div className="space-y-2">
                                    <label className="text-sm font-medium text-gray-700">E-mail de Envio</label>
                                    <Input
                                        name="senderEmail"
                                        value={config.senderEmail}
                                        onChange={handleChange}
                                        placeholder="Ex: financeiro@atlas.com"
                                    />
                                </div>
                            </div>
                        </CardContent>
                    </Card>

                    <Card>
                        <CardHeader>
                            <CardTitle>Modelos de E-mail</CardTitle>
                            <CardDescription>
                                Personalize o conteúdo das mensagens. Use {'{variaveis}'} para conteúdo dinâmico.
                            </CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <div className="space-y-2">
                                <label className="text-sm font-medium text-gray-700">Assunto do E-mail</label>
                                <Input
                                    name="emailSubject"
                                    value={config.emailSubject}
                                    onChange={handleChange}
                                />
                                <p className="text-xs text-gray-500">Variáveis disponíveis: {'{unidade}'}, {'{mes_ref}'}, {'{mes_extenso}'}</p>
                            </div>

                            <div className="space-y-2">
                                <label className="text-sm font-medium text-gray-700">Saudação</label>
                                <Input
                                    name="emailGreeting"
                                    value={config.emailGreeting}
                                    onChange={handleChange}
                                />
                            </div>

                            <div className="space-y-2">
                                <label className="text-sm font-medium text-gray-700">Texto Introdutório</label>
                                <Input
                                    name="emailIntro"
                                    value={config.emailIntro}
                                    onChange={handleChange}
                                />
                            </div>
                        </CardContent>
                    </Card>

                    <div className="flex justify-end">
                        <Button onClick={handleSave} disabled={loading} className="w-full sm:w-auto">
                            {loading ? (
                                <span className="flex items-center">Salvando...</span>
                            ) : (
                                <span className="flex items-center">
                                    <Save className="mr-2 h-4 w-4" /> Salvar Alterações
                                </span>
                            )}
                        </Button>
                    </div>
                </div>
                )}
            </div>
        </Layout>
    )
}
