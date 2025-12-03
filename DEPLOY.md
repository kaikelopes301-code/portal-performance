# 🚀 Guia de Deploy - Portal Performance

Este guia explica como fazer o deploy gratuito do Portal Performance usando **Render** (backend) e **Vercel** (frontend).

---

## 📋 Pré-requisitos

1. Conta no GitHub com o repositório do projeto
2. Conta gratuita no [Render](https://render.com)
3. Conta gratuita no [Vercel](https://vercel.com)
4. Chave de API do [SendGrid](https://sendgrid.com) (100 emails/dia grátis)

---

## 🔧 Parte 1: Deploy do Backend (Render)

### Passo 1: Preparar o Repositório

Certifique-se de que os seguintes arquivos existem:
- `backend/render.yaml` ✅ (já criado)
- `backend/requirements.txt` ✅ (já otimizado)
- `.env.example` ✅ (já criado)

### Passo 2: Criar Conta no Render

1. Acesse [render.com](https://render.com)
2. Clique em **Get Started for Free**
3. Conecte sua conta GitHub

### Passo 3: Criar Novo Web Service

1. No Dashboard, clique em **New +** → **Web Service**
2. Conecte seu repositório GitHub (`portal-allos`)
3. Configure:

| Campo | Valor |
|-------|-------|
| **Name** | `portal-performance-api` |
| **Region** | Oregon (US West) |
| **Branch** | `main` |
| **Root Directory** | `backend` |
| **Runtime** | Python 3 |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| **Instance Type** | Free |

### Passo 4: Configurar Variáveis de Ambiente

Na aba **Environment**, adicione:

```
DATABASE_URL=sqlite:///./faturamento.db
SENDGRID_API_KEY=SG.sua-chave-aqui
SENDGRID_FROM_EMAIL=consultoria@atlasinovacoes.com.br
SENDGRID_FROM_NAME=Atlas Inovações | Operações
SECRET_KEY=gerar-chave-aleatoria-32-chars
PORTAL_API_KEY=gerar-api-key-segura
ALLOWED_ORIGINS=https://seu-frontend.vercel.app
HTML_RETENTION_DAYS=30
JOB_RETENTION_DAYS=90
ENVIRONMENT=production
```

> 💡 Para gerar chaves seguras, use: `python -c "import secrets; print(secrets.token_hex(32))"`

### Passo 5: Deploy

1. Clique em **Create Web Service**
2. Aguarde o build (3-5 minutos)
3. Quando terminar, você terá uma URL tipo: `https://portal-performance-api.onrender.com`

### Passo 6: Testar

Acesse:
- `https://portal-performance-api.onrender.com/health` → Deve retornar `{"status": "ok"}`
- `https://portal-performance-api.onrender.com/docs` → Documentação Swagger

---

## 🎨 Parte 2: Deploy do Frontend (Vercel)

### Passo 1: Preparar o Repositório

Certifique-se de que existe:
- `frontend/vercel.json` ✅ (já criado)
- `frontend/package.json` ✅
- `frontend/vite.config.ts` ✅

### Passo 2: Criar Conta no Vercel

1. Acesse [vercel.com](https://vercel.com)
2. Clique em **Sign Up** → **Continue with GitHub**
3. Autorize acesso aos repositórios

### Passo 3: Importar Projeto

1. No Dashboard, clique em **Add New...** → **Project**
2. Selecione o repositório `portal-allos`
3. Configure:

| Campo | Valor |
|-------|-------|
| **Project Name** | `portal-performance` |
| **Framework Preset** | Vite |
| **Root Directory** | `frontend` |
| **Build Command** | `npm run build` |
| **Output Directory** | `dist` |

### Passo 4: Configurar Variáveis de Ambiente

Na seção **Environment Variables**, adicione:

```
VITE_API_URL=https://portal-performance-api.onrender.com
VITE_ENV=production
```

### Passo 5: Deploy

1. Clique em **Deploy**
2. Aguarde o build (1-2 minutos)
3. Quando terminar, você terá uma URL tipo: `https://portal-performance.vercel.app`

### Passo 6: Atualizar CORS no Backend

Volte ao Render e atualize a variável:
```
ALLOWED_ORIGINS=https://portal-performance.vercel.app
```

---

## 🔄 Deploy Automático

Após a configuração inicial, todo push para a branch `main` fará deploy automático:
- **Render**: Rebuild do backend
- **Vercel**: Rebuild do frontend

---

## ⚠️ Limitações do Tier Gratuito

### Render (Free)
- 750 horas/mês (suficiente para 1 serviço 24/7)
- **Sleep após 15 minutos de inatividade**
- Primeiro request após sleep demora ~30-60s

### Vercel (Hobby)
- Builds ilimitados
- 100GB bandwidth/mês
- Sem limitação de sleep

### Solução para Cold Start do Render

Use um serviço gratuito de uptime monitoring:

1. Acesse [UptimeRobot](https://uptimerobot.com) (gratuito)
2. Crie uma conta
3. Adicione um monitor:
   - **Monitor Type**: HTTP(s)
   - **URL**: `https://portal-performance-api.onrender.com/health`
   - **Monitoring Interval**: 5 minutos

Isso manterá o backend "acordado" constantemente.

---

## 📁 Estrutura de Arquivos para Deploy

```
portal-allos/
├── .env.example          # Template de variáveis
├── .gitignore            # Arquivos ignorados
├── backend/
│   ├── render.yaml       # Config do Render
│   ├── requirements.txt  # Dependências Python
│   └── app/
│       └── main.py       # Entrada da API
└── frontend/
    ├── vercel.json       # Config do Vercel
    ├── package.json      # Dependências Node
    └── vite.config.ts    # Config do Vite
```

---

## 🛠️ Troubleshooting

### Backend não inicia no Render

1. Verifique os logs no Dashboard do Render
2. Confirme que `Root Directory` está como `backend`
3. Verifique se todas as variáveis de ambiente estão configuradas

### Frontend não conecta com Backend

1. Verifique `VITE_API_URL` no Vercel
2. Confirme que `ALLOWED_ORIGINS` no Render inclui a URL do Vercel
3. Verifique se a URL não tem `/` no final

### Erro 422 (Validation Error)

1. Acesse `/docs` no backend para ver a API
2. Verifique o formato dos dados enviados

### Emails não são enviados

1. Verifique `SENDGRID_API_KEY` no Render
2. Confirme que o email de origem está verificado no SendGrid
3. Verifique se não excedeu o limite diário (100/dia)

---

## 📊 Monitoramento

### Render
- Dashboard mostra logs em tempo real
- Métricas de uso de memória/CPU

### Vercel
- Analytics de performance
- Logs de build

### Recomendado
- [UptimeRobot](https://uptimerobot.com) - Monitoramento de uptime gratuito
- [Sentry](https://sentry.io) - Tracking de erros (tier gratuito disponível)

---

## 💰 Custo Total

| Serviço | Tier | Custo |
|---------|------|-------|
| Render | Free | R$ 0 |
| Vercel | Hobby | R$ 0 |
| SendGrid | Free | R$ 0 |
| UptimeRobot | Free | R$ 0 |
| **Total** | - | **R$ 0/mês** |

---

## 🔗 Links Úteis

- [Render Docs](https://render.com/docs)
- [Vercel Docs](https://vercel.com/docs)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
- [Vite Deployment](https://vitejs.dev/guide/static-deploy.html)
