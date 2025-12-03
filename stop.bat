@echo off
chcp 65001 >nul
title Portal Performance - Encerrando...

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║              ENCERRANDO PORTAL PERFORMANCE                   ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

echo [INFO] Encerrando processos...

:: Encerrar Node (Frontend)
taskkill /f /im node.exe >nul 2>&1
echo       ✓ Frontend encerrado

:: Encerrar Python/Uvicorn (Backend)
taskkill /f /im python.exe >nul 2>&1
echo       ✓ Backend encerrado

echo.
echo [OK] Todos os serviços foram encerrados.
echo.
pause
