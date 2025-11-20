"""
Portal Performance - Launcher
Executa o Streamlit e abre o navegador automaticamente.
"""

import subprocess
import sys
import os
import time
import webbrowser
import socket
from pathlib import Path

# Configurações
PORTA = 8501
URL = f"http://localhost:{PORTA}"

def verificar_porta_disponivel(porta):
    """Verifica se a porta está livre."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', porta)) != 0

def encontrar_porta_livre(porta_inicial=8501):
    """Encontra uma porta livre a partir da porta inicial."""
    porta = porta_inicial
    while porta < porta_inicial + 100:
        if verificar_porta_disponivel(porta):
            return porta
        porta += 1
    return porta_inicial

def main():
    # Encontra o diretório do executável/script
    if getattr(sys, 'frozen', False):
        # Executando como .exe (PyInstaller)
        base_dir = Path(sys.executable).parent
    else:
        # Executando como script Python
        base_dir = Path(__file__).parent
    
    app_path = base_dir / "portal_streamlit" / "app.py"
    
    # Verifica se o arquivo existe
    if not app_path.exists():
        print(f"❌ Erro: Arquivo não encontrado: {app_path}")
        print("Certifique-se de que a pasta 'portal_streamlit' está no mesmo diretório.")
        input("\nPressione ENTER para sair...")
        sys.exit(1)
    
    # Encontra porta livre
    porta = encontrar_porta_livre(PORTA)
    url = f"http://localhost:{porta}"
    
    print("=" * 50)
    print("   🚀 PORTAL PERFORMANCE - ATLAS INOVAÇÕES")
    print("=" * 50)
    print(f"\n📂 Diretório: {base_dir}")
    print(f"🌐 URL: {url}")
    print("\n⏳ Iniciando servidor...")
    print("-" * 50)
    
    # Comando Streamlit
    cmd = [
        sys.executable, "-m", "streamlit", "run",
        str(app_path),
        "--server.port", str(porta),
        "--server.headless", "true",
        "--browser.gatherUsageStats", "false",
        "--theme.base", "dark",
    ]
    
    try:
        # Inicia o Streamlit em background
        processo = subprocess.Popen(
            cmd,
            cwd=str(base_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        )
        
        # Aguarda o servidor iniciar
        print("\n⏳ Aguardando servidor iniciar...")
        tentativas = 0
        servidor_pronto = False
        
        while tentativas < 30:  # 30 segundos de timeout
            time.sleep(1)
            tentativas += 1
            
            # Verifica se a porta está em uso (servidor rodando)
            if not verificar_porta_disponivel(porta):
                servidor_pronto = True
                break
            
            # Verifica se o processo ainda está rodando
            if processo.poll() is not None:
                print("\n❌ Erro: O servidor encerrou inesperadamente.")
                output = processo.stdout.read()
                if output:
                    print(f"Log: {output}")
                input("\nPressione ENTER para sair...")
                sys.exit(1)
        
        if not servidor_pronto:
            print("\n⚠️ Timeout aguardando servidor. Tentando abrir mesmo assim...")
        
        # Abre o navegador
        print(f"\n✅ Servidor iniciado!")
        print(f"🌐 Abrindo navegador em: {url}")
        print("-" * 50)
        webbrowser.open(url)
        
        print("\n📌 O portal está rodando!")
        print("   Para encerrar, feche esta janela ou pressione Ctrl+C")
        print("-" * 50)
        
        # Mantém o processo rodando e mostra logs
        while True:
            linha = processo.stdout.readline()
            if linha:
                # Filtra logs muito verbosos
                if "Watching" not in linha and "watcher" not in linha.lower():
                    print(f"   {linha.strip()}")
            
            # Verifica se o processo encerrou
            if processo.poll() is not None:
                print("\n⚠️ Servidor encerrado.")
                break
            
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\n\n🛑 Encerrando servidor...")
        processo.terminate()
        processo.wait(timeout=5)
        print("✅ Servidor encerrado com sucesso!")
        
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")
        input("\nPressione ENTER para sair...")
        sys.exit(1)

if __name__ == "__main__":
    main()