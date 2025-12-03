# Sistema de Faturamento v2.0

Aplicação web completa para processamento de planilhas de faturamento e geração de relatórios.

## 🏗️ Arquitetura

```
backpperformance/
├── backend/          # FastAPI backend
│   ├── app/
│   │   ├── main.py
│   │   ├── database.py
│   │   ├── models/
│   │   ├── routers/
│   │   └── services/
│   └── requirements.txt
│
└── frontend/         # React frontend
    ├── src/
    ├── package.json
    └── vite.config.ts
```

## 🚀 Quick Start

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
cp .env.example .env   # Configure variáveis
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## 📦 Stack Tecnológica

### Backend
- FastAPI 0.104+
- PostgreSQL (SQLAlchemy)
- SendGrid (email)
- Cloudinary (storage)
- Celery + Redis (tasks)

### Frontend (Otimizado)
- React 18 + Vite
- TypeScript
- TailwindCSS
- SWR (5KB)
- Zustand (1.2KB)
- Fetch API nativo

**Bundle: < 150KB gzipped** ⚡

## 🌐 Deploy Gratuito

- **Frontend:** Vercel
- **Backend:** Render.com
- **DB:** Render PostgreSQL
- **Storage:** Cloudinary (10GB)
- **Email:** SendGrid (100/dia)

**Custo: R$ 0,00/mês** ✅

## 📝 Status

- [x] Fase 1: Estrutura inicial criada
- [ ] Fase 2: Backend API Core
- [ ] Fase 3: Frontend UI
- [ ] Fase 4: Integração Email/Storage
- [ ] Fase 5: Deploy

## 📖 Documentação

Ver `/backend/README.md` e `/frontend/README.md` para detalhes específicos.

---

**Versão:** 2.0.0  
**Criado:** 29/11/2025
