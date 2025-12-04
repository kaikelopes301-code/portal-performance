// Dados completos de todas as unidades/shoppings por região

export interface Unit {
    id: string
    name: string
    email: string
    region: string
}

export interface Region {
    code: string
    name: string
    units: Unit[]
}

// Lista completa de shoppings por região
export const REGIONS_DATA: Region[] = [
    {
        code: 'RJ',
        name: 'Regional RJ',
        units: [
            { id: 'rj-bangu', name: 'Bangu Shopping', email: 'bangu@exemplo.com', region: 'RJ' },
            { id: 'rj-carioca', name: 'Carioca Shopping', email: 'carioca@exemplo.com', region: 'RJ' },
            { id: 'rj-caxias', name: 'Caxias Shopping', email: 'caxias@exemplo.com', region: 'RJ' },
            { id: 'rj-independencia', name: 'Independência Shopping', email: 'independencia@exemplo.com', region: 'RJ' },
            { id: 'rj-norte', name: 'Norte Shopping', email: 'norte@exemplo.com', region: 'RJ' },
            { id: 'rj-passeio', name: 'Passeio Shopping', email: 'passeio@exemplo.com', region: 'RJ' },
            { id: 'rj-recreio', name: 'Recreio Shopping', email: 'recreio@exemplo.com', region: 'RJ' },
            { id: 'rj-riodesign', name: 'Rio Design Leblon', email: 'riodesign@exemplo.com', region: 'RJ' },
            { id: 'rj-granderio', name: 'Shopping Grande Rio', email: 'granderio@exemplo.com', region: 'RJ' },
            { id: 'rj-leblon', name: 'Shopping Leblon', email: 'leblon@exemplo.com', region: 'RJ' },
            { id: 'rj-vilavelha', name: 'Shopping Vila Velha', email: 'vilavelha@exemplo.com', region: 'RJ' },
           
        ]
    },
    {
        code: 'SP1',
        name: 'Regional SP1',
        units: [
            { id: 'sp1-londrina', name: 'Catuaí Shopping Londrina', email: 'londrina@exemplo.com', region: 'SP1' },
            { id: 'sp1-maringa', name: 'Catuaí Shopping Maringá', email: 'maringa@exemplo.com', region: 'SP1' },
            { id: 'sp1-saobernardo', name: 'São Bernardo Plaza Shopping', email: 'saobernardo@exemplo.com', region: 'SP1' },
            { id: 'sp1-campogrande', name: 'Shopping Campo Grande', email: 'campogrande@exemplo.com', region: 'SP1' },
            { id: 'sp1-curitiba', name: 'Shopping Curitiba', email: 'curitiba@exemplo.com', region: 'SP1' },
            { id: 'sp1-goiania', name: 'Shopping Goiânia', email: 'goiania@exemplo.com', region: 'SP1' },
            { id: 'sp1-metropole', name: 'Shopping Metrópole', email: 'metropole@exemplo.com', region: 'SP1' },
            { id: 'sp1-passeioaguas', name: 'Shopping Passeio das Águas', email: 'passeioaguas@exemplo.com', region: 'SP1' },
            { id: 'sp1-tambore', name: 'Shopping Tamboré', email: 'tambore@exemplo.com', region: 'SP1' },
        ]
    },
    {
        code: 'NNE',
        name: 'Regional NNE',
        units: [
            { id: 'nne-amazonas', name: 'Amazonas Shopping', email: 'amazonas@exemplo.com', region: 'NNE' },
            { id: 'nne-boulevardbelem', name: 'Boulevard Belém', email: 'boulevardbelem@exemplo.com', region: 'NNE' },
            { id: 'nne-boulevardfeira', name: 'Boulevard Feira de Santana', email: 'boulevardfeira@exemplo.com', region: 'NNE' },
            { id: 'nne-cariri', name: 'Cariri Shopping', email: 'cariri@exemplo.com', region: 'NNE' },
            { id: 'nne-manauara', name: 'Manauara Shopping', email: 'manauara@exemplo.com', region: 'NNE' },
            { id: 'nne-parquebelem', name: 'Parque Shopping Belém', email: 'parquebelem@exemplo.com', region: 'NNE' },
            { id: 'nne-bahia', name: 'Shopping da Bahia', email: 'bahia@exemplo.com', region: 'NNE' },
            { id: 'nne-parangaba', name: 'Shopping Parangaba', email: 'parangaba@exemplo.com', region: 'NNE' },
            { id: 'nne-plazasul', name: 'Shopping Plaza Sul', email: 'plazasul@exemplo.com', region: 'NNE' },
            { id: 'nne-rioanil', name: 'Shopping Rio Anil', email: 'rioanil@exemplo.com', region: 'NNE' },
            { id: 'nne-taboao', name: 'Shopping Taboão', email: 'taboao@exemplo.com', region: 'NNE' },
        ]
    },
    {
        code: 'SP2',
        name: 'Regional SP2',
        units: [
            { id: 'sp2-boulevardbauru', name: 'Boulevard Bauru', email: 'boulevardbauru@exemplo.com', region: 'SP2' },
            { id: 'sp2-franca', name: 'Franca Shopping', email: 'franca@exemplo.com', region: 'SP2' },
            { id: 'sp2-pracanovaaracatuba', name: 'Praça Nova Araçatuba', email: 'pracanovaaracatuba@exemplo.com', region: 'SP2' },
            { id: 'sp2-pracanovasantamaria', name: 'Praça Nova Santa Maria', email: 'pracanovasantamaria@exemplo.com', region: 'SP2' },
            { id: 'sp2-campolimpo', name: 'Shopping Campo Limpo', email: 'campolimpo@exemplo.com', region: 'SP2' },
            { id: 'sp2-dompedro', name: 'Shopping Parque Dom Pedro', email: 'dompedro@exemplo.com', region: 'SP2' },
            { id: 'sp2-piracicaba', name: 'Shopping Piracicaba', email: 'piracicaba@exemplo.com', region: 'SP2' },
            { id: 'sp2-villalobos', name: 'Shopping Villa Lobos', email: 'villalobos@exemplo.com', region: 'SP2' },
            { id: 'sp2-villagiocaxias', name: 'Shopping Villagio Caxias', email: 'villagiocaxias@exemplo.com', region: 'SP2' },
        ]
    },
    {
        code: 'SP3',
        name: 'Regional SP3',
        units: [
            { id: 'sp3-boulevardbh', name: 'Boulevard BH', email: 'boulevardbh@exemplo.com', region: 'SP3' },
            { id: 'sp3-centeruberlandia', name: 'Center Shopping Uberlândia', email: 'centeruberlandia@exemplo.com', region: 'SP3' },
            { id: 'sp3-mooca', name: 'Mooca Plaza Shopping', email: 'mooca@exemplo.com', region: 'SP3' },
            { id: 'sp3-delrey', name: 'Shopping Del Rey', email: 'delrey@exemplo.com', region: 'SP3' },
            { id: 'sp3-estacaobh', name: 'Shopping Estação BH', email: 'estacaobh@exemplo.com', region: 'SP3' },
            { id: 'sp3-estacaocuiaba', name: 'Shopping Estação Cuiabá', email: 'estacaocuiaba@exemplo.com', region: 'SP3' },
            { id: 'sp3-metrosantacruz', name: 'Shopping Metrô Santa Cruz', email: 'metrosantacruz@exemplo.com', region: 'SP3' },
        ]
    },
]

