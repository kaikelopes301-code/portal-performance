@echo off
chcp 65001 >nul
title Portal Performance - Iniciando...

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║           PORTAL PERFORMANCE - SISTEMA DE FATURAMENTO        ║
echo ║                      Atlas Inovações                         ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

:: Cores
set "GREEN=[92m"
set "RED=[91m"
set "YELLOW=[93m"
set "BLUE=[94m"
set "NC=[0m"

:: Diretório base
set "BASE_DIR=%~dp0"
cd /d "%BASE_DIR%"

echo %BLUE%[INFO]%NC% Verificando dependências...
echo.

:: ============================================
:: VERIFICAR PYTHON
:: ============================================
echo %YELLOW%[1/6]%NC% Verificando Python...
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo %RED%[ERRO]%NC% Python não encontrado! Instale o Python 3.10+
    pause
    exit /b 1
)
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo       ✓ Python %PYTHON_VERSION% encontrado

:: ============================================
:: VERIFICAR NODE.JS
:: ============================================
echo %YELLOW%[2/6]%NC% Verificando Node.js...
node --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo %RED%[ERRO]%NC% Node.js não encontrado! Instale o Node.js 18+
    pause
    exit /b 1
)
for /f %%i in ('node --version 2^>^&1') do set NODE_VERSION=%%i
echo       ✓ Node.js %NODE_VERSION% encontrado

:: ============================================
:: VERIFICAR/CRIAR VENV DO BACKEND
:: ============================================
echo %YELLOW%[3/6]%NC% Verificando ambiente virtual do Backend...
if not exist "backend\venv\Scripts\activate.bat" (
    echo       Criando ambiente virtual...
    cd backend
    python -m venv venv
    cd ..
    echo       ✓ Ambiente virtual criado
) else (
    echo       ✓ Ambiente virtual existe
)

:: ============================================
:: INSTALAR DEPENDÊNCIAS DO BACKEND
:: ============================================
echo %YELLOW%[4/6]%NC% Verificando dependências do Backend...
cd backend
call venv\Scripts\activate.bat

:: Verificar se uvicorn está instalado (indica que deps foram instaladas)
python -c "import uvicorn" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo       Instalando dependências Python...
    pip install -r requirements.txt --quiet
    if %ERRORLEVEL% NEQ 0 (
        echo %RED%[ERRO]%NC% Falha ao instalar dependências do Backend
        pause
        exit /b 1
    )
    echo       ✓ Dependências Python instaladas
) else (
    echo       ✓ Dependências Python OK
)
cd ..

:: ============================================
:: INSTALAR DEPENDÊNCIAS DO FRONTEND
:: ============================================
echo %YELLOW%[5/6]%NC% Verificando dependências do Frontend...
cd frontend
if not exist "node_modules" (
    echo       Instalando dependências Node.js...
    call npm install --silent
    if %ERRORLEVEL% NEQ 0 (
        echo %RED%[ERRO]%NC% Falha ao instalar dependências do Frontend
        pause
        exit /b 1
    )
    echo       ✓ Dependências Node.js instaladas
) else (
    echo       ✓ Dependências Node.js OK
)
cd ..

:: ============================================
:: VERIFICAR ARQUIVO .ENV
:: ============================================
echo %YELLOW%[6/6]%NC% Verificando configuração...
if not exist ".env" (
    echo %YELLOW%[AVISO]%NC% Arquivo .env não encontrado na raiz
    echo       Crie o arquivo .env com as configurações necessárias
) else (
    echo       ✓ Arquivo .env encontrado
)

echo.
echo %GREEN%═══════════════════════════════════════════════════════════════%NC%
echo %GREEN%  Todas as dependências verificadas! Iniciando serviços...     %NC%
echo %GREEN%═══════════════════════════════════════════════════════════════%NC%
echo.

:: ============================================
:: INICIAR BACKEND
:: ============================================
echo %BLUE%[INFO]%NC% Iniciando Backend (FastAPI)...
cd backend
start "Backend - FastAPI" cmd /k "call venv\Scripts\activate.bat && echo. && echo ══════════════════════════════════════ && echo   BACKEND - http://localhost:8000 && echo ══════════════════════════════════════ && echo. && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
cd ..

:: Aguardar backend iniciar
timeout /t 3 /nobreak >nul

:: ============================================
:: INICIAR FRONTEND
:: ============================================
echo %BLUE%[INFO]%NC% Iniciando Frontend (Vite)...
cd frontend
start "Frontend - Vite" cmd /k "echo. && echo ══════════════════════════════════════ && echo   FRONTEND - http://localhost:5173 && echo ══════════════════════════════════════ && echo. && npm run dev"
cd ..

:: ============================================
:: MENSAGEM FINAL
:: ============================================
echo.
echo %GREEN%╔══════════════════════════════════════════════════════════════╗%NC%
echo %GREEN%║                    SISTEMA INICIADO!                         ║%NC%
echo %GREEN%╠══════════════════════════════════════════════════════════════╣%NC%
echo %GREEN%║                                                              ║%NC%
echo %GREEN%║   Frontend:  http://localhost:5173                           ║%NC%
echo %GREEN%║   Backend:   http://localhost:8000                           ║%NC%
echo %GREEN%║   API Docs:  http://localhost:8000/docs                      ║%NC%
echo %GREEN%║                                                              ║%NC%
echo %GREEN%║   Pressione qualquer tecla para abrir o navegador...         ║%NC%
echo %GREEN%║                                                              ║%NC%
echo %GREEN%╚══════════════════════════════════════════════════════════════╝%NC%
echo.

pause >nul

:: Abrir navegador
start "" "http://localhost:5173"

echo.
echo %YELLOW%[INFO]%NC% Para encerrar, feche as janelas do terminal ou pressione Ctrl+C
echo.
