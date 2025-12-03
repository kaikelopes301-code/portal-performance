# Sistema de Faturamento - Backend API

FastAPI backend para processamento de planilhas de faturamento.

## Setup

```bash
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txtd
```

## Executar

```bash
uvicorn app.main:app --reload
```

## Variáveis de Ambiente

Copie `.env.example` para `.env` e preencha:
- `DATABASE_URL`
- `SENDGRID_API_KEY`
- `CLOUDINARY_NAME`, `CLOUDINARY_KEY`, `CLOUDINARY_SECRET`
- `SECRET_KEY`
