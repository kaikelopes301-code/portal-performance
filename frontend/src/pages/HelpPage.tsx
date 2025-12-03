import { useState } from 'react'
import { HelpCircle, ChevronDown, ChevronRight, Mail, FileSpreadsheet, Settings, Send, Eye, AlertTriangle, CheckCircle, ExternalLink, BookOpen, MessageCircle } from 'lucide-react'
import Layout from '@/components/layout/Layout'

// FAQ Items
const FAQ_ITEMS = [
    {
        category: 'Geral',
        questions: [
            {
                q: 'O que é o Portal Performance?',
                a: 'O Portal Performance é um sistema automatizado para envio de relatórios de medição mensal para shoppings. Ele processa planilhas Excel, gera relatórios HTML formatados e envia por email para os gestores de cada unidade.'
            },
            {
                q: 'Quais formatos de arquivo são suportados?',
                a: 'O sistema aceita arquivos Excel nos formatos .xlsx e .xls. A planilha deve conter uma aba com o nome "Faturamento {REGIÃO}" (ex: "Faturamento RJ", "Faturamento SP1").'
            },
            {
                q: 'Como são organizadas as regiões?',
                a: 'Os shoppings são divididos em 5 regiões: SP1 (São Paulo Capital - Zona Sul/Leste), SP2 (São Paulo - ABC/Metropolitana), SP3 (São Paulo Interior + Paraná), RJ (Rio de Janeiro) e NNE (Norte e Nordeste).'
            }
        ]
    },
    {
        category: 'Envio de Emails',
        questions: [
            {
                q: 'Como enviar medições para múltiplas unidades?',
                a: 'Na página de Execução, selecione as unidades desejadas clicando nelas ou use o botão "Selecionar Todas" em cada região. Depois clique em "Enviar Emails". O sistema processará cada unidade individualmente e mostrará o progresso.'
            },
            {
                q: 'Posso enviar para uma única unidade?',
                a: 'Sim! Basta selecionar apenas a unidade desejada e clicar em enviar. Você também pode usar a página de Preview para visualizar o email antes de enviar.'
            },
            {
                q: 'O que fazer se um envio falhar?',
                a: 'Se um envio falhar, o status da unidade aparecerá em vermelho. Você pode tentar novamente selecionando apenas as unidades com erro e clicando em enviar novamente. Verifique também a conexão com a internet e as configurações de email.'
            },
            {
                q: 'Como funciona o modo de teste?',
                a: 'O modo de teste gera os arquivos HTML normalmente, mas não envia os emails. É útil para verificar se os relatórios estão corretos antes do envio real. Ative-o em Configurações > Email.'
            }
        ]
    },
    {
        category: 'Configurações',
        questions: [
            {
                q: 'Como alterar as colunas do relatório?',
                a: 'Acesse Configurações > Colunas do Relatório. Você pode ativar/desativar colunas e reordenar arrastando. Algumas colunas são obrigatórias e não podem ser desativadas.'
            },
            {
                q: 'Como definir o mês de referência?',
                a: 'Em Configurações > Mês de Referência, escolha entre modo Automático (usa o mês anterior) ou Fixo (define um mês específico). Você também pode sobrescrever o mês na página de Execução.'
            },
            {
                q: 'Como configurar o SendGrid?',
                a: 'Adicione sua API Key do SendGrid no arquivo .env na raiz do projeto: SENDGRID_API_KEY=SG.sua_chave. Depois configure o email do remetente em Configurações > Email.'
            }
        ]
    },
    {
        category: 'Troubleshooting',
        questions: [
            {
                q: 'A planilha não está sendo lida corretamente',
                a: 'Verifique se: 1) O arquivo não está aberto no Excel, 2) A aba tem o nome correto "Faturamento {REGIÃO}", 3) Os cabeçalhos das colunas estão na primeira linha, 4) Não há linhas vazias no início.'
            },
            {
                q: 'Os valores estão aparecendo errados no relatório',
                a: 'Verifique o formato das células na planilha. Valores monetários devem estar em formato brasileiro (R$ 1.234,56). Datas devem estar no formato DD/MM/AAAA.'
            },
            {
                q: 'O email não está chegando para os destinatários',
                a: 'Verifique: 1) Se o email do destinatário está correto, 2) Se o SendGrid está configurado corretamente, 3) Se o email não caiu na pasta de spam. Você pode verificar o status dos envios no painel do SendGrid.'
            }
        ]
    }
]

