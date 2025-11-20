#  Configuração SendGrid - Guia Completo

##  Status Atual

O projeto **JÁ ESTÁ 100% CONFIGURADO**! 

-  Código implementado (`emailer.py` + `main.py`)
- Dependência instalada (`pip install sendgrid` ✓)
-  Variáveis criadas no `.env`

### Passo 1: Configurar `.env`

Edite `c:\backpperformance\.env` (linhas 6 e 10):

```env
# Ativar SendGrid
USE_SENDGRID=true

# Cole sua chave aqui
SENDGRID_API_KEY=SG.sua_chave_copiada_aqui
```

### Passo 2: Testar

```powershell
# Teste sem enviar
python main.py --regiao RJ --unidade "Passeio Shopping" --mes 2025-10 --dry-run --xlsx-dir "C:\planilhas"

# Envio real
python main.py --regiao RJ --unidade "Passeio Shopping" --mes 2025-10 --xlsx-dir "C:\planilhas"
```

**Sucesso!** Você verá:
```
✓ E-mail enviado via SendGrid com sucesso (Status: 202)
```

---

##  Configurações no `.env`

```env
# Obrigatórias
USE_SENDGRID=true
SENDGRID_API_KEY=SG.sua_chave_aqui
SENDGRID_FROM_EMAIL=consultoria@atlasinovacoes.com.br
SENDGRID_FROM_NAME=Atlas Inovações | Operações

# Opcional (para UE)
SENDGRID_USE_EU_REGION=false
```

---

##  Solução de Problemas

### Erro: `401 Unauthorized`
**Causa**: API Key incorreta  
**Solução**: Verifique se copiou completa (começa com `SG.`)

### Erro: `403 Forbidden`
**Causa**: Sem permissão "Mail Send"  
**Solução**: Edite a chave → Marque "Mail Send" Full Access

### Erro: `SENDGRID_API_KEY não configurada`
**Causa**: Chave vazia no `.env`  
**Solução**: Adicione `SENDGRID_API_KEY=SG.xxx` no `.env`

### E-mails não chegam
1. Verifique pasta de spam
2. Confira logs: https://app.sendgrid.com → Activity

### Amem, deu tudo certo
    (status 202)
---

##  Voltar para Outlook

No `.env`, mude:
```env
USE_SENDGRID=false
```

##  Checklist Final
- [ ] `.env` → `USE_SENDGRID=true`
- [ ] `.env` → `SENDGRID_API_KEY=SG.xxx`
- [ ] Teste com `--dry-run` OK
- [ ] Envio real funcionou
- [ ] E-mail recebido ✉️

---

 **Links úteis**:
- Painel: https://app.sendgrid.com
- Docs: https://docs.sendgrid.com
- Status: https://status.sendgrid.com
