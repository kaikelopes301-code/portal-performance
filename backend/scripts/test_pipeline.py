"""
Script de teste para validar o pipeline de execução.
Uso: python test_pipeline.py
"""
import sys
import os

# Adiciona o backend ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.pipeline_service import get_pipeline_service

def test_pipeline():
    print("=" * 60)
    print("TESTE DO PIPELINE DE EXECUÇÃO")
    print("=" * 60)
    
    service = get_pipeline_service()
    
    # 1. Lista regiões
    print("\n1. Regiões disponíveis:")
    regions = service.list_available_regions()
    print(f"   {regions}")
    
    # 2. Lista unidades de uma região
    print("\n2. Unidades da região RJ:")
    units = service.list_available_units("RJ")
    for u in units[:5]:
        print(f"   - {u}")
    if len(units) > 5:
        print(f"   ... e mais {len(units) - 5} unidades")
    
    # 3. Lista meses disponíveis
    print("\n3. Meses disponíveis na região RJ:")
    months = service.list_available_months("RJ")
    for m in months[:3]:
        print(f"   - {m}")
    
    # 4. Testa execução dry-run
    if units and months:
        print(f"\n4. Executando dry-run para '{units[0]}' no mês '{months[0]}':")
        result = service.execute(
            region="RJ",
            unit=units[0],
            month=months[0],
            dry_run=True,
            send_email=False
        )
        
        print(f"   Sucesso: {result.success}")
        print(f"   Linhas: {result.rows_count}")
        print(f"   Emails encontrados: {len(result.emails_found)}")
        print(f"   HTML: {result.html_path}")
        if result.error:
            print(f"   Erro: {result.error}")
    
    print("\n" + "=" * 60)
    print("TESTE CONCLUÍDO COM SUCESSO!")
    print("=" * 60)

if __name__ == "__main__":
    test_pipeline()