// Guia Rápido Steps
const QUICK_GUIDE_STEPS = [
    {
        step: 1,
        title: 'Prepare a Planilha',
        description: 'Certifique-se que a planilha Excel contém a aba correta com os dados de medição.',
        icon: FileSpreadsheet
    },
    {
        step: 2,
        title: 'Configure as Opções',
        description: 'Ajuste o mês de referência e as colunas que aparecerão no relatório.',
        icon: Settings
    },
    {
        step: 3,
        title: 'Visualize o Preview',
        description: 'Confira como ficará o email antes de enviar para os destinatários.',
        icon: Eye
    },
    {
        step: 4,
        title: 'Envie as Medições',
        description: 'Selecione as unidades e envie os relatórios por email.',
        icon: Send
    }
]

export default function HelpPage() {
    const [expandedCategory, setExpandedCategory] = useState<string | null>('Geral')
    const [expandedQuestion, setExpandedQuestion] = useState<string | null>(null)

    return (
        <Layout>
            <div className="space-y-8 animate-fade-in-up">
                {/* Hero Section */}
                <div className="hero-glass">
                    <div className="relative z-10">
                        <h1 className="text-3xl font-bold text-white mb-2 flex items-center gap-3">
                            <HelpCircle className="h-8 w-8" />
                            Central de Ajuda
                        </h1>
                        <p className="text-blue-100 text-lg">
                            Encontre respostas para suas dúvidas e aprenda a usar o sistema.
                        </p>
                    </div>
                </div>

                {/* Quick Start Guide */}
                <div className="glass-card p-0 overflow-hidden">
                    <div className="p-6 border-b border-gray-200/50">
                        <h2 className="text-xl font-bold text-[#2F4F71] flex items-center gap-2">
                            <BookOpen className="h-6 w-6 text-[#3b82f6]" />
                            Guia Rápido
                        </h2>
                        <p className="text-gray-500 mt-1">4 passos para enviar suas medições</p>
                    </div>
                    <div className="p-6">
                        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                            {QUICK_GUIDE_STEPS.map((item, idx) => (
                                <div key={item.step} className="relative">
                                    <div className="glass-card-static p-4 h-full">
                                        <div className="flex items-center gap-3 mb-3">
                                            <div className="w-10 h-10 bg-gradient-to-br from-[#3b82f6] to-[#2563eb] text-white rounded-xl flex items-center justify-center font-bold shadow-lg">
                                                {item.step}
                                            </div>
                                            <item.icon className="h-5 w-5 text-[#3b82f6]" />
                                        </div>
                                        <h3 className="font-semibold text-gray-900 mb-1">{item.title}</h3>
                                        <p className="text-sm text-gray-500">{item.description}</p>
                                    </div>
                                    {idx < QUICK_GUIDE_STEPS.length - 1 && (
                                        <div className="hidden md:block absolute top-1/2 -right-2 transform -translate-y-1/2 z-10">
                                            <ChevronRight className="h-5 w-5 text-[#3b82f6]" />
                                        </div>
                                    )}
                                </div>
                            ))}
                        </div>
                    </div>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    {/* FAQ */}
                    <div className="lg:col-span-2 space-y-4">
                        <h2 className="text-lg font-bold text-[#2F4F71] flex items-center gap-2">
                            <HelpCircle className="h-5 w-5 text-[#3b82f6]" />
                            Perguntas Frequentes
                        </h2>

                        {FAQ_ITEMS.map(category => (
                            <div key={category.category} className="accordion-glass overflow-hidden">
                                <button
                                    onClick={() => setExpandedCategory(
                                        expandedCategory === category.category ? null : category.category
                                    )}
                                    className="w-full p-4 flex items-center justify-between hover:bg-white/50 transition-colors"
                                >
                                    <span className="font-semibold text-gray-900">{category.category}</span>
                                    {expandedCategory === category.category ? (
                                        <ChevronDown className="h-5 w-5 text-[#3b82f6]" />
                                    ) : (
                                        <ChevronRight className="h-5 w-5 text-gray-400" />
                                    )}
                                </button>

                                {expandedCategory === category.category && (
                                    <div className="border-t border-gray-200/50">
                                        {category.questions.map((item, idx) => (
                                            <div key={idx} className="border-b border-gray-100 last:border-b-0">
                                                <button
                                                    onClick={() => setExpandedQuestion(
                                                        expandedQuestion === item.q ? null : item.q
                                                    )}
                                                    className="w-full p-4 flex items-start justify-between text-left hover:bg-white/30 transition-colors"
                                                >
                                                    <span className="text-sm font-medium text-gray-800 pr-4">
                                                        {item.q}
                                                    </span>
                                                    {expandedQuestion === item.q ? (
                                                        <ChevronDown className="h-4 w-4 text-[#3b82f6] flex-shrink-0 mt-0.5" />
                                                    ) : (
                                                        <ChevronRight className="h-4 w-4 text-gray-400 flex-shrink-0 mt-0.5" />
                                                    )}
                                                </button>
                                                {expandedQuestion === item.q && (
                                                    <div className="px-4 pb-4">
                                                        <p className="text-sm text-gray-600 glass-card-static p-4">
                                                            {item.a}
                                                        </p>
                                                    </div>
                                                )}
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>

                    {/* Sidebar */}
                    <div className="space-y-4">
                        {/* Dicas */}
                        <div className="glass-card p-0 overflow-hidden">
                            <div className="p-4 border-b border-gray-200/50">
                                <h3 className="font-semibold text-gray-900 flex items-center gap-2">
                                    <CheckCircle className="h-5 w-5 text-green-500" />
                                    Dicas Importantes
                                </h3>
                            </div>
                            <div className="p-4 space-y-3">
                                {[
                                    'Sempre faça um preview antes de enviar em massa',
                                    'Verifique o mês de referência antes de cada envio',
                                    'Mantenha a planilha fechada durante o processamento',
                                    'Use o modo teste para validar configurações'
                                ].map((tip, idx) => (
                                    <div key={idx} className="flex items-start gap-3 text-sm">
                                        <div className="w-5 h-5 rounded-full bg-green-100 flex items-center justify-center flex-shrink-0 mt-0.5">
                                            <CheckCircle className="h-3 w-3 text-green-600" />
                                        </div>
                                        <p className="text-gray-600">{tip}</p>
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* Avisos */}
                        <div className="glass-card p-0 overflow-hidden border-amber-200/50">
                            <div className="p-4 border-b border-amber-200/50 bg-amber-50/50">
                                <h3 className="font-semibold text-amber-800 flex items-center gap-2">
                                    <AlertTriangle className="h-5 w-5" />
                                    Avisos
                                </h3>
                            </div>
                            <div className="p-4 space-y-2 text-sm text-amber-700 bg-amber-50/30">
                                <p>• Não feche o navegador durante o envio</p>
                                <p>• Emails enviados não podem ser cancelados</p>
                                <p>• Limite de 100 envios por hora (SendGrid)</p>
                            </div>
                        </div>

                        {/* Suporte */}
                        <div className="glass-card p-0 overflow-hidden">
                            <div className="p-4 border-b border-gray-200/50">
                                <h3 className="font-semibold text-gray-900 flex items-center gap-2">
                                    <MessageCircle className="h-5 w-5 text-[#3b82f6]" />
                                    Precisa de Ajuda?
                                </h3>
                            </div>
                            <div className="p-4 space-y-4">
                                <p className="text-sm text-gray-600">
                                    Entre em contato com o suporte técnico:
                                </p>
                                <a 
                                    href="mailto:kaike.costa@atlasinovacoes.com.br"
                                    className="flex items-center gap-2 text-sm text-[#3b82f6] hover:text-[#2563eb] font-medium"
                                >
                                    <Mail className="h-4 w-4" />
                                    kaike.costa@atlasinovacoes.com.br
                                </a>
                                <button className="btn-atlas-secondary w-full text-sm">
                                    <ExternalLink className="h-4 w-4 mr-2" />
                                    Documentação Completa
                                </button>
                            </div>
                        </div>

                        {/* Versão */}
                        <div className="text-center text-xs text-gray-400 py-4">
                            <p>Portal Performance v2.0</p>
                            <p>© 2025 Atlas Inovações</p>
                        </div>
                    </div>
                </div>
            </div>
        </Layout>
    )
}
