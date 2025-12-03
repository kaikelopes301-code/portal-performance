"""
Script de testes para validar migração do código backend
"""

import sys
from pathlib import Path

print("="*60)
print("TESTE 1: Imports dos Módulos")
print("="*60)

try:
    print("\n1. Importando app.services.utils...")
    from app.services import utils
    print("   ✓ utils importado com sucesso")
    
    print("\n2. Importando app.services.processor...")
    from app.services import processor
    print("   ✓ processor importado com sucesso")
    
    print("\n3. Importando app.services.emailer...")
    from app.services import emailer
    print("   ✓ emailer importado com sucesso")
    
    print("\n4. Importando app.services.extractor...")
    from app.services import extractor
    print("   ✓ extractor importado com sucesso")
    
except Exception as e:
    print(f"   ✗ ERRO: {e}")
    sys.exit(1)

print("\n" + "="*60)
print("TESTE 2: Funções Básicas")
print("="*60)

try:
    # Teste formatação BRL
    print("\n1. Testando fmt_brl()...")
    result = utils.fmt_brl(1234.56)
    expected = "R$ 1.234,56"
    assert result == expected, f"Esperado '{expected}', obteve '{result}'"
    print(f"   ✓ fmt_brl(1234.56) = {result}")
    
    # Teste parse_year_month
    print("\n2. Testando parse_year_month()...")
    result = utils.parse_year_month("2025-11")
    expected = "2025-11"
    assert result == expected, f"Esperado '{expected}', obteve '{result}'"
    print(f"   ✓ parse_year_month('2025-11') = {result}")
    
    # Teste normalize_unit
    print("\n3. Testando normalize_unit()...")
    result = utils.normalize_unit("Shopping São Paulo")
    assert result == "shopping sao paulo", f"Esperado 'shopping sao paulo', obteve '{result}'"
    print(f"   ✓ normalize_unit('Shopping São Paulo') = '{result}'")
    
    # Teste split_emails
    print("\n4. Testando split_emails()...")
    result = utils.split_emails("user@example.com; outro@test.com", warn=False)
    assert len(result) == 2, f"Esperado 2 emails, obteve {len(result)}"
    print(f"   ✓ split_emails() = {result}")
    
except AssertionError as e:
    print(f"   ✗ FALHA: {e}")
    sys.exit(1)
except Exception as e:
    print(f"   ✗ ERRO: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "="*60)
print("TESTE 3: Constantes e Configurações")
print("="*60)

try:
    print("\n1. Verificando constantes do processor...")
    assert hasattr(processor, 'COLUMN_CANDIDATES'), "COLUMN_CANDIDATES não encontrado"
    assert hasattr(processor, 'DISPLAY_HEADER_SYNONYMS'), "DISPLAY_HEADER_SYNONYMS não encontrado"
    print(f"   ✓ COLUMN_CANDIDATES tem {len(processor.COLUMN_CANDIDATES)} mapeamentos")
    print(f"   ✓ DISPLAY_HEADER_SYNONYMS tem {len(processor.DISPLAY_HEADER_SYNONYMS)} sinônimos")
    
    print("\n2. Verificando classe Emailer...")
    assert hasattr(emailer, 'Emailer'), "Classe Emailer não encontrada"
    print("   ✓ Classe Emailer disponível")
    
    print("\n3. Verificando classe Extractor...")
    assert hasattr(extractor, 'Extractor'), "Classe Extractor não encontrada"
    print("   ✓ Classe Extractor disponível")
    
except AssertionError as e:
    print(f"   ✗ FALHA: {e}")
    sys.exit(1)
except Exception as e:
    print(f"   ✗ ERRO: {e}")
    sys.exit(1)

print("\n" + "="*60)
print("TESTE 4: API FastAPI")
print("="*60)

try:
    print("\n1. Importando FastAPI app...")
    from app.main import app
    print("   ✓ FastAPI app importado com sucesso")
    
    print("\n2. Verificando rotas...")
    routes = [route.path for route in app.routes]
    assert "/" in routes, "Rota / não encontrada"
    assert "/health" in routes, "Rota /health não encontrada"
    print(f"   ✓ Rotas disponíveis: {routes}")
    
except Exception as e:
    print(f"   ✗ ERRO: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "="*60)
print("✅ TODOS OS TESTES PASSARAM!")
print("="*60)
print("\nMigração validada com sucesso. Sistema pronto para próxima fase.")
