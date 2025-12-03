# Sistema de Performance - Instruções de Execução

## 📋 Resumo das Implementações

### Backend (FastAPI)

1. **`backend/app/core/__init__.py`**: Wrapper que importa os módulos core da raiz do projeto:
   - `Extractor` - Leitura de planilhas Excel
   - `filter_and_prepare`, `map_columns` - Processamento de dados
   - `Emailer` - Geração de HTML e envio de emails
   - `utils` - Utilitários diversos

2. **`backend/app/services/pipeline_service.py`**: Serviço que orquestra o fluxo completo:
   - `execute()` - Executa o pipeline para uma unidade
   - `list_available_units()` - Lista unidades de uma região
   - `list_available_months()` - Lista meses disponíveis
   - `list_available_regions()` - Lista regiões com planilhas

3. **Novos endpoints em `backend/app/routers/process.py`**:
   - `POST /api/process/execute` - Executa o pipeline para uma unidade
   - `POST /api/process/execute/batch` - Executa em lote para múltiplas unidades
   - `GET /api/process/metadata/regions` - Lista regiões disponíveis
   - `GET /api/process/metadata/{region}` - Lista unidades e meses de uma região

### Frontend (React + TypeScript)

1. **`ExecutionPage.tsx`** atualizado para:
   - Chamar a API real `/api/process/execute`
   - Mostrar progresso real de processamento
   - Exibir logs com contagem de linhas e emails encontrados

2. **`SettingsPage.tsx`** atualizado para:
   - Salvar configurações via API
   - Suporte a escopo (padrão ou por unidade)
   - Seletor de unidades personalizadas

---

## 🚀 Como Executar

### 1. Ativar o ambiente virtual
```powershell
cd c:\backpperformance
.\.venv\Scripts\Activate
```

### 2. Iniciar o Backend
```powershell
cd c:\backpperformance\backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### 3. Iniciar o Frontend (em outro terminal)
```powershell
cd c:\backpperformance\frontend
npm run dev
```

### 4. Acessar o sistema
- **Frontend**: http://localhost:5173
- **Backend (Docs)**: http://localhost:8000/docs

---

## 🧪 Testar o Pipeline

### Via Script
```powershell
cd c:\backpperformance\backend
python scripts/test_pipeline.py
```

### Via API (Swagger)
1. Acesse http://localhost:8000/docs
2. Expanda `POST /api/process/execute`
3. Clique em "Try it out"
4. Use este payload:
```json
{
  "region": "RJ",
  "unit": "Bangu Shopping",
  "month": "2025-11",
  "dry_run": true,
  "send_email": false
}
```
5. Clique "Execute"

---

## 📧 Configurar SendGrid para Envio Real

1. Crie um arquivo `.env` na raiz do projeto:
```env
SENDGRID_API_KEY=sua_chave_aqui
SENDGRID_FROM_EMAIL=seu@email.com
SENDGRID_FROM_NAME=Equipe Financeira
```

2. Para enviar emails reais, use:
```json
{
  "region": "RJ",
  "unit": "Bangu Shopping",
  "month": "2025-11",
  "dry_run": false,
  "send_email": true
}
```

---

## 📁 Estrutura de Arquivos

```
backpperformance/
├── planilhas/              # Planilhas Excel por região
│   ├── *_RJ_2025.xlsx
│   ├── *_SP1_2025.xlsx
│   └── ...
├── output_html/            # HTMLs gerados (saída)
├── templates/              # Templates de email (Jinja2)
│   └── email_template_dark.html
├── config/
│   └── overrides.json      # Configurações (defaults → regions → units)
├── backend/
│   ├── app/
│   │   ├── core/           # Wrapper para módulos da raiz
│   │   ├── services/
│   │   │   ├── config_service.py
│   │   │   └── pipeline_service.py
│   │   └── routers/
│   │       └── process.py
│   └── scripts/
│       └── test_pipeline.py
└── frontend/
    └── src/
        └── pages/
            ├── ExecutionPage.tsx
            └── SettingsPage.tsx
```

---

## 🔧 Fluxo do Pipeline

1. **Localiza Planilha**: `Extractor.find_workbook(region)` busca em `planilhas/`
2. **Lê Dados**: `Extractor.read_region_sheet()` lê a aba "Faturamento {REGIÃO}"
3. **Filtra**: `filter_and_prepare()` filtra por unidade e mês
4. **Gera HTML**: `Emailer.render_html()` usa `email_template_dark.html`
5. **Salva**: Escreve em `output_html/{unit}_{month}.html`
6. **Envia** (opcional): `SendGrid` envia para os emails encontrados

---

## ⚙️ Configurações Hierárquicas

O sistema suporta configurações em 3 níveis (sobrescrita em cascata):

1. **defaults**: Aplica a todas as unidades
2. **regions**: Sobrescreve defaults para uma região
3. **units**: Sobrescreve tudo para uma unidade específica

Exemplo de `config/overrides.json`:
```json
{
  "defaults": {
    "visible_columns": ["Unidade", "Fornecedor", "Valor Mensal Final"],
    "month_reference": "auto"
  },
  "regions": {
    "RJ": { "copy": { "saudacao": "Prezados colegas do RJ" } }
  },
  "units": {
    "Bangu Shopping": { "visible_columns": ["Unidade", "Categoria", "Fornecedor"] }
  }
}
```
