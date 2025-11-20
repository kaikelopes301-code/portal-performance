2. Instalação das Dependências
Abra o terminal na pasta do projeto e execute:

## pip install -r requirements.txt  , pip install -r portal_streamlit/requirements.txt

Dica: Recomendo usar um ambiente virtual (python -m venv venv).

3. Configuração do Envio de E-mails

No arquivo .env (raiz do projeto), configure

USE_SENDGRID=true
SENDGRID_API_KEY=SG.sua_chave_aqui
SENDGRID_FROM_EMAIL=seu-email@dominio.com
SENDGRID_FROM_NAME=Seu Nome


## pip install sendgrid

## python -c "from sendgrid import SendGridAPIClient; print('✓ SendGrid instalado!')"

Opção 2: Outlook (Apenas Windows)
Necessário Outlook instalado e configurado

No .env:

USE_SENDGRID=false
SENDER_EMAIL=seu-email@empresa.com
SENDER_NAME=Seu Nome

4. Como Executar
Interface Web (Streamlit):

## python -m streamlit run portal_streamlit/app.py

Envio real:

## python main.py --regiao SP1 --unidade "Shopping X" --mes 2025-10 --xlsx-dir "D:\Planilhas"


5. Checklist Rápido
 Python 3.10+ instalado
 Dependências instaladas (pip install ...)
 .env configurado
 API Key do SendGrid (se aplicável)
 Outlook instalado (se aplicável)
 Planilhas no diretório correto

 7. Documentação e Suporte
Manual SendGrid
README do projeto
[SENDGRID_CONFIG.md] para detalhes técnicos