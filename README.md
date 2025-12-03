# Portal Performance - Sistema de Faturamento

**Sistema automatizado de envio de medições** para shoppings, com interface web moderna e API REST.

## 🚀 Início Rápido

### Windows (Recomendado)
```bash
# Clique duplo em start.bat ou execute:
start.bat
```

O script irá:
1. ✅ Verificar Python e Node.js
2. ✅ Criar ambiente virtual (se necessário)
3. ✅ Instalar dependências automaticamente
4. ✅ Iniciar Backend (http://localhost:8000)
5. ✅ Iniciar Frontend (http://localhost:5173)
6. ✅ Abrir navegador

### Manual
```bash
# Backend
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend (novo terminal)
cd frontend
npm install
npm run dev
```

## Requisitos
- Python 3.10+
- Node.js 18+
- **Para envio via SendGrid** (recomendado): API Key do SendGrid ([ver guia](SENDGRID_CONFIG.md))
- **Para envio via Outlook**: Windows com Outlook instalado

## Estrutura
```text
faturamento_email/
├── main.py
├── extractor.py
├── processor.py
├── emailer.py
├── utils.py
├── templates/
│   └── email_template_dark.html
├── assets/
│   └── logo-atlas.png
├── output_html/
├── faturamento_logs.db  # (criado na primeira execução)
├── .env
└── requirements.txt
```

> Caso já possua um `.env` corporativo, substitua o arquivo incluído aqui pelo seu. As chaves mais importantes: `SENDER_EMAIL`, `SENDER_NAME`, `SLA_URL`, `USE_TEST_SUBJECT`, `UNIT_EXCEPTIONS`, `ATTACH_FILTERED_XLSX` e cores de marca.

## 📧 Configuração de Envio de E-mails

O sistema suporta dois métodos de envio:

### Método 1: SendGrid (Recomendado - Multiplataforma)

**Vantagens**: Funciona em qualquer sistema operacional, confiável, rastreável, até 100 e-mails/dia grátis.

**Configuração rápida**:
1. Crie conta em https://sendgrid.com
2. Gere uma API Key em Settings > API Keys
3. Configure o `.env`:
   ```env
   USE_SENDGRID=true
   SENDGRID_API_KEY=SG.sua_chave_aqui
   SENDGRID_FROM_EMAIL=seu-email@dominio.com
   SENDGRID_FROM_NAME=Atlas Inovações
   ```

📖 **[Guia completo de configuração do SendGrid](SENDGRID_SETUP.md)**

### Método 2: Outlook (Apenas Windows)

**Requisitos**: Windows + Outlook instalado e configurado

**Configuração**:
```env
USE_SENDGRID=false
SENDER_EMAIL=seu-email@empresa.com
SENDER_NAME=Seu Nome
```

## Como rodar (exemplos)

### Interface Web (Recomendado)
```bash
# Backend
cd backend && uvicorn app.main:app --reload

# Frontend (em outro terminal)
cd frontend && npm run dev
```
Acesse: http://localhost:5173

### CLI - Dry-run para 1 unidade:
```bash
python main.py --regiao SP1 --unidade "Shopping X" --mes 2025-11 --xlsx-dir "D:\Planilhas" --dry-run
```
→ Gera `output_html/Shopping_X_2025-11.html` sem enviar e-mail.

- **Dry-run** para todas as unidades de uma região (mês padrão: anterior ao atual ou conforme `.env`):
  ```bash
  python main.py --regiao RJ --dry-run --xlsx-dir C:\pasta\das\planilhas
  ```

- **Envio real** (uma unidade):
  ```bash
  python main.py --regiao SP1 --unidade "Shopping X" --mes 2025-08 --xlsx-dir "D:\Planilhas"
  ```
  **Nota**: Usa SendGrid se `USE_SENDGRID=true` no `.env`, caso contrário usa Outlook.

## Como a planilha é encontrada
O script procura no diretório `--xlsx-dir` arquivos com padrões como:
- `*Medição Mensal*_{REGIAO}_*.xlsx` (ex.: `_RJ_` / `_SP1_` / `_SP2_` / `_SP3_` / `_NNE_`)
- ou qualquer `.xlsx` que possua a aba `Faturamento {REGIAO}`.

A aba lida é sempre `Faturamento {REGIAO}` (ex.: `Faturamento RJ`).

## Campos usados no e-mail
- Unidade
- Categoria
- Fornecedor
- HC Planilha
- Dias Faltas
- Horas Atrasos
- Valor Planilha
- Desconto Falta Validado Atlas
- Desconto Atrasos Validado Atlas
- Desconto SLA Mês Desconto Equipamentos
- **Valor Mensal Final** (em negrito no HTML)
- Mês de emissão da NF


## Assunto e remetente
- Assunto: `Medição mensal — {Unidade} — {Mês/AAAA por extenso}`.
- Se `USE_TEST_SUBJECT=true` no `.env`, o assunto recebe prefixo `(Teste)`.
- Remetente:
  - **SendGrid**: Usa `SENDGRID_FROM_EMAIL` e `SENDGRID_FROM_NAME`
  - **Outlook**: Usa `SENDER_EMAIL` do `.env` e tenta usar a conta do Outlook com esse endereço

## Logs (SQLite)
- Banco: `faturamento_logs.db` (criado automaticamente).
- Tabela: `send_logs` com data/hora, região, unidade, mês, status (saved/sent/failed), etc.

## Anexo opcional
- Se `ATTACH_FILTERED_XLSX=true` no `.env`, é anexado um XLSX com as linhas filtradas da unidade+mês.

## Observações
- Valores monetários são formatados como `R$ 1.234,56`.
- Endereços de e-mail são lidos da coluna `E-mail` (ou sinônimos) e separados por `;`. Duplicados são removidos.
- Se não houver destinatários na planilha, usa-se `FALLBACK_EMAIL` do `.env`.
- `--preview` abre o HTML no navegador após gerar.

-

## Dicas de editor
- Configure o VS Code com `"files.encoding": "utf8"` para evitar BOM.

