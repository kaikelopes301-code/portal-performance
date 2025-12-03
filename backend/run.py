#!/usr/bin/env python
"""
Script para iniciar o servidor backend FastAPI.
Execute de qualquer lugar: python backend/run.py
"""
import os
import sys

# Adiciona o diretório backend ao path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)
os.chdir(backend_dir)

import uvicorn

if __name__ == "__main__":
    print("=" * 60)
    print("  PORTAL PERFORMANCE - Backend API")
    print("  Atlas Inovações")
    print("=" * 60)
    print(f"\n  Diretório: {backend_dir}")
    print("  URL: http://localhost:8000")
    print("  Docs: http://localhost:8000/docs")
    print("\n  Pressione Ctrl+C para parar\n")
    print("=" * 60)
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=[backend_dir]
    )
