@echo off
setlocal enabledelayedexpansion

echo ========================================================
echo   INICIANDO THE INTELLIGENCE SYSTEM (ENTREGA FINAL)
echo ========================================================

REM 1. Verificar si existe .env
if not exist .env (
    echo [AVISO] No se encontro el archivo .env. Copiando desde .env.example...
    copy .env.example .env
    echo Por favor configura tus API keys en .env antes de continuar.
)

REM 2. Intentar levantar via Docker Compose si Docker esta disponible
docker --version >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo [DOCKER] Iniciando servicios con Docker Compose...
    docker compose up --build
    exit /b %ERRORLEVEL%
)

REM 3. Fallback en ejecucion local con Python y Uvicorn
echo [FALLBACK LOCAL] Docker no detectado en PATH. Iniciando servicios en entorno Python local...
if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
)
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