// Helper para obter todas as unidades
export const getAllUnits = (): Unit[] => {
    return REGIONS_DATA.flatMap(region => region.units)
}

// Helper para obter unidades por região
export const getUnitsByRegion = (regionCode: string): Unit[] => {
    const region = REGIONS_DATA.find(r => r.code === regionCode)
    return region ? region.units : []
}

// Helper para obter uma unidade pelo ID
export const getUnitById = (unitId: string): Unit | undefined => {
    return getAllUnits().find(u => u.id === unitId)
}

// Total de unidades
export const TOTAL_UNITS = getAllUnits().length

// ==========================================
// COLUNAS DO RELATÓRIO
// ==========================================

export interface ColumnConfig {
    id: string
    name: string
    description: string
    required: boolean
}

// COLUNAS PADRÃO (sempre visíveis no relatório)
export const STANDARD_COLUMNS: ColumnConfig[] = [
    { id: 'unidade', name: 'Unidade', description: 'Nome do shopping', required: true },
    { id: 'categoria', name: 'Categoria', description: 'Tipo de serviço (Segurança, Limpeza, etc)', required: true },
    { id: 'fornecedor', name: 'Fornecedor', description: 'Nome da empresa prestadora', required: true },
    { id: 'hc_planilha', name: 'HC Planilha', description: 'Headcount conforme planilha', required: true },
    { id: 'dias_faltas', name: 'Dias Faltas', description: 'Quantidade de dias com faltas', required: true },
    { id: 'horas_atrasos', name: 'Horas Atrasos', description: 'Total de horas de atrasos', required: true },
    { id: 'valor_planilha', name: 'Valor Planilha', description: 'Valor original da planilha', required: true },
    { id: 'desc_falta', name: 'Desc. Falta Validado Atlas', description: 'Desconto por faltas validado', required: true },
    { id: 'desc_atraso', name: 'Desc. Atraso Validado Atlas', description: 'Desconto por atrasos validado', required: true },
    { id: 'desc_sla', name: 'Desconto SLA Mês', description: 'Desconto de SLA mensal', required: true },
    { id: 'valor_mensal_final', name: 'Valor Mensal Final', description: 'Valor final após descontos', required: true },
    { id: 'mes_ref', name: 'Mês de referência para faturamento', description: 'Competência da medição', required: true },
    { id: 'mes_emissao', name: 'Mês de emissão da NF', description: 'Mês de emissão da nota fiscal', required: true },
]

// COLUNAS EXTRAS (opcionais, podem ser ativadas conforme necessidade)
export const EXTRA_COLUMNS: ColumnConfig[] = [
    { id: 'desc_sla_retroativo', name: 'Desconto SLA Retroativo', description: 'Desconto SLA de meses anteriores', required: false },
    { id: 'desc_equipamentos', name: 'Desconto Equipamentos', description: 'Desconto de equipamentos', required: false },
    { id: 'premio_assiduidade', name: 'Prêmio Assiduidade', description: 'Bônus por assiduidade', required: false },
    { id: 'outros_descontos', name: 'Outros descontos', description: 'Outros descontos aplicados', required: false },
    { id: 'taxa_prorrogacao', name: 'Taxa de prorrogação do prazo pagamento', description: 'Taxa aplicada na prorrogação', required: false },
    { id: 'valor_prorrogacao', name: 'Valor mensal com prorrogação do prazo pagamento', description: 'Valor com prorrogação incluída', required: false },
    { id: 'retroativo_dissidio', name: 'Retroativo de dissídio', description: 'Valor retroativo de dissídio', required: false },
    { id: 'parcela', name: 'Parcela (x/x)', description: 'Número da parcela', required: false },
    { id: 'valor_extras', name: 'Valor extras validado Atlas', description: 'Valores extras validados', required: false },
]

// Todas as colunas
export const ALL_COLUMNS = [...STANDARD_COLUMNS, ...EXTRA_COLUMNS]
